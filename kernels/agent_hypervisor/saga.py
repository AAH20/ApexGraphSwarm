"""Saga transactions for long-running agent operations.

A saga is a sequence of steps, each with a compensating action.
If any step fails, all previously completed steps are compensated
(rolled back) in reverse order.

This implements the Saga pattern for distributed transactions without
requiring a central coordinator.
"""
from __future__ import annotations

import enum
import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


class SagaError(RuntimeError):
    """Saga execution or compensation failure."""


class SagaState(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    FAILED = "failed"


@dataclass
class SagaStep:
    """A single step in a saga with its compensation."""
    name: str
    action: Callable[[], Any]
    compensation: Callable[[], Any] | None = None
    action_result: Any = None
    compensated: bool = False
    failed: bool = False
    error: str | None = None
    started_at: float | None = None
    completed_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "compensated": self.compensated,
            "failed": self.failed,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


@dataclass
class SagaLog:
    """Persistent log of saga execution for audit and recovery."""
    saga_id: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    state: SagaState = SagaState.PENDING
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def record_step_start(self, step_name: str) -> None:
        self.steps.append({
            "step": step_name,
            "event": "start",
            "timestamp": time.time(),
        })

    def record_step_complete(self, step_name: str, result: Any = None) -> None:
        self.steps.append({
            "step": step_name,
            "event": "complete",
            "timestamp": time.time(),
            "result": _safe_serialize(result),
        })

    def record_step_compensation(self, step_name: str) -> None:
        self.steps.append({
            "step": step_name,
            "event": "compensate",
            "timestamp": time.time(),
        })

    def record_step_compensated(self, step_name: str) -> None:
        self.steps.append({
            "step": step_name,
            "event": "compensated",
            "timestamp": time.time(),
        })

    def record_failure(self, step_name: str, error: str) -> None:
        self.steps.append({
            "step": step_name,
            "event": "failure",
            "timestamp": time.time(),
            "error": error,
        })

    def to_dict(self) -> dict[str, Any]:
        return {
            "sagaId": self.saga_id,
            "state": self.state.value,
            "startedAt": self.started_at,
            "completedAt": self.completed_at,
            "steps": self.steps,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def _safe_serialize(value: Any) -> Any:
    """Safely serialize a value for the saga log."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [_safe_serialize(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _safe_serialize(v) for k, v in value.items()}
    return str(value)


class Saga:
    """A saga transaction coordinator.

    Usage:
        saga = Saga("deploy-service")
        saga.add_step("create-vm", create_vm_fn, delete_vm_fn)
        saga.add_step("configure", configure_fn, unconfigure_fn)
        result = saga.execute()
    """

    def __init__(self, name: str, *, saga_id: str | None = None,
                 metadata: dict[str, Any] | None = None):
        self.saga_id = saga_id or str(uuid.uuid4())
        self.name = name
        self._steps: list[SagaStep] = []
        self._state = SagaState.PENDING
        self._log = SagaLog(saga_id=self.saga_id, metadata=metadata or {})
        self._lock = threading.RLock()
        self._results: list[Any] = []

    @property
    def state(self) -> SagaState:
        return self._state

    @property
    def log(self) -> SagaLog:
        return self._log

    def add_step(self, name: str, action: Callable[[], Any],
                 compensation: Callable[[], Any] | None = None) -> Saga:
        """Add a step to the saga. Returns self for chaining."""
        with self._lock:
            if self._state != SagaState.PENDING:
                raise SagaError("Cannot add steps to a saga that has started")
            self._steps.append(SagaStep(
                name=name,
                action=action,
                compensation=compensation,
            ))
            return self

    def execute(self) -> list[Any]:
        """Execute all saga steps.

        If any step fails, compensates all completed steps in reverse order.
        Returns the list of action results if successful.
        Raises SagaError if execution or compensation fails.
        """
        with self._lock:
            if self._state != SagaState.PENDING:
                raise SagaError(f"Saga already in state: {self._state.value}")

            self._state = SagaState.RUNNING
            self._log.state = SagaState.RUNNING
            completed_steps: list[SagaStep] = []

            try:
                for step in self._steps:
                    step.started_at = time.time()
                    self._log.record_step_start(step.name)
                    try:
                        step.action_result = step.action()
                        step.completed_at = time.time()
                        self._log.record_step_complete(step.name, step.action_result)
                        completed_steps.append(step)
                        self._results.append(step.action_result)
                    except Exception as e:
                        step.failed = True
                        step.error = str(e)
                        step.completed_at = time.time()
                        self._log.record_failure(step.name, str(e))
                        raise SagaError(
                            f"Saga step '{step.name}' failed: {e}"
                        ) from e

                self._state = SagaState.COMPLETED
                self._log.state = SagaState.COMPLETED
                self._log.completed_at = time.time()
                return list(self._results)

            except SagaError:
                # Compensate completed steps in reverse order
                self._state = SagaState.COMPENSATING
                self._log.state = SagaState.COMPENSATING
                compensation_errors: list[str] = []

                for step in reversed(completed_steps):
                    if step.compensation is None:
                        continue
                    try:
                        self._log.record_step_compensation(step.name)
                        step.compensation()
                        step.compensated = True
                        self._log.record_step_compensated(step.name)
                    except Exception as comp_err:
                        compensation_errors.append(
                            f"Compensation for step '{step.name}' failed: {comp_err}"
                        )

                if compensation_errors:
                    self._state = SagaState.FAILED
                    self._log.state = SagaState.FAILED
                    self._log.completed_at = time.time()
                    raise SagaError(
                        f"Saga '{self.name}' failed with compensation errors: "
                        + "; ".join(compensation_errors)
                    )

                self._state = SagaState.COMPENSATED
                self._log.state = SagaState.COMPENSATED
                self._log.completed_at = time.time()
                raise

    def to_dict(self) -> dict[str, Any]:
        return {
            "sagaId": self.saga_id,
            "name": self.name,
            "state": self._state.value,
            "steps": [s.to_dict() for s in self._steps],
            "log": self._log.to_dict(),
        }


class SagaOrchestrator:
    """Manages multiple sagas and their persistence."""

    def __init__(self):
        self._sagas: dict[str, Saga] = {}
        self._lock = threading.RLock()

    def start_saga(self, name: str, *, saga_id: str | None = None,
                   metadata: dict[str, Any] | None = None) -> Saga:
        """Create and register a new saga."""
        with self._lock:
            saga = Saga(name, saga_id=saga_id, metadata=metadata)
            self._sagas[saga.saga_id] = saga
            return saga

    def get_saga(self, saga_id: str) -> Saga | None:
        with self._lock:
            return self._sagas.get(saga_id)

    def list_sagas(self) -> list[str]:
        with self._lock:
            return sorted(self._sagas.keys())

    def get_saga_log(self, saga_id: str) -> SagaLog | None:
        saga = self.get_saga(saga_id)
        return saga.log if saga else None
