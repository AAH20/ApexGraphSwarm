"""Durable, local-first SQLite scheduler for versioned ApexGraphSwarm plans.

This module provides job bookkeeping only. It does not call model providers,
execute tools, start subprocesses, or claim that logical agents are workers.
Paid work must carry an explicit integer micro-USD reservation at admission.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import secrets
import os
import sqlite3
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


MAX_PLAN_BYTES = 2 * 1024 * 1024
MAX_RESULT_BYTES = 1024 * 1024
MAX_EVENT_BYTES = 64 * 1024
MAX_TASKS = 10_000
MAX_AGENTS = 300
MAX_ACTIVE = 64
MAX_ATTEMPTS = 10
MAX_LEASE_SECONDS = 300
MIN_LEASE_SECONDS = 1
_SECRET_FIELD = re.compile(r"(?:^|[_-])(api[_-]?key|access[_-]?token|password|secret|credential|authorization)(?:$|[_-])", re.IGNORECASE)


class ControlError(ValueError):
    """A rejected plan, transition, or control-plane request."""


class ConflictError(ControlError):
    """An idempotency key or state transition conflicts with stored state."""


class LeaseError(ConflictError):
    """The lease is missing, expired, or fenced by a newer attempt."""


class BudgetError(ControlError):
    """Cost is unknown, malformed, or exceeds a reserved amount."""


def _json(value: Any, *, maximum: int, label: str) -> str:
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError, RecursionError) as exc:
        raise ControlError(f"{label} must be finite JSON data.") from exc
    if len(encoded.encode("utf-8")) > maximum:
        raise ControlError(f"{label} exceeds its size limit.")
    return encoded


def _identifier(value: Any, label: str, maximum: int = 128) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or "\x00" in value:
        raise ControlError(f"{label} must be a non-empty string of at most {maximum} characters.")
    return value


def _microdollars(value: Any, label: str) -> int:
    # bool is an int subclass; accept only exact integers.
    if type(value) is not int or value < 0 or value > 2**63 - 1:
        raise BudgetError(f"{label} must be a known integer number of micro-USD in SQLite's supported range.")
    return value


def _reject_secret_fields(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str) and _SECRET_FIELD.search(key) and not key.lower().endswith(("_ref", "-ref")):
                raise ControlError("Task payloads must use secret references, not credential fields.")
            _reject_secret_fields(child)
    elif isinstance(value, list):
        for child in value:
            _reject_secret_fields(child)


class ControlStore:
    """Transactional durable job queue backed by one SQLite database.

    `max_registered_agents` bounds logical identities per run, while
    `max_active` separately bounds live leases across all runs in this DB.
    A task's `reservedCostMicrousd` is the maximum spend admitted for all of
    its attempts combined. Unknown cost must not be represented as zero.
    """

    def __init__(self, db_path: str | os.PathLike[str], *, max_active: int = 4,
                 max_registered_agents: int = MAX_AGENTS,
                 max_run_cost_microusd: int | None = None,
                 clock=time.time):
        if type(max_active) is not int or not 1 <= max_active <= MAX_ACTIVE:
            raise ControlError(f"max_active must be between 1 and {MAX_ACTIVE}.")
        if type(max_registered_agents) is not int or not 1 <= max_registered_agents <= MAX_AGENTS:
            raise ControlError(f"max_registered_agents must be between 1 and {MAX_AGENTS}.")
        if max_run_cost_microusd is not None:
            _microdollars(max_run_cost_microusd, "max_run_cost_microusd")
        self.max_active = max_active
        self.max_registered_agents = max_registered_agents
        self.max_run_cost_microusd = max_run_cost_microusd
        self._clock = clock
        self._lock = threading.RLock()
        path = str(db_path)
        if path != ":memory:":
            path = str(Path(path).expanduser().resolve())
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path, timeout=15, isolation_level=None,
                                   check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.execute("PRAGMA busy_timeout=15000")
        if path != ":memory:":
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.execute("PRAGMA synchronous=FULL")
        self._initialize()

    def close(self) -> None:
        with self._lock:
            self._db.close()

    def __enter__(self) -> "ControlStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                yield self._db
            except BaseException:
                self._db.execute("ROLLBACK")
                raise
            else:
                self._db.execute("COMMIT")

    def _initialize(self) -> None:
        with self._lock:
            self._db.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    version INTEGER NOT NULL,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    plan_digest TEXT NOT NULL,
                    status TEXT NOT NULL,
                    budget_microusd INTEGER NOT NULL,
                    spent_microusd INTEGER NOT NULL DEFAULT 0,
                    budget_exceeded INTEGER NOT NULL DEFAULT 0,
                    cancel_requested INTEGER NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS agents (
                    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                    agent_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    PRIMARY KEY(run_id, agent_id)
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                    task_key TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    execution_class TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL,
                    reserved_cost_microusd INTEGER NOT NULL,
                    actual_cost_microusd INTEGER NOT NULL DEFAULT 0,
                    worker_id TEXT,
                    lease_token TEXT,
                    lease_expires_at REAL,
                    claimed_at REAL,
                    completed_at REAL,
                    result_json TEXT,
                    error TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    UNIQUE(run_id, task_key),
                    FOREIGN KEY(run_id, agent_id) REFERENCES agents(run_id, agent_id)
                        ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS dependencies (
                    run_id TEXT NOT NULL,
                    task_key TEXT NOT NULL,
                    dependency_key TEXT NOT NULL,
                    PRIMARY KEY(run_id, task_key, dependency_key),
                    FOREIGN KEY(run_id, task_key) REFERENCES tasks(run_id, task_key)
                        ON DELETE CASCADE,
                    FOREIGN KEY(run_id, dependency_key) REFERENCES tasks(run_id, task_key)
                        ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS events (
                    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                    sequence INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    task_id TEXT,
                    created_at REAL NOT NULL,
                    data_json TEXT NOT NULL,
                    PRIMARY KEY(run_id, sequence)
                );
                CREATE TABLE IF NOT EXISTS control_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS tasks_ready ON tasks(run_id, status, created_at);
                CREATE INDEX IF NOT EXISTS tasks_lease ON tasks(status, lease_expires_at);
                CREATE INDEX IF NOT EXISTS deps_task ON dependencies(run_id, task_key);
            """)
            # Additive migration for databases created by earlier local prototypes.
            migrations = {
                "runs": {"cancel_requested": "INTEGER NOT NULL DEFAULT 0"},
                "tasks": {"execution_class": "TEXT NOT NULL DEFAULT 'external'",
                          "claimed_at": "REAL", "completed_at": "REAL"},
            }
            for table, columns in migrations.items():
                present = {row[1] for row in self._db.execute(f"PRAGMA table_info({table})")}
                for column, declaration in columns.items():
                    if column not in present:
                        self._db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")
            configured = dict(self._db.execute("SELECT key,value FROM control_meta"))
            expected = {"max_active": str(self.max_active),
                        "max_registered_agents": str(self.max_registered_agents)}
            if configured and any(configured.get(key) != value for key, value in expected.items()):
                raise ControlError("Scheduler capacity settings do not match this database's persisted configuration.")
            if not configured:
                self._db.executemany("INSERT INTO control_meta(key,value) VALUES(?,?)", expected.items())

    def create_run(self, plan: dict[str, Any], *, idempotency_key: str,
                   budget_microusd: int | None) -> dict[str, Any]:
        """Validate, reserve budget and atomically create a DAG run.

        All work must specify a known integer budget and a reservation per task.
        Deterministic/local work may use zero. Reusing the same idempotency key
        with identical plan and budget returns the original run.
        """
        key = _identifier(idempotency_key, "idempotency_key", 200)
        if budget_microusd is None:
            raise BudgetError("A known integer budget is required; unknown cost cannot be admitted.")
        budget = _microdollars(budget_microusd, "budget_microusd")
        normalized, digest, total_reservation = self._validate_plan(plan)
        if self.max_run_cost_microusd is not None and budget > self.max_run_cost_microusd:
            raise BudgetError("Run budget exceeds the configured maximum.")
        if total_reservation > budget:
            raise BudgetError("Task reservations exceed the run budget.")
        now = self._now()
        run_id = str(uuid.uuid4())
        with self._transaction() as db:
            prior = db.execute("SELECT id,plan_digest,budget_microusd FROM runs WHERE idempotency_key=?", (key,)).fetchone()
            if prior:
                if prior["plan_digest"] != digest or prior["budget_microusd"] != budget:
                    raise ConflictError("Idempotency key was already used for a different plan or budget.")
                return self._status(db, prior["id"])
            db.execute("INSERT INTO runs(id,version,idempotency_key,plan_digest,status,budget_microusd,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                       (run_id, 1, key, digest, "queued", budget, now, now))
            for agent in normalized["agents"]:
                db.execute("INSERT INTO agents(run_id,agent_id,name) VALUES(?,?,?)",
                           (run_id, agent["id"], agent["name"]))
            for task in normalized["tasks"]:
                task_id = str(uuid.uuid4())
                db.execute("""INSERT INTO tasks(task_id,run_id,task_key,agent_id,execution_class,status,payload_json,
                              max_attempts,reserved_cost_microusd,created_at,updated_at)
                              VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                           (task_id, run_id, task["id"], task["agentId"], task["executionClass"], "pending",
                            task["payloadJson"], task["maxAttempts"], task["reservedCostMicrousd"], now, now))
            for task in normalized["tasks"]:
                for dependency in task["dependencies"]:
                    db.execute("INSERT INTO dependencies(run_id,task_key,dependency_key) VALUES(?,?,?)",
                               (run_id, task["id"], dependency))
            self._event(db, run_id, "run.created", None, now,
                        {"agentCount": len(normalized["agents"]), "taskCount": len(normalized["tasks"]),
                         "reservedCostMicrousd": total_reservation})
            return self._status(db, run_id)

    def claim(self, run_id: str, worker_id: str, *, lease_seconds: int = 30,
              agent_id: str | None = None) -> dict[str, Any] | None:
        """Atomically lease one ready task, subject to the global active cap."""
        run_id = _identifier(run_id, "run_id")
        worker = _identifier(worker_id, "worker_id")
        lease = self._lease_duration(lease_seconds)
        if agent_id is not None:
            agent_id = _identifier(agent_id, "agent_id")
        now = self._now()
        with self._transaction() as db:
            if not db.execute("SELECT 1 FROM runs WHERE id=?", (run_id,)).fetchone():
                raise ControlError("Run not found.")
            self._recover_expired(db, now)
            run = db.execute("SELECT status FROM runs WHERE id=?", (run_id,)).fetchone()
            if run["status"] not in {"queued", "running"}:
                return None
            active = db.execute("SELECT COUNT(*) FROM tasks WHERE status='running' AND lease_expires_at>?", (now,)).fetchone()[0]
            if active >= self.max_active:
                return None
            query = """SELECT t.* FROM tasks t WHERE t.run_id=? AND t.status='pending'
                       AND NOT EXISTS (SELECT 1 FROM dependencies d JOIN tasks p
                         ON p.run_id=d.run_id AND p.task_key=d.dependency_key
                         WHERE d.run_id=t.run_id AND d.task_key=t.task_key AND p.status!='succeeded')"""
            params: list[Any] = [run_id]
            if agent_id is not None:
                query += " AND t.agent_id=?"
                params.append(agent_id)
            query += " ORDER BY t.created_at,t.task_key LIMIT 1"
            task = db.execute(query, params).fetchone()
            if task is None:
                self._refresh_run(db, run_id, now)
                return None
            token = secrets.token_urlsafe(32)
            expires = now + lease
            db.execute("UPDATE tasks SET status='running',attempts=attempts+1,worker_id=?,lease_token=?,lease_expires_at=?,claimed_at=?,completed_at=NULL,updated_at=? WHERE task_id=? AND status='pending'",
                       (worker, token, expires, now, now, task["task_id"]))
            self._event(db, run_id, "task.claimed", task["task_id"], now,
                        {"taskKey": task["task_key"], "agentId": task["agent_id"], "workerId": worker,
                         "attempt": task["attempts"] + 1, "leaseExpiresAt": expires})
            db.execute("UPDATE runs SET status='running',updated_at=? WHERE id=? AND status='queued'", (now, run_id))
            return self._task(db, task["task_id"], include_token=True)

    def heartbeat(self, task_id: str, lease_token: str, *, lease_seconds: int = 30) -> dict[str, Any]:
        task_id = _identifier(task_id, "task_id")
        token = _identifier(lease_token, "lease_token", 256)
        lease = self._lease_duration(lease_seconds)
        now = self._now()
        with self._transaction() as db:
            task = self._leased_task(db, task_id, token, now)
            expiry = now + lease
            db.execute("UPDATE tasks SET lease_expires_at=?,updated_at=? WHERE task_id=?", (expiry, now, task_id))
            self._event(db, task["run_id"], "task.heartbeat", task_id, now, {"leaseExpiresAt": expiry})
            return self._task(db, task_id, include_token=True)

    def complete(self, task_id: str, lease_token: str, result: Any,
                 actual_cost_microusd: int | None = None) -> dict[str, Any]:
        task_id = _identifier(task_id, "task_id")
        token = _identifier(lease_token, "lease_token", 256)
        if actual_cost_microusd is None:
            raise BudgetError("Actual cost must be known before completion; use zero only for verified free/local work.")
        actual = _microdollars(actual_cost_microusd, "actual_cost_microusd")
        encoded = _json(result, maximum=MAX_RESULT_BYTES, label="result")
        now = self._now()
        with self._transaction() as db:
            task = self._leased_task(db, task_id, token, now)
            self._settle(db, task, actual)
            db.execute("UPDATE tasks SET status='succeeded',actual_cost_microusd=actual_cost_microusd+?,result_json=?,error=NULL,worker_id=NULL,lease_token=NULL,lease_expires_at=NULL,completed_at=?,updated_at=? WHERE task_id=?",
                       (actual, encoded, now, now, task_id))
            self._event(db, task["run_id"], "task.completed", task_id, now,
                        {"actualCostMicrousd": actual, "attempt": task["attempts"]})
            self._refresh_run(db, task["run_id"], now)
            return self._status(db, task["run_id"])

    def fail(self, task_id: str, lease_token: str, error: str, *, retryable: bool = False,
             actual_cost_microusd: int | None = None) -> dict[str, Any]:
        task_id = _identifier(task_id, "task_id")
        token = _identifier(lease_token, "lease_token", 256)
        err = _identifier(error, "error", 2_000)
        if type(retryable) is not bool:
            raise ControlError("retryable must be a boolean.")
        if actual_cost_microusd is None:
            raise BudgetError("Actual cost must be known; use zero only for verified free/local work.")
        actual = _microdollars(actual_cost_microusd, "actual_cost_microusd")
        now = self._now()
        with self._transaction() as db:
            task = self._leased_task(db, task_id, token, now)
            self._settle(db, task, actual)
            if retryable and task["execution_class"] not in {"fixture", "local_idempotent", "external_idempotent"}:
                raise ConflictError("Automatic retry requires an explicitly retry-safe executionClass.")
            reservation_left = task["reserved_cost_microusd"] - task["actual_cost_microusd"] - actual
            retry_budget_remains = task["reserved_cost_microusd"] == 0 or reservation_left > 0
            will_retry = retryable and task["attempts"] < task["max_attempts"] and retry_budget_remains
            next_status = "pending" if will_retry else "failed"
            over_reservation = actual > task["reserved_cost_microusd"] - task["actual_cost_microusd"]
            db.execute("UPDATE tasks SET status=?,actual_cost_microusd=actual_cost_microusd+?,error=?,worker_id=NULL,lease_token=NULL,lease_expires_at=NULL,completed_at=?,updated_at=? WHERE task_id=?",
                       (next_status, actual, err, None if will_retry else now, now, task_id))
            self._event(db, task["run_id"], "task.retry_scheduled" if will_retry else "task.failed",
                        task_id, now, {"error": err, "attempt": task["attempts"],
                                       "actualCostMicrousd": actual, "reservationExceeded": over_reservation})
            if not will_retry:
                self._fail_blocked_descendants(db, task["run_id"], task["task_key"], now)
            self._refresh_run(db, task["run_id"], now)
            return self._status(db, task["run_id"])

    def cancel(self, run_id: str) -> dict[str, Any]:
        run_id = _identifier(run_id, "run_id")
        now = self._now()
        with self._transaction() as db:
            run = db.execute("SELECT status FROM runs WHERE id=?", (run_id,)).fetchone()
            if not run:
                return None
            if run["status"] not in {"succeeded", "failed", "cancelled"}:
                rows = db.execute("SELECT task_id,task_key,status FROM tasks WHERE run_id=? AND status IN ('pending','running')", (run_id,)).fetchall()
                for task in rows:
                    row = db.execute("SELECT execution_class,reserved_cost_microusd FROM tasks WHERE task_id=?", (task["task_id"],)).fetchone()
                    ambiguous = task["status"] == "running" and not (row["execution_class"] in {"fixture", "local_idempotent"} and row["reserved_cost_microusd"] == 0)
                    status = "needs_reconciliation" if ambiguous else "cancelled"
                    db.execute("UPDATE tasks SET status=?,worker_id=NULL,lease_token=NULL,lease_expires_at=NULL,error=?,completed_at=?,updated_at=? WHERE task_id=?",
                               (status, "Cancellation requested; external execution outcome is unknown." if ambiguous else "Run cancelled.", None if ambiguous else now, now, task["task_id"]))
                    self._event(db, run_id, "task.cancel_requested" if ambiguous else "task.cancelled", task["task_id"], now, {"taskKey": task["task_key"]})
                db.execute("UPDATE runs SET cancel_requested=1,updated_at=? WHERE id=?", (now, run_id))
                self._refresh_run(db, run_id, now)
                self._event(db, run_id, "run.cancelled" if self._status(db, run_id)["run"]["status"] == "cancelled" else "run.cancel_requested", None, now, {})
            return self._status(db, run_id)

    def status(self, run_id: str) -> dict[str, Any] | None:
        run_id = _identifier(run_id, "run_id")
        with self._lock:
            return self._status(self._db, run_id)

    def recover_expired(self, now: float | None = None) -> dict[str, int]:
        """Requeue expired attempts with budget left, fail exhausted attempts."""
        moment = self._now() if now is None else float(now)
        if not math.isfinite(moment) or moment < 0:
            raise ControlError("Recovery timestamp must be a finite non-negative value.")
        with self._transaction() as db:
            return self._recover_expired(db, moment)

    def reconcile(self, task_id: str, *, outcome: str,
                  actual_cost_microusd: int | None, result: Any = None) -> dict[str, Any]:
        """Resolve an expired/cancelled external attempt after operator/provider inspection.

        `not_started` is the only outcome that makes a task pending again, and
        only when cancellation was not requested and attempts remain.
        """
        task_id = _identifier(task_id, "task_id")
        if outcome not in {"succeeded", "failed", "not_started"}:
            raise ControlError("outcome must be succeeded, failed, or not_started.")
        if actual_cost_microusd is None:
            raise BudgetError("Reconciliation requires a known integer actual cost.")
        actual = _microdollars(actual_cost_microusd, "actual_cost_microusd")
        if outcome == "not_started" and actual != 0:
            raise BudgetError("A not_started attempt must have zero actual cost.")
        encoded = _json(result, maximum=MAX_RESULT_BYTES, label="result") if outcome == "succeeded" else None
        now = self._now()
        with self._transaction() as db:
            task = db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if not task or task["status"] != "needs_reconciliation":
                raise ConflictError("Task is not awaiting reconciliation.")
            run = db.execute("SELECT cancel_requested FROM runs WHERE id=?", (task["run_id"],)).fetchone()
            if outcome == "not_started":
                status = "cancelled" if run["cancel_requested"] else ("pending" if task["attempts"] < task["max_attempts"] else "failed")
                db.execute("UPDATE tasks SET status=?,error=NULL,worker_id=NULL,lease_token=NULL,lease_expires_at=NULL,completed_at=?,updated_at=? WHERE task_id=?",
                           (status, None if status == "pending" else now, now, task_id))
            else:
                self._settle(db, task, actual)
                status = outcome
                db.execute("UPDATE tasks SET status=?,actual_cost_microusd=actual_cost_microusd+?,result_json=?,error=?,worker_id=NULL,lease_token=NULL,lease_expires_at=NULL,completed_at=?,updated_at=? WHERE task_id=?",
                           (outcome, actual, encoded, None if outcome == "succeeded" else "External execution failed after reconciliation.", now, now, task_id))
                if outcome == "failed":
                    self._fail_blocked_descendants(db, task["run_id"], task["task_key"], now)
            self._event(db, task["run_id"], "task.reconciled", task_id, now,
                        {"outcome": outcome, "actualCostMicrousd": actual})
            if status == "failed":
                self._fail_blocked_descendants(db, task["run_id"], task["task_key"], now)
            self._refresh_run(db, task["run_id"], now)
            return self._status(db, task["run_id"])

    def _validate_plan(self, plan: Any) -> tuple[dict[str, Any], str, int]:
        encoded = _json(plan, maximum=MAX_PLAN_BYTES, label="plan")
        if not isinstance(plan, dict) or set(plan) != {"version", "agents", "tasks"}:
            raise ControlError("Plan must contain exactly version, agents, and tasks.")
        if type(plan["version"]) is not int or plan["version"] != 1:
            raise ControlError("Plan version 1 is required.")
        agents_raw, tasks_raw = plan["agents"], plan["tasks"]
        if not isinstance(agents_raw, list) or not 1 <= len(agents_raw) <= self.max_registered_agents:
            raise ControlError(f"Plan must register 1 to {self.max_registered_agents} logical agents.")
        if not isinstance(tasks_raw, list) or not 1 <= len(tasks_raw) <= MAX_TASKS:
            raise ControlError(f"Plan must contain 1 to {MAX_TASKS} tasks.")
        agents: list[dict[str, str]] = []
        agent_ids: set[str] = set()
        for row in agents_raw:
            if not isinstance(row, dict) or set(row) - {"id", "name"}:
                raise ControlError("Each agent must contain only id and optional name.")
            agent_id = _identifier(row.get("id"), "agent.id")
            name = row.get("name", agent_id)
            name = _identifier(name, "agent.name", 200)
            if agent_id in agent_ids:
                raise ControlError("Agent IDs must be unique within a run.")
            agent_ids.add(agent_id)
            agents.append({"id": agent_id, "name": name})
        tasks: list[dict[str, Any]] = []
        task_ids: set[str] = set()
        reservation = 0
        for row in tasks_raw:
            if not isinstance(row, dict) or set(row) - {"id", "agentId", "dependencies", "payload", "reservedCostMicrousd", "maxAttempts", "executionClass"}:
                raise ControlError("Task contains unsupported fields.")
            task_id = _identifier(row.get("id"), "task.id")
            agent_id = _identifier(row.get("agentId"), "task.agentId")
            if task_id in task_ids:
                raise ControlError("Task IDs must be unique within a run.")
            if agent_id not in agent_ids:
                raise ControlError(f"Task {task_id} references an unknown logical agent.")
            deps = row.get("dependencies", [])
            if not isinstance(deps, list) or any(not isinstance(dep, str) for dep in deps):
                raise ControlError(f"Task {task_id} dependencies must be a list of task IDs.")
            if len(set(deps)) != len(deps) or task_id in deps:
                raise ControlError(f"Task {task_id} has duplicate or self dependencies.")
            cost = _microdollars(row.get("reservedCostMicrousd"), f"task {task_id} reservedCostMicrousd")
            execution_class = row.get("executionClass", "external")
            if execution_class not in {"fixture", "local_idempotent", "external_idempotent", "external"}:
                raise ControlError(f"Task {task_id} has an unsupported executionClass.")
            if execution_class == "fixture" and cost != 0:
                raise BudgetError(f"Task {task_id} fixture execution must have zero reserved cost.")
            attempts = row.get("maxAttempts", 1)
            if type(attempts) is not int or not 1 <= attempts <= MAX_ATTEMPTS:
                raise ControlError(f"Task {task_id} maxAttempts must be from 1 to {MAX_ATTEMPTS}.")
            payload = _json(row.get("payload", {}), maximum=MAX_RESULT_BYTES, label=f"task {task_id} payload")
            _reject_secret_fields(json.loads(payload))
            reservation += cost
            if reservation > 2**63 - 1:
                raise BudgetError("Combined task reservations exceed the supported integer range.")
            task_ids.add(task_id)
            tasks.append({"id": task_id, "agentId": agent_id, "dependencies": deps,
                          "payloadJson": payload, "reservedCostMicrousd": cost,
                          "maxAttempts": attempts, "executionClass": execution_class})
        for task in tasks:
            missing = set(task["dependencies"]) - task_ids
            if missing:
                raise ControlError(f"Task {task['id']} has missing dependencies: {', '.join(sorted(missing))}.")
        self._validate_acyclic(tasks)
        canonical = {"version": 1, "agents": sorted(agents, key=lambda a: a["id"]),
                     "tasks": sorted(({"id": t["id"], "agentId": t["agentId"],
                                       "dependencies": sorted(t["dependencies"]),
                                       "payload": json.loads(t["payloadJson"]),
                                       "reservedCostMicrousd": t["reservedCostMicrousd"],
                                       "maxAttempts": t["maxAttempts"],
                                       "executionClass": t["executionClass"]} for t in tasks), key=lambda t: t["id"])}
        digest = hashlib.sha256(_json({"plan": canonical, "reserved": reservation}, maximum=MAX_PLAN_BYTES, label="plan").encode()).hexdigest()
        return {"agents": agents, "tasks": tasks}, digest, reservation

    @staticmethod
    def _validate_acyclic(tasks: list[dict[str, Any]]) -> None:
        indegree = {task["id"]: len(task["dependencies"]) for task in tasks}
        children: dict[str, list[str]] = {task["id"]: [] for task in tasks}
        for task in tasks:
            for dependency in task["dependencies"]:
                children[dependency].append(task["id"])
        ready = [task_id for task_id, degree in indegree.items() if degree == 0]
        visited = 0
        while ready:
            current = ready.pop()
            visited += 1
            for child in children[current]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
        if visited != len(indegree):
            raise ControlError("Task dependencies contain a cycle.")

    def _recover_expired(self, db: sqlite3.Connection, now: float) -> dict[str, int]:
        expired = db.execute("SELECT * FROM tasks WHERE status='running' AND lease_expires_at<=? ORDER BY lease_expires_at", (now,)).fetchall()
        counts = {"requeued": 0, "failed": 0}
        for task in expired:
            safe_to_retry = task["execution_class"] == "fixture" and task["reserved_cost_microusd"] == 0
            retry = safe_to_retry and task["attempts"] < task["max_attempts"]
            ambiguous = not safe_to_retry
            status = "pending" if retry else ("needs_reconciliation" if ambiguous else "failed")
            db.execute("UPDATE tasks SET status=?,worker_id=NULL,lease_token=NULL,lease_expires_at=NULL,error=?,completed_at=?,updated_at=? WHERE task_id=?",
                       (status, "Lease expired; prior worker was fenced; reconcile external outcome." if ambiguous else "Lease expired; prior worker was fenced.", None if retry or ambiguous else now, now, task["task_id"]))
            self._event(db, task["run_id"], "task.lease_expired", task["task_id"], now,
                        {"attempt": task["attempts"], "requeued": retry, "needsReconciliation": ambiguous})
            event = "task.requeued" if retry else ("task.needs_reconciliation" if ambiguous else "task.failed")
            self._event(db, task["run_id"], event, task["task_id"], now,
                        {"reason": "lease_expired", "attempt": task["attempts"]})
            if retry:
                counts["requeued"] += 1
            elif not ambiguous:
                counts["failed"] += 1
                self._fail_blocked_descendants(db, task["run_id"], task["task_key"], now)
            self._refresh_run(db, task["run_id"], now)
        return counts

    def _fail_blocked_descendants(self, db: sqlite3.Connection, run_id: str, failed_key: str, now: float) -> None:
        queue = [failed_key]
        seen: set[str] = set()
        while queue:
            parent = queue.pop()
            if parent in seen:
                continue
            seen.add(parent)
            rows = db.execute("SELECT t.task_id,t.task_key FROM dependencies d JOIN tasks t ON t.run_id=d.run_id AND t.task_key=d.task_key WHERE d.run_id=? AND d.dependency_key=? AND t.status='pending'", (run_id, parent)).fetchall()
            for row in rows:
                db.execute("UPDATE tasks SET status='failed',error='Dependency failed',completed_at=?,updated_at=? WHERE task_id=?", (now, now, row["task_id"]))
                self._event(db, run_id, "task.failed", row["task_id"], now,
                            {"taskKey": row["task_key"], "reason": "dependency_failed"})
                queue.append(row["task_key"])

    def _settle(self, db: sqlite3.Connection, task: sqlite3.Row, actual: int) -> None:
        remaining = task["reserved_cost_microusd"] - task["actual_cost_microusd"]
        run = db.execute("SELECT budget_microusd,spent_microusd FROM runs WHERE id=?", (task["run_id"],)).fetchone()
        spent = run["spent_microusd"] + actual
        other_reservations = db.execute("SELECT COALESCE(SUM(reserved_cost_microusd-actual_cost_microusd),0) FROM tasks WHERE run_id=? AND status IN ('pending','running','needs_reconciliation') AND task_id!=?", (task["run_id"], task["task_id"])).fetchone()[0]
        breached = actual > remaining or spent + other_reservations > run["budget_microusd"]
        db.execute("UPDATE runs SET spent_microusd=?,budget_exceeded=CASE WHEN ? THEN 1 ELSE budget_exceeded END,updated_at=? WHERE id=?",
                   (spent, int(breached), self._now(), task["run_id"]))
        if breached:
            self._event(db, task["run_id"], "run.budget_exceeded", task["task_id"], self._now(),
                        {"actualCostMicrousd": actual, "reservationRemainingMicrousd": remaining,
                         "spentMicrousd": spent, "otherReservedMicrousd": other_reservations})

    def _leased_task(self, db: sqlite3.Connection, task_id: str, token: str, now: float) -> sqlite3.Row:
        task = db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if not task:
            raise LeaseError("Task or lease was not found.")
        if task["status"] != "running" or task["lease_token"] != token:
            raise LeaseError("Lease is no longer current; transition was fenced.")
        if task["lease_expires_at"] <= now:
            self._recover_expired(db, now)
            raise LeaseError("Lease expired; transition was fenced.")
        return task

    def _refresh_run(self, db: sqlite3.Connection, run_id: str, now: float) -> None:
        run = db.execute("SELECT status,cancel_requested,budget_exceeded FROM runs WHERE id=?", (run_id,)).fetchone()
        if not run or run["status"] in {"cancelled", "failed", "budget_exceeded"}:
            return
        statuses = [row[0] for row in db.execute("SELECT status FROM tasks WHERE run_id=?", (run_id,))]
        if run["budget_exceeded"]:
            status = "budget_exceeded"
        elif any(item == "needs_reconciliation" for item in statuses):
            status = "needs_reconciliation"
        elif run["cancel_requested"]:
            status = "cancelled"
        elif any(item == "failed" for item in statuses):
            status = "failed"
        elif all(status == "succeeded" for status in statuses):
            status = "succeeded"
        elif any(status == "running" for status in statuses):
            status = "running"
        else:
            status = "queued"
        previous = run["status"]
        db.execute("UPDATE runs SET status=?,updated_at=? WHERE id=?", (status, now, run_id))
        if status in {"succeeded", "failed"} and previous not in {"succeeded", "failed"}:
            self._event(db, run_id, "run.completed", None, now, {"status": status})

    def _event(self, db: sqlite3.Connection, run_id: str, event_type: str,
               task_id: str | None, now: float, data: Any) -> None:
        encoded = _json(data, maximum=MAX_EVENT_BYTES, label="event")
        sequence = db.execute("SELECT COALESCE(MAX(sequence),0)+1 FROM events WHERE run_id=?", (run_id,)).fetchone()[0]
        db.execute("INSERT INTO events(run_id,sequence,event_type,task_id,created_at,data_json) VALUES(?,?,?,?,?,?)",
                   (run_id, sequence, event_type, task_id, now, encoded))

    def _status(self, db: sqlite3.Connection, run_id: str) -> dict[str, Any] | None:
        row = db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if not row:
            return None
        spent = row["spent_microusd"]
        reserved = db.execute("SELECT COALESCE(SUM(reserved_cost_microusd-actual_cost_microusd),0) FROM tasks WHERE run_id=? AND status IN ('pending','running','needs_reconciliation')", (run_id,)).fetchone()[0]
        agents = [{"id": a["agent_id"], "name": a["name"]} for a in db.execute("SELECT * FROM agents WHERE run_id=? ORDER BY agent_id", (run_id,))]
        tasks = [self._task(db, task["task_id"]) for task in db.execute("SELECT task_id FROM tasks WHERE run_id=? ORDER BY created_at,task_key", (run_id,))]
        events = [{"sequence": e["sequence"], "type": e["event_type"], "taskId": e["task_id"],
                   "at": e["created_at"], "data": json.loads(e["data_json"])}
                  for e in db.execute("SELECT * FROM events WHERE run_id=? ORDER BY sequence", (run_id,))]
        return {"run": {"id": row["id"], "status": row["status"], "version": row["version"],
                         "createdAt": row["created_at"], "updatedAt": row["updated_at"],
                         "idempotencyKey": row["idempotency_key"], "budgetMicrousd": row["budget_microusd"],
                         "cancelRequested": bool(row["cancel_requested"]),
                         "reservedMicrousd": reserved, "spentMicrousd": spent,
                         "remainingMicrousd": row["budget_microusd"] - reserved - spent,
                         "budgetExceeded": bool(row["budget_exceeded"])},
                "agents": agents, "tasks": tasks, "events": events}

    def _task(self, db: sqlite3.Connection, task_id: str, *, include_token: bool = False) -> dict[str, Any]:
        row = db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        dependencies = [item[0] for item in db.execute("SELECT dependency_key FROM dependencies WHERE run_id=? AND task_key=? ORDER BY dependency_key", (row["run_id"], row["task_key"]))]
        task = {"taskId": row["task_id"], "id": row["task_key"], "agentId": row["agent_id"],
                "status": row["status"], "dependencies": dependencies, "payload": json.loads(row["payload_json"]),
                "attempts": row["attempts"], "maxAttempts": row["max_attempts"],
                "executionClass": row["execution_class"],
                "reservedCostMicrousd": row["reserved_cost_microusd"],
                "actualCostMicrousd": row["actual_cost_microusd"], "workerId": row["worker_id"],
                "leaseExpiresAt": row["lease_expires_at"], "claimedAt": row["claimed_at"],
                "completedAt": row["completed_at"], "result": json.loads(row["result_json"]) if row["result_json"] is not None else None,
                "error": row["error"]}
        if include_token and row["lease_token"]:
            task["leaseToken"] = row["lease_token"]
        return task

    def _lease_duration(self, value: Any) -> int:
        if type(value) is not int or not MIN_LEASE_SECONDS <= value <= MAX_LEASE_SECONDS:
            raise ControlError(f"lease_seconds must be between {MIN_LEASE_SECONDS} and {MAX_LEASE_SECONDS}.")
        return value

    def _now(self) -> float:
        value = float(self._clock())
        if not math.isfinite(value) or value < 0:
            raise ControlError("Clock returned an invalid timestamp.")
        return value


def _cli_request(request: dict[str, Any]) -> dict[str, Any]:
    path = request.get("dbPath")
    if not isinstance(path, str) or not path:
        raise ControlError("dbPath is required.")
    action = request.get("action")
    with ControlStore(path, max_active=request.get("maxActive", 4)) as store:
        if action == "initialize":
            return {"initialized": True, "dbPath": path}
        if action == "create":
            return store.create_run(request.get("plan"), idempotency_key=request.get("idempotencyKey"),
                                    budget_microusd=request.get("budgetMicrousd"))
        if action == "status":
            result = store.status(request.get("runId"))
            if result is None:
                raise ControlError("Run not found.")
            return result
        if action == "claim":
            return {"task": store.claim(request.get("runId"), request.get("workerId"),
                                        lease_seconds=request.get("leaseSeconds", 30),
                                        agent_id=request.get("agentId"))}
        if action == "heartbeat":
            return {"task": store.heartbeat(request.get("taskId"), request.get("leaseToken"),
                                            lease_seconds=request.get("leaseSeconds", 30))}
        if action == "complete":
            return store.complete(request.get("taskId"), request.get("leaseToken"),
                                  request.get("result"), request.get("actualCostMicrousd"))
        if action == "fail":
            return store.fail(request.get("taskId"), request.get("leaseToken"), request.get("error"),
                              retryable=request.get("retryable", False),
                              actual_cost_microusd=request.get("actualCostMicrousd"))
        if action == "cancel":
            result = store.cancel(request.get("runId"))
            if result is None:
                raise ControlError("Run not found.")
            return result
        if action == "recover":
            return store.recover_expired()
        raise ControlError("Unsupported action.")


def main() -> int:
    try:
        raw = sys.stdin.read(MAX_PLAN_BYTES + 1)
        if len(raw.encode("utf-8")) > MAX_PLAN_BYTES:
            raise ControlError("CLI request exceeds the 2 MiB limit.")
        request = json.loads(raw)
        response = _cli_request(request)
        print(json.dumps({"ok": True, "data": response}, ensure_ascii=False, separators=(",", ":")))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc) if isinstance(exc, ControlError) else "Control operation failed."}, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
