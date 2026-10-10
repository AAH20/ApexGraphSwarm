"""Durable, local-first SQLite scheduler for versioned ApexGraphSwarm plans.

This module provides job bookkeeping only. It does not call model providers,
execute tools, start subprocesses, or claim that logical agents are workers.
Paid work must carry an explicit integer micro-USD reservation at admission.
"""

from __future__ import annotations

import hashlib
import hmac
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
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .access import AccessDenied, authorize, initialize_access_schema, new_grant_id
from .identity import (WorkerIdentityError, initialize_identity_schema,
                       issue_credential, token_digest, verify_credential)
from .ledger import attempt_id, record_attempt_start, settle_attempt
from .specialist_access import (SpecialistContractError, activate_contract,
                                approval_is_satisfied, approve_contract, bind_plan,
                                configure_approvers, contract_status,
                                create_contract, initialize_specialist_schema,
                                revoke_contract, validate_task_contract)


MAX_PLAN_BYTES = 2 * 1024 * 1024
MAX_RESULT_BYTES = 1024 * 1024
MAX_EVENT_BYTES = 64 * 1024
MAX_TASKS = 10_000
MAX_AGENTS = 300
MAX_ACTIVE = 64
MAX_ATTEMPTS = 10
MAX_CHECKPOINTS_PER_ATTEMPT = 12
MAX_CHECKPOINT_BYTES = 64 * 1024
MAX_CHECKPOINT_TOTAL_BYTES = 128 * 1024
MAX_LEASE_SECONDS = 300
MIN_LEASE_SECONDS = 1
MAX_RESOURCE_CONCURRENCY = 10_000
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


def _reject_checkpoint_fields(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str) and key == "tokenUsage":
                # This is the one permitted token-related receipt field. Keep
                # its schema intentionally narrow: arbitrary token metadata or
                # nested values could otherwise become a credential exfiltration
                # path under a benign-looking key.
                allowed = {"prompt", "completion", "total", "reasoning", "cachedPrompt"}
                if (not isinstance(child, dict) or not set(child).issubset(allowed)
                        or any(v is not None and (type(v) is not int or v < 0)
                               for v in child.values())):
                    raise ControlError("tokenUsage must contain only known non-negative integer or null counts.")
                continue
            if isinstance(key, str) and re.search(r"token|credential|password|secret|api[_-]?key|authorization", key, re.IGNORECASE):
                raise ControlError("Checkpoints must not contain credentials or secret fields.")
            _reject_checkpoint_fields(child)
    elif isinstance(value, list):
        for child in value:
            _reject_checkpoint_fields(child)


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
        try:
            self._initialize()
        except BaseException:
            self._db.close()
            raise

    def _settle_execution_attempt(self, db: sqlite3.Connection, *, task_id: str, attempt: int,
                                  outcome: str, actual_cost_microusd: int | None,
                                  settled_at: float, receipt_json: str) -> None:
        row = db.execute("SELECT grant_id,reserved_microusd,outcome FROM execution_attempts WHERE attempt_id=?",
                         (attempt_id(task_id, attempt),)).fetchone()
        if (row and row["grant_id"] and row["outcome"] in {"running", "unknown"}
                and outcome != "unknown" and actual_cost_microusd is not None):
            db.execute("UPDATE access_grants SET reserved_microusd=MAX(0,reserved_microusd-?), "
                       "spent_microusd=spent_microusd+? WHERE grant_id=?",
                       (row["reserved_microusd"], actual_cost_microusd or 0, row["grant_id"]))
        settle_attempt(db, task_id=task_id, attempt=attempt, outcome=outcome,
                       actual_cost_microusd=actual_cost_microusd, settled_at=settled_at,
                       receipt_json=receipt_json)

    def enroll_worker(self, *, worker_id: str, principal_id: str,
                      expires_at: float) -> dict[str, Any]:
        """Enroll a worker and return its opaque credential exactly once."""
        worker = _identifier(worker_id, "worker_id")
        principal = _identifier(principal_id, "principal_id")
        if type(expires_at) not in (int, float):
            raise ControlError("expires_at must be a future finite timestamp.")
        expiry = float(expires_at)
        now = self._now()
        if not math.isfinite(expiry) or expiry <= now:
            raise ControlError("expires_at must be a future finite timestamp.")
        credential = issue_credential()
        with self._transaction() as db:
            if db.execute("SELECT 1 FROM workers WHERE worker_id=?", (worker,)).fetchone():
                raise ConflictError("Worker ID is already enrolled; use a new worker ID.")
            db.execute("INSERT INTO workers(worker_id,principal_id,token_hash,expires_at,created_at) VALUES(?,?,?,?,?)",
                       (worker, principal, token_digest(credential), expiry, now))
        return {"workerId": worker, "principalId": principal, "expiresAt": expiry,
                "credential": credential}

    def revoke_worker(self, worker_id: str) -> bool:
        worker = _identifier(worker_id, "worker_id")
        now = self._now()
        with self._transaction() as db:
            cursor = db.execute("UPDATE workers SET revoked_at=? WHERE worker_id=? AND revoked_at IS NULL",
                                (now, worker))
            return cursor.rowcount == 1

    def _authenticate_worker(self, db: sqlite3.Connection, worker_id: str,
                             credential: str | None, now: float):
        try:
            return verify_credential(db, worker_id=worker_id,
                                     credential=credential, now=now)
        except WorkerIdentityError as exc:
            raise AccessDenied(str(exc)) from None

    def _authenticate_lease(self, db: sqlite3.Connection, task: sqlite3.Row,
                            credential: str | None, now: float, *, check_grant: bool = True):
        identity = self._authenticate_worker(db, task["worker_id"], credential, now)
        attempt = db.execute("SELECT principal_id,grant_id FROM execution_attempts "
                             "WHERE task_id=? AND attempt_number=?",
                             (task["task_id"], task["attempts"])).fetchone()
        if not attempt or attempt["principal_id"] != identity["principal_id"]:
            raise AccessDenied("Worker authentication failed.")
        if check_grant and task["execution_class"] != "fixture":
            grant = db.execute("SELECT expires_at,revoked_at FROM access_grants WHERE grant_id=?",
                               (attempt["grant_id"],)).fetchone() if attempt["grant_id"] else None
            if not grant or grant["revoked_at"] is not None or grant["expires_at"] <= now:
                raise AccessDenied("Capability grant expired or was revoked during the lease.")
        return identity

    def grant_access(self, *, principal_id: str, tool_id: str, resource_id: str,
                     max_budget_microusd: int, expires_at: float) -> dict[str, Any]:
        """Create a local exact capability grant. Caller authenticates principal identity."""
        principal = _identifier(principal_id, "principal_id")
        tool = _identifier(tool_id, "tool_id")
        resource = _identifier(resource_id, "resource_id")
        budget = _microdollars(max_budget_microusd, "max_budget_microusd")
        if type(expires_at) not in (int, float):
            raise ControlError("expires_at must be a future finite timestamp.")
        expiry = float(expires_at)
        if not math.isfinite(expiry) or expiry <= self._now():
            raise ControlError("expires_at must be a future finite timestamp.")
        now = self._now()
        grant_id = new_grant_id()
        with self._transaction() as db:
            db.execute("INSERT INTO access_grants(grant_id,principal_id,tool_id,resource_id,max_budget_microusd,expires_at,created_at) VALUES(?,?,?,?,?,?,?)",
                       (grant_id, principal, tool, resource, budget, expiry, now))
        return {"grantId": grant_id, "principalId": principal, "tool": tool,
                "resource": resource, "maxBudgetMicrousd": budget, "expiresAt": expiry,
                "spentMicrousd": 0, "reservedMicrousd": 0, "revokedAt": None}

    def revoke_access(self, grant_id: str) -> bool:
        """Revoke a grant immediately; the next claim checks revocation transactionally."""
        grant = _identifier(grant_id, "grant_id")
        now = self._now()
        with self._transaction() as db:
            cursor = db.execute("UPDATE access_grants SET revoked_at=? WHERE grant_id=? AND revoked_at IS NULL", (now, grant))
            return cursor.rowcount == 1

    def configure_specialist_approvers(self, principal_ids: Any) -> dict[str, Any]:
        now = self._now()
        try:
            with self._transaction() as db:
                return configure_approvers(db, principal_ids, now)
        except SpecialistContractError as exc:
            raise ControlError(str(exc)) from None

    def create_specialist_contract(self, *, idempotency_key: str,
                                   design: Any, assignment: Any) -> dict[str, Any]:
        now = self._now()
        try:
            with self._transaction() as db:
                return create_contract(db, idempotency_key=idempotency_key,
                                       design_input=design, assignment_input=assignment,
                                       now=now)
        except SpecialistContractError as exc:
            raise ControlError(str(exc)) from None

    def approve_specialist_contract(self, contract_id: str, worker_id: str,
                                    credential: str | None) -> dict[str, Any]:
        now = self._now()
        try:
            with self._transaction() as db:
                return approve_contract(db, contract_id=contract_id, worker_id=worker_id,
                                        credential=credential, now=now)
        except SpecialistContractError as exc:
            raise AccessDenied(str(exc)) from None

    def activate_specialist_contract(self, contract_id: str) -> dict[str, Any]:
        now = self._now()
        try:
            with self._transaction() as db:
                return activate_contract(db, contract_id, now)
        except SpecialistContractError as exc:
            raise ControlError(str(exc)) from None

    def revoke_specialist_contract(self, contract_id: str) -> bool:
        now = self._now()
        try:
            with self._transaction() as db:
                return revoke_contract(db, contract_id, now)
        except SpecialistContractError as exc:
            raise ControlError(str(exc)) from None

    def specialist_contract_status(self, contract_id: str) -> dict[str, Any]:
        try:
            with self._lock:
                self._db.execute("BEGIN")
                try:
                    result = contract_status(self._db, contract_id, now=self._now())
                except BaseException:
                    self._db.execute("ROLLBACK")
                    raise
                else:
                    self._db.execute("COMMIT")
                    return result
        except SpecialistContractError as exc:
            raise ControlError(str(exc)) from None

    def bind_specialist_contract(self, *, contract_id: str,
                                 plan: Any, task_id: str) -> dict[str, Any]:
        now = self._now()
        try:
            with self._transaction() as db:
                return bind_plan(db, contract_id=contract_id, plan=plan,
                                 task_id=task_id, now=now)
        except SpecialistContractError as exc:
            raise ControlError(str(exc)) from None

    @staticmethod
    def _resource_occupancy(db: sqlite3.Connection, resource_id: str,
                            run_id: str | None = None) -> int:
        """Count live or ambiguous external effects that still hold a slot."""
        query = ("SELECT task_id,attempts,status FROM tasks WHERE resource_id=? "
                 "AND status IN ('running','needs_reconciliation')")
        params: list[Any] = [resource_id]
        if run_id is not None:
            query += " AND run_id=?"
            params.append(run_id)
        rows = db.execute(query, params).fetchall()
        occupied = 0
        for task in rows:
            if task["status"] == "running":
                # An expired lease is not evidence that the remote operation
                # stopped. Recovery will move it to needs_reconciliation.
                occupied += 1
                continue
            attempt = db.execute("SELECT outcome,receipt_json FROM execution_attempts "
                                 "WHERE task_id=? AND attempt_number=?",
                                 (task["task_id"], task["attempts"])).fetchone()
            if not attempt or attempt["outcome"] == "unknown":
                try:
                    receipt = json.loads(attempt["receipt_json"]) if attempt and attempt["receipt_json"] else {}
                except (TypeError, ValueError):
                    receipt = {}
                # A persisted provider result is known to have finished even
                # when its billing amount is unresolved; it does not occupy a
                # running-work slot. All other unknown effects remain held.
                if receipt.get("successfulOutput") is not True:
                    occupied += 1
        return occupied

    def configure_resource_capacity(self, resource_id: str,
                                    max_concurrency: int) -> dict[str, Any]:
        """Configure one exact resource cap without undercutting occupied work."""
        resource = _identifier(resource_id, "resource_id")
        if type(max_concurrency) is not int or not 1 <= max_concurrency <= MAX_RESOURCE_CONCURRENCY:
            raise ControlError("max_concurrency must be an integer from 1 to 10000.")
        now = self._now()
        with self._transaction() as db:
            self._recover_expired(db, now)
            occupied = self._resource_occupancy(db, resource)
            if max_concurrency < occupied:
                raise ConflictError("Resource capacity cannot be lowered below currently occupied or unresolved work.")
            prior = db.execute("SELECT max_concurrency,updated_at FROM resource_capacities WHERE resource_id=?",
                               (resource,)).fetchone()
            changed = prior is None or prior["max_concurrency"] != max_concurrency
            if changed:
                db.execute("INSERT INTO resource_capacities(resource_id,max_concurrency,updated_at) VALUES(?,?,?) "
                           "ON CONFLICT(resource_id) DO UPDATE SET max_concurrency=excluded.max_concurrency,updated_at=excluded.updated_at",
                           (resource, max_concurrency, now))
            return {"resourceId": resource, "maxConcurrency": max_concurrency,
                    "occupiedCount": occupied, "changed": changed,
                    "updatedAt": now if changed else prior["updated_at"]}

    def resource_capacity_status(self, *, limit: int = 1000) -> dict[str, Any]:
        """Return bounded, read-only configured and required resource capacity state."""
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ControlError("resource capacity status limit must be from 1 to 1000.")
        now = self._now()
        with self._lock:
            self._db.execute("BEGIN")
            try:
                total = self._db.execute("SELECT COUNT(*) FROM resource_capacities").fetchone()[0]
                rows = self._db.execute("SELECT resource_id,max_concurrency,updated_at FROM resource_capacities "
                                        "ORDER BY resource_id LIMIT ?", (limit,)).fetchall()
                resources = []
                for row in rows:
                    occupied = self._resource_occupancy(self._db, row["resource_id"])
                    resources.append({"resourceId": row["resource_id"],
                                      "maxConcurrency": row["max_concurrency"],
                                      "occupiedCount": occupied,
                                      "availableCount": max(0, row["max_concurrency"] - occupied),
                                      "overcommitted": occupied > row["max_concurrency"],
                                      "updatedAt": row["updated_at"]})
                required_total = self._db.execute("SELECT COUNT(DISTINCT t.resource_id) FROM tasks t "
                    "LEFT JOIN resource_capacities c ON c.resource_id=t.resource_id "
                    "WHERE t.require_resource_capacity=1 AND c.resource_id IS NULL").fetchone()[0]
                required_rows = self._db.execute("SELECT DISTINCT t.resource_id FROM tasks t "
                    "LEFT JOIN resource_capacities c ON c.resource_id=t.resource_id "
                    "WHERE t.require_resource_capacity=1 AND c.resource_id IS NULL "
                    "ORDER BY t.resource_id LIMIT ?", (limit,)).fetchall()
            except BaseException:
                self._db.execute("ROLLBACK")
                raise
            else:
                self._db.execute("COMMIT")
        return {"resources": resources, "totalConfiguredResources": total,
                "truncated": total > len(resources),
                "requiredButUnconfiguredResources": [row[0] for row in required_rows],
                "totalRequiredButUnconfiguredResources": required_total,
                "requiredResourcesTruncated": required_total > len(required_rows),
                "asOf": now}

    def ledger(self, run_id: str | None = None, *, limit: int = 1000) -> dict[str, Any]:
        """Read stable attempt receipts with explicit coverage and bounded rows."""
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ControlError("ledger limit must be from 1 to 1000.")
        if run_id is not None:
            run_id = _identifier(run_id, "run_id")
        with self._lock:
            return self._ledger_view(self._db, run_id, limit)

    def _ledger_view(self, db: sqlite3.Connection, run_id: str | None,
                     limit: int) -> dict[str, Any]:
        where = " WHERE run_id=?" if run_id is not None else ""
        args = (run_id,) if run_id is not None else ()
        total = db.execute("SELECT COUNT(*) FROM execution_attempts" + where, args).fetchone()[0]
        expected = db.execute("SELECT COALESCE(SUM(attempts),0) FROM tasks" +
                              (" WHERE run_id=?" if run_id is not None else ""), args).fetchone()[0]
        agg = db.execute("""SELECT COALESCE(SUM(actual_cost_microusd),0),
            SUM(CASE WHEN actual_cost_microusd IS NULL THEN 1 ELSE 0 END)
            FROM execution_attempts""" + where, args).fetchone()
        unresolved = (agg[1] or 0) + max(0, expected - total)
        rows = db.execute("SELECT * FROM execution_attempts" + where +
                          " ORDER BY started_at DESC,attempt_id DESC LIMIT ?", (*args, limit)).fetchall()
        checkpoint_total = db.execute("SELECT COUNT(*) FROM worker_checkpoints" + where, args).fetchone()[0]
        checkpoint_rows = db.execute("SELECT task_id,attempt_number,checkpoint_id,value_sha256,byte_length "
                                      "FROM worker_checkpoints WHERE " +
                                      ("run_id=?" if run_id is not None else "1=1") +
                                      " ORDER BY created_at DESC LIMIT 1200", args).fetchall()
        checkpoints: dict[tuple[str, int], list[dict[str, Any]]] = {}
        for checkpoint in checkpoint_rows:
            key = (checkpoint["task_id"], checkpoint["attempt_number"])
            checkpoints.setdefault(key, []).append({"checkpointId": checkpoint["checkpoint_id"],
                                                     "sha256": checkpoint["value_sha256"],
                                                     "byteLength": checkpoint["byte_length"]})
        attempts = [{"attemptId": row["attempt_id"], "taskId": row["task_id"], "runId": row["run_id"],
                     "attempt": row["attempt_number"],
                     "checkpoints": list(reversed(checkpoints.get((row["task_id"], row["attempt_number"]), []))),
                     "workerId": row["worker_id"],
                     "principalId": row["principal_id"], "grantId": row["grant_id"],
                     "tool": row["tool_id"], "resource": row["resource_id"],
                     "reservedMicrousd": row["reserved_microusd"], "startedAt": row["started_at"],
                     "settledAt": row["settled_at"], "outcome": row["outcome"],
                     "actualCostMicrousd": row["actual_cost_microusd"],
                     "receipt": json.loads(row["receipt_json"]) if row["receipt_json"] else None}
                    for row in reversed(rows)]
        return {"attempts": attempts, "totalAttempts": total, "returnedAttempts": len(attempts),
                "truncated": total > len(attempts), "checkpointSummariesTruncated": checkpoint_total > len(checkpoint_rows),
                "knownActualMicrousd": agg[0] or 0,
                "unresolvedCostCount": unresolved, "coverageComplete": total >= expected,
                "allCostsResolved": unresolved == 0}

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
            initialize_access_schema(self._db)
            initialize_identity_schema(self._db)
            initialize_specialist_schema(self._db)
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
                    tool_id TEXT,
                    resource_id TEXT,
                    require_resource_capacity INTEGER NOT NULL DEFAULT 0,
                    resource_concurrency_limit INTEGER,
                    specialist_contract_id TEXT,
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
                CREATE TABLE IF NOT EXISTS resource_capacities (
                    resource_id TEXT PRIMARY KEY,
                    max_concurrency INTEGER NOT NULL CHECK(max_concurrency BETWEEN 1 AND 10000),
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS worker_checkpoints (
                    task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
                    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                    attempt_number INTEGER NOT NULL,
                    worker_id TEXT NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    value_sha256 TEXT NOT NULL,
                    byte_length INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    PRIMARY KEY(task_id,attempt_number,checkpoint_id)
                );
                CREATE INDEX IF NOT EXISTS worker_checkpoints_run ON worker_checkpoints(run_id,created_at);
                CREATE TABLE IF NOT EXISTS provider_receipt_reconciliations (
                    task_id TEXT PRIMARY KEY REFERENCES tasks(task_id) ON DELETE CASCADE,
                    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                    evidence_sha256 TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS provider_generation_ownership (
                    provider TEXT NOT NULL,
                    generation_id TEXT NOT NULL,
                    task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
                    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                    attempt_number INTEGER NOT NULL,
                    call_id TEXT NOT NULL,
                    model TEXT NOT NULL,
                    claimed_at REAL NOT NULL,
                    PRIMARY KEY(provider,generation_id),
                    UNIQUE(task_id,attempt_number,call_id)
                );
                CREATE TABLE IF NOT EXISTS execution_attempts (
                    attempt_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
                    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                    attempt_number INTEGER NOT NULL,
                    worker_id TEXT NOT NULL,
                    principal_id TEXT,
                    grant_id TEXT,
                    tool_id TEXT,
                    resource_id TEXT,
                    reserved_microusd INTEGER NOT NULL,
                    started_at REAL NOT NULL,
                    settled_at REAL,
                    outcome TEXT NOT NULL,
                    actual_cost_microusd INTEGER,
                    receipt_json TEXT,
                    UNIQUE(task_id,attempt_number)
                );
                CREATE INDEX IF NOT EXISTS tasks_ready ON tasks(run_id, status, created_at);
                CREATE INDEX IF NOT EXISTS tasks_lease ON tasks(status, lease_expires_at);
                CREATE INDEX IF NOT EXISTS deps_task ON dependencies(run_id, task_key);
            """)
            # Additive migration for databases created by earlier local prototypes.
            migrations = {
                "runs": {"cancel_requested": "INTEGER NOT NULL DEFAULT 0"},
                "tasks": {"execution_class": "TEXT NOT NULL DEFAULT 'external'",
                          "claimed_at": "REAL", "completed_at": "REAL",
                          "tool_id": "TEXT", "resource_id": "TEXT",
                          "require_resource_capacity": "INTEGER NOT NULL DEFAULT 0",
                          "resource_concurrency_limit": "INTEGER",
                          "specialist_contract_id": "TEXT"},
            }
            for table, columns in migrations.items():
                present = {row[1] for row in self._db.execute(f"PRAGMA table_info({table})")}
                for column, declaration in columns.items():
                    if column not in present:
                        self._db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")
            attempt_columns = {row[1] for row in self._db.execute("PRAGMA table_info(execution_attempts)")}
            for column in ("tool_id", "resource_id"):
                if column not in attempt_columns:
                    self._db.execute(f"ALTER TABLE execution_attempts ADD COLUMN {column} TEXT")
            configured = dict(self._db.execute("SELECT key,value FROM control_meta"))
            expected = {"max_active": str(self.max_active),
                        "max_registered_agents": str(self.max_registered_agents)}
            if configured and any(configured.get(key) != value for key, value in expected.items()):
                raise ControlError("Scheduler capacity settings do not match this database's persisted configuration.")
            if not configured:
                self._db.executemany("INSERT INTO control_meta(key,value) VALUES(?,?)", expected.items())
            self._backfill_provider_generation_ownership()

    def _claim_provider_generation(self, db: sqlite3.Connection, *, provider: str,
                                   generation_id: str, task_id: str, run_id: str,
                                   attempt: int, call_id: str, model: str,
                                   claimed_at: float) -> None:
        """Claim one provider generation ID for exactly one task invocation."""
        provider = _identifier(provider, "provider", 64)
        generation = _identifier(generation_id, "generation_id", 256)
        task = _identifier(task_id, "task_id")
        run = _identifier(run_id, "run_id")
        call = _identifier(call_id, "call_id")
        model_id = _identifier(model, "model", 256)
        if type(attempt) is not int or not 1 <= attempt <= MAX_ATTEMPTS:
            raise ControlError("Provider generation attempt number is invalid.")
        owner = db.execute("SELECT task_id,run_id,attempt_number,call_id,model FROM provider_generation_ownership WHERE provider=? AND generation_id=?",
                           (provider, generation)).fetchone()
        expected = (task, run, attempt, call, model_id)
        if owner:
            actual = (owner["task_id"], owner["run_id"], owner["attempt_number"],
                      owner["call_id"], owner["model"])
            if actual != expected:
                raise ConflictError("Provider generation ID is already bound to a different invocation.")
            return
        prior_call = db.execute("SELECT provider,generation_id,run_id,model FROM provider_generation_ownership WHERE task_id=? AND attempt_number=? AND call_id=?",
                                (task, attempt, call)).fetchone()
        if prior_call:
            raise ConflictError("Provider call is already bound to a different generation ID.")
        try:
            db.execute("INSERT INTO provider_generation_ownership(provider,generation_id,task_id,run_id,attempt_number,call_id,model,claimed_at) VALUES(?,?,?,?,?,?,?,?)",
                       (provider, generation, task, run, attempt, call, model_id, claimed_at))
        except sqlite3.IntegrityError:
            # Another process may have won the unique-key race before this
            # transaction obtained its write lock. Re-read only to distinguish
            # the identical replay from a conflicting owner.
            owner = db.execute("SELECT task_id,run_id,attempt_number,call_id,model FROM provider_generation_ownership WHERE provider=? AND generation_id=?",
                               (provider, generation)).fetchone()
            actual = ((owner["task_id"], owner["run_id"], owner["attempt_number"],
                       owner["call_id"], owner["model"]) if owner else None)
            if actual != expected:
                raise ConflictError("Provider generation ID is already bound to a different invocation.") from None

    def _backfill_provider_generation_ownership(self) -> None:
        """Backfill old response checkpoints once; fail closed on ambiguity."""
        with self._transaction() as db:
            marker = db.execute("SELECT value FROM control_meta WHERE key='provider_generation_ownership_migrated'").fetchone()
            if marker:
                if marker["value"] != "1":
                    raise ControlError("Provider generation ownership migration marker is invalid; inspect the database.")
                return
            audit_rows = db.execute("SELECT task_id,run_id,evidence_sha256,evidence_json,created_at FROM provider_receipt_reconciliations ORDER BY created_at,task_id").fetchall()
            for row in audit_rows:
                if len(row["evidence_json"].encode("utf-8")) > MAX_RESULT_BYTES:
                    raise ControlError("Legacy provider reconciliation audit exceeds the evidence limit; inspect the database.")
                if not hmac.compare_digest(hashlib.sha256(row["evidence_json"].encode("utf-8")).hexdigest(),
                                           row["evidence_sha256"]):
                    raise ControlError("Legacy provider reconciliation audit digest is invalid; inspect the database.")
                try:
                    evidence = json.loads(row["evidence_json"])
                except (TypeError, ValueError):
                    raise ControlError("Legacy provider reconciliation audit is malformed; inspect the database.") from None
                if (not isinstance(evidence, dict)
                        or evidence.get("provider") != "openrouter"
                        or evidence.get("provenance") != "trusted_local_operator_assertion"
                        or not isinstance(evidence.get("receipts"), list)
                        or not 1 <= len(evidence["receipts"]) <= MAX_ATTEMPTS * MAX_CHECKPOINTS_PER_ATTEMPT):
                    raise ControlError("Legacy provider reconciliation audit is ambiguous; inspect the database.")
                task = db.execute("SELECT run_id FROM tasks WHERE task_id=?", (row["task_id"],)).fetchone()
                if not task or task["run_id"] != row["run_id"]:
                    raise ControlError("Legacy provider audit task binding is ambiguous; inspect the database.")
                for entry in evidence["receipts"]:
                    if not isinstance(entry, dict) or set(entry) != {"attempt", "callId", "receipt"}:
                        raise ControlError("Legacy provider audit receipt identity is ambiguous; inspect the database.")
                    attempt, call_id, receipt = entry["attempt"], entry["callId"], entry["receipt"]
                    if (type(attempt) is not int or not isinstance(call_id, str)
                            or not isinstance(receipt, dict) or receipt.get("provider") != "openrouter"):
                        raise ControlError("Legacy provider audit receipt identity is ambiguous; inspect the database.")
                    generation_id, model = receipt.get("generationId"), receipt.get("model")
                    if not isinstance(generation_id, str) or not isinstance(model, str):
                        raise ControlError("Legacy provider audit is missing its generation or model identity.")
                    self._claim_provider_generation(db, provider="openrouter",
                                                    generation_id=generation_id,
                                                    task_id=row["task_id"], run_id=row["run_id"],
                                                    attempt=attempt, call_id=call_id,
                                                    model=model, claimed_at=row["created_at"])
            rows = db.execute("SELECT task_id,run_id,attempt_number,checkpoint_id,value_json,created_at FROM worker_checkpoints WHERE checkpoint_id LIKE '%:receipt' ORDER BY created_at,task_id,attempt_number,checkpoint_id").fetchall()
            for row in rows:
                value = json.loads(row["value_json"])
                if not isinstance(value, dict) or value.get("provider") != "openrouter":
                    continue
                generation_id = value.get("generationId")
                if generation_id is None:
                    # Historical response without a usable ID remains
                    # unreconcilable; it cannot reserve an unknown identity.
                    continue
                call_id = value.get("callId")
                if not isinstance(call_id, str) or row["checkpoint_id"] != call_id + ":receipt":
                    raise ControlError("Legacy provider receipt identity is ambiguous; inspect the database before reopening.")
                start_row = db.execute("SELECT value_json FROM worker_checkpoints WHERE task_id=? AND attempt_number=? AND checkpoint_id=?",
                                       (row["task_id"], row["attempt_number"], call_id + ":started")).fetchone()
                if not start_row:
                    raise ControlError("Legacy provider receipt has no matching started checkpoint; inspect the database before reopening.")
                start = json.loads(start_row["value_json"])
                model = value.get("model")
                if (not isinstance(start, dict) or start.get("provider") != "openrouter"
                        or start.get("callId") != call_id or start.get("model") != model
                        or not isinstance(model, str) or not model.strip()):
                    raise ControlError("Legacy provider receipt model binding is ambiguous; inspect the database before reopening.")
                task = db.execute("SELECT run_id FROM tasks WHERE task_id=?", (row["task_id"],)).fetchone()
                if not task or task["run_id"] != row["run_id"]:
                    raise ControlError("Legacy provider receipt task binding is ambiguous; inspect the database before reopening.")
                self._claim_provider_generation(db, provider="openrouter", generation_id=generation_id,
                                                task_id=row["task_id"], run_id=row["run_id"],
                                                attempt=row["attempt_number"], call_id=call_id,
                                                model=model, claimed_at=row["created_at"])
            db.execute("INSERT INTO control_meta(key,value) VALUES('provider_generation_ownership_migrated','1')")

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
            required_resources = {task["resourceId"] for task in normalized["tasks"]
                                  if task["requireResourceCapacity"]}
            for resource_id in required_resources:
                if not db.execute("SELECT 1 FROM resource_capacities WHERE resource_id=?",
                                  (resource_id,)).fetchone():
                    raise ControlError(f"Task requires administrator-configured capacity for resource {resource_id!r}.")
            for task in normalized["tasks"]:
                contract_id = task["specialistContractId"]
                if contract_id is None:
                    continue
                if not task["requireResourceCapacity"]:
                    raise ControlError("Specialist-bound tasks must require configured resource capacity.")
                try:
                    validate_task_contract(db, contract_id=contract_id,
                                           agent_id=task["agentId"],
                                           tool_id=task["toolId"],
                                           resource_id=task["resourceId"],
                                           payload=json.loads(task["payloadJson"]), now=now)
                except SpecialistContractError as exc:
                    raise ControlError(str(exc)) from None
            db.execute("INSERT INTO runs(id,version,idempotency_key,plan_digest,status,budget_microusd,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                       (run_id, 1, key, digest, "queued", budget, now, now))
            for agent in normalized["agents"]:
                db.execute("INSERT INTO agents(run_id,agent_id,name) VALUES(?,?,?)",
                           (run_id, agent["id"], agent["name"]))
            for task in normalized["tasks"]:
                task_id = str(uuid.uuid4())
                db.execute("""INSERT INTO tasks(task_id,run_id,task_key,agent_id,execution_class,tool_id,resource_id,
                              require_resource_capacity,resource_concurrency_limit,specialist_contract_id,status,payload_json,
                              max_attempts,reserved_cost_microusd,created_at,updated_at)
                              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                           (task_id, run_id, task["id"], task["agentId"], task["executionClass"], task["toolId"],
                            task["resourceId"], int(task["requireResourceCapacity"]), task["resourceConcurrencyLimit"],
                            task["specialistContractId"], "pending", task["payloadJson"], task["maxAttempts"],
                            task["reservedCostMicrousd"], now, now))
            for task in normalized["tasks"]:
                for dependency in task["dependencies"]:
                    db.execute("INSERT INTO dependencies(run_id,task_key,dependency_key) VALUES(?,?,?)",
                               (run_id, task["id"], dependency))
            self._event(db, run_id, "run.created", None, now,
                        {"agentCount": len(normalized["agents"]), "taskCount": len(normalized["tasks"]),
                         "reservedCostMicrousd": total_reservation})
            return self._status(db, run_id)

    def claim(self, run_id: str, worker_id: str, *, lease_seconds: int = 30,
              agent_id: str | None = None, principal_id: str | None = None,
              task_id: str | None = None,
              _credential: str | None = None, _require_identity: bool = False) -> dict[str, Any] | None:
        """Atomically lease one ready task, subject to the global active cap."""
        run_id = _identifier(run_id, "run_id")
        worker = _identifier(worker_id, "worker_id")
        lease = self._lease_duration(lease_seconds)
        if agent_id is not None:
            agent_id = _identifier(agent_id, "agent_id")
        if principal_id is not None:
            principal_id = _identifier(principal_id, "principal_id")
        if task_id is not None:
            task_id = _identifier(task_id, "task_id")
        now = self._now()
        with self._transaction() as db:
            identity = None
            if _require_identity or _credential is not None:
                identity = self._authenticate_worker(db, worker, _credential, now)
                if principal_id is not None and principal_id != identity["principal_id"]:
                    raise AccessDenied("Worker authentication failed.")
                principal_id = identity["principal_id"]
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
            if task_id is not None:
                query += " AND t.task_id=?"
                params.append(task_id)
            query += " ORDER BY t.created_at,t.task_key"
            candidates = db.execute(query, params).fetchall()
            task = None
            for candidate in candidates:
                resource_id = candidate["resource_id"]
                if candidate["require_resource_capacity"] and not db.execute(
                        "SELECT 1 FROM resource_capacities WHERE resource_id=?", (resource_id,)).fetchone():
                    continue
                if resource_id is not None:
                    configured = db.execute("SELECT max_concurrency FROM resource_capacities WHERE resource_id=?",
                                            (resource_id,)).fetchone()
                    per_run_limit = candidate["resource_concurrency_limit"]
                    if configured is not None and self._resource_occupancy(db, resource_id) >= configured[0]:
                        continue
                    if per_run_limit is not None and self._resource_occupancy(
                            db, resource_id, run_id=run_id) >= per_run_limit:
                        continue
                task = candidate
                break
            if task is None:
                self._refresh_run(db, run_id, now)
                return None
            grant_id = None
            principal = principal_id
            specialist_expiry = now + lease
            if task["specialist_contract_id"] is not None:
                if identity is None:
                    raise AccessDenied("Specialist-bound tasks require authenticated worker dispatch.")
                try:
                    _contract_row, contract = validate_task_contract(
                        db, contract_id=task["specialist_contract_id"],
                        agent_id=task["agent_id"], tool_id=task["tool_id"],
                        resource_id=task["resource_id"],
                        payload=json.loads(task["payload_json"]), now=now)
                except SpecialistContractError as exc:
                    raise AccessDenied(str(exc)) from None
                if contract["workerId"] != worker or contract["principalId"] != identity["principal_id"]:
                    raise AccessDenied("Authenticated worker does not match the specialist contract.")
                specialist_expiry = contract["expiresAt"]
            attempt_reservation = task["reserved_cost_microusd"] - task["actual_cost_microusd"]
            if task["execution_class"] != "fixture":
                if not task["tool_id"] or not task["resource_id"]:
                    raise AccessDenied("Nonfixture task lacks an exact tool/resource capability scope.")
                grant_id = authorize(db, principal_id=principal, tool_id=task["tool_id"],
                                     resource_id=task["resource_id"],
                                     budget_microusd=attempt_reservation, now=now)
                grant_expiry = db.execute("SELECT expires_at FROM access_grants WHERE grant_id=?", (grant_id,)).fetchone()[0]
            else:
                grant_expiry = now + lease
            token = secrets.token_urlsafe(32)
            identity_expiry = identity["expires_at"] if identity is not None else now + lease
            expires = min(now + lease, grant_expiry, identity_expiry, specialist_expiry)
            attempt_number = task["attempts"] + 1
            db.execute("UPDATE tasks SET status='running',attempts=attempts+1,worker_id=?,lease_token=?,lease_expires_at=?,claimed_at=?,completed_at=NULL,updated_at=? WHERE task_id=? AND status='pending'",
                       (worker, token, expires, now, now, task["task_id"]))
            record_attempt_start(db, task_id=task["task_id"], run_id=run_id, attempt=attempt_number,
                                 worker_id=worker, principal_id=principal, grant_id=grant_id,
                                 reserved_microusd=attempt_reservation, tool_id=task["tool_id"],
                                 resource_id=task["resource_id"], started_at=now)
            if grant_id:
                db.execute("UPDATE access_grants SET reserved_microusd=reserved_microusd+? WHERE grant_id=?",
                           (attempt_reservation, grant_id))
            self._event(db, run_id, "task.claimed", task["task_id"], now,
                        {"taskKey": task["task_key"], "agentId": task["agent_id"], "workerId": worker,
                         "attempt": task["attempts"] + 1, "leaseExpiresAt": expires})
            db.execute("UPDATE runs SET status='running',updated_at=? WHERE id=? AND status='queued'", (now, run_id))
            return self._task(db, task["task_id"], include_token=True)

    def claim_authenticated(self, run_id: str, worker_id: str, credential: str | None,
                            *, lease_seconds: int = 30,
                            agent_id: str | None = None,
                            task_id: str | None = None) -> dict[str, Any] | None:
        return self.claim(run_id, worker_id, lease_seconds=lease_seconds,
                          agent_id=agent_id, task_id=task_id, _credential=credential,
                          _require_identity=True)

    def heartbeat(self, task_id: str, lease_token: str, *, lease_seconds: int = 30,
                  _credential: str | None = None, _require_identity: bool = False) -> dict[str, Any]:
        task_id = _identifier(task_id, "task_id")
        token = _identifier(lease_token, "lease_token", 256)
        lease = self._lease_duration(lease_seconds)
        now = self._now()
        with self._transaction() as db:
            task = self._leased_task(db, task_id, token, now)
            identity = None
            if _require_identity or _credential is not None:
                identity = self._authenticate_lease(db, task, _credential, now)
            expiry = now + lease
            if identity is not None:
                expiry = min(expiry, identity["expires_at"])
            if task["specialist_contract_id"] is not None:
                if identity is None:
                    raise AccessDenied("Specialist-bound leases require authenticated heartbeats.")
                try:
                    _contract_row, contract = validate_task_contract(
                        db, contract_id=task["specialist_contract_id"],
                        agent_id=task["agent_id"], tool_id=task["tool_id"],
                        resource_id=task["resource_id"],
                        payload=json.loads(task["payload_json"]), now=now)
                except SpecialistContractError as exc:
                    raise AccessDenied(str(exc)) from None
                if contract["workerId"] != task["worker_id"] or contract["principalId"] != identity["principal_id"]:
                    raise AccessDenied("Authenticated worker does not match the specialist contract.")
                expiry = min(expiry, contract["expiresAt"])
            if task["execution_class"] != "fixture":
                attempt = db.execute("SELECT grant_id FROM execution_attempts WHERE task_id=? AND attempt_number=?",
                                     (task_id, task["attempts"])).fetchone()
                grant = db.execute("SELECT expires_at,revoked_at FROM access_grants WHERE grant_id=?",
                                   (attempt["grant_id"],)).fetchone() if attempt and attempt["grant_id"] else None
                if not grant or grant["revoked_at"] is not None or grant["expires_at"] <= now:
                    raise AccessDenied("Capability grant expired or was revoked during the lease.")
                expiry = min(expiry, grant["expires_at"])
            db.execute("UPDATE tasks SET lease_expires_at=?,updated_at=? WHERE task_id=?", (expiry, now, task_id))
            self._event(db, task["run_id"], "task.heartbeat", task_id, now, {"leaseExpiresAt": expiry})
            return self._task(db, task_id, include_token=True)

    def heartbeat_authenticated(self, task_id: str, lease_token: str,
                                credential: str | None, *, lease_seconds: int = 30) -> dict[str, Any]:
        return self.heartbeat(task_id, lease_token, lease_seconds=lease_seconds,
                              _credential=credential, _require_identity=True)

    def complete(self, task_id: str, lease_token: str, result: Any,
                 actual_cost_microusd: int | None = None, *,
                 _credential: str | None = None, _require_identity: bool = False) -> dict[str, Any]:
        task_id = _identifier(task_id, "task_id")
        token = _identifier(lease_token, "lease_token", 256)
        if actual_cost_microusd is None:
            raise BudgetError("Actual cost must be known before legacy completion; use authenticated completion for unknown cost.")
        actual = _microdollars(actual_cost_microusd, "actual_cost_microusd")
        encoded = _json(result, maximum=MAX_RESULT_BYTES, label="result")
        now = self._now()
        with self._transaction() as db:
            task = self._leased_task(db, task_id, token, now)
            if _require_identity or _credential is not None:
                self._authenticate_lease(db, task, _credential, now)
            self._settle(db, task, actual)
            self._settle_execution_attempt(db, task_id=task_id, attempt=task["attempts"], outcome="succeeded",
                                           actual_cost_microusd=actual, settled_at=now,
                                           receipt_json=_json({"outcome": "succeeded", "actualCostMicrousd": actual}, maximum=MAX_EVENT_BYTES, label="receipt"))
            db.execute("UPDATE tasks SET status='succeeded',actual_cost_microusd=actual_cost_microusd+?,result_json=?,error=NULL,worker_id=NULL,lease_token=NULL,lease_expires_at=NULL,completed_at=?,updated_at=? WHERE task_id=?",
                       (actual, encoded, now, now, task_id))
            self._event(db, task["run_id"], "task.completed", task_id, now,
                        {"actualCostMicrousd": actual, "attempt": task["attempts"]})
            self._refresh_run(db, task["run_id"], now)
            return self._status(db, task["run_id"])

    def complete_authenticated(self, task_id: str, lease_token: str, credential: str | None,
                               result: Any, actual_cost_microusd: int | None = None) -> dict[str, Any]:
        _reject_checkpoint_fields(result)
        encoded = _json(result, maximum=MAX_RESULT_BYTES, label="result")
        if isinstance(credential, str) and credential in encoded:
            raise ControlError("Result must not contain the worker credential.")
        if actual_cost_microusd is None:
            return self._complete_authenticated_unknown_cost(task_id, lease_token, credential, result)
        return self.complete(task_id, lease_token, result, actual_cost_microusd,
                             _credential=credential, _require_identity=True)

    def _complete_authenticated_unknown_cost(self, task_id: str, lease_token: str,
                                             credential: str | None, result: Any) -> dict[str, Any]:
        task_id = _identifier(task_id, "task_id")
        token = _identifier(lease_token, "lease_token", 256)
        encoded = _json(result, maximum=MAX_RESULT_BYTES, label="result")
        _reject_checkpoint_fields(result)
        if isinstance(credential, str) and credential in encoded:
            raise ControlError("Result must not contain the worker credential.")
        now = self._now()
        with self._transaction() as db:
            task = self._leased_task(db, task_id, token, now)
            self._authenticate_lease(db, task, credential, now)
            self._settle_execution_attempt(db, task_id=task_id, attempt=task["attempts"],
                                           outcome="unknown", actual_cost_microusd=None,
                                           settled_at=now,
                                           receipt_json=_json({"outcome": "unknown",
                                                               "successfulOutput": True},
                                                              maximum=MAX_EVENT_BYTES, label="receipt"))
            db.execute("UPDATE tasks SET status='needs_reconciliation',result_json=?,error=?,worker_id=NULL,lease_token=NULL,lease_expires_at=NULL,completed_at=NULL,updated_at=? WHERE task_id=?",
                       (encoded, "Successful output recorded; actual cost is unresolved.", now, task_id))
            self._event(db, task["run_id"], "task.succeeded_cost_unknown", task_id, now,
                        {"attempt": task["attempts"], "actualCostMicrousd": None,
                         "resultPersisted": True})
            self._refresh_run(db, task["run_id"], now)
            return self._status(db, task["run_id"])

    def fail(self, task_id: str, lease_token: str, error: str, *, retryable: bool = False,
             actual_cost_microusd: int | None = None,
             _credential: str | None = None, _require_identity: bool = False) -> dict[str, Any]:
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
            if _require_identity or _credential is not None:
                self._authenticate_lease(db, task, _credential, now)
            self._settle(db, task, actual)
            if retryable and task["execution_class"] not in {"fixture", "local_idempotent", "external_idempotent"}:
                raise ConflictError("Automatic retry requires an explicitly retry-safe executionClass.")
            self._settle_execution_attempt(db, task_id=task_id, attempt=task["attempts"], outcome="failed",
                                           actual_cost_microusd=actual, settled_at=now,
                                           receipt_json=_json({"outcome": "failed", "actualCostMicrousd": actual}, maximum=MAX_EVENT_BYTES, label="receipt"))
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

    def fail_authenticated(self, task_id: str, lease_token: str, credential: str | None,
                           error: str, *, retryable: bool = False,
                           actual_cost_microusd: int | None = None) -> dict[str, Any]:
        if isinstance(credential, str) and credential in error:
            raise ControlError("Failure details must not contain the worker credential.")
        if actual_cost_microusd is None:
            if retryable:
                raise ConflictError("Unknown-cost failures cannot be automatically retried; reconcile the attempt first.")
            return self._fail_authenticated_unknown_cost(task_id, lease_token, credential, error)
        return self.fail(task_id, lease_token, error, retryable=retryable,
                         actual_cost_microusd=actual_cost_microusd,
                         _credential=credential, _require_identity=True)

    def _fail_authenticated_unknown_cost(self, task_id: str, lease_token: str,
                                        credential: str | None, error: str) -> dict[str, Any]:
        """Fence a failed/cancelled worker promptly while retaining its liability.

        The attempt remains unresolved and its reservation stays held until an
        operator reconciles actual spend. A replay is accepted only for the
        same worker credential, lease token, and failure detail.
        """
        task_id = _identifier(task_id, "task_id")
        token = _identifier(lease_token, "lease_token", 256)
        err = _identifier(error, "error", 2_000)
        now = self._now()
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with self._transaction() as db:
            task = db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if task and task["status"] == "running" and task["lease_token"] is not None:
                if not hmac.compare_digest(task["lease_token"], token):
                    raise LeaseError("Task or lease was not found.")
                # Grant revocation blocks new dispatch and renewal, but an
                # already-running worker must be able to report failure and
                # release the live lease into reconciliation.
                identity = self._authenticate_lease(db, task, credential, now, check_grant=False)
                receipt = {"outcome": "unknown", "reason": "failure_cost_unknown",
                           "leaseTokenSha256": token_hash}
                self._settle_execution_attempt(db, task_id=task_id, attempt=task["attempts"],
                                               outcome="unknown", actual_cost_microusd=None,
                                               settled_at=now,
                                               receipt_json=_json(receipt, maximum=MAX_EVENT_BYTES,
                                                                  label="receipt"))
                db.execute("UPDATE tasks SET status='needs_reconciliation',error=?,worker_id=NULL,lease_token=NULL,lease_expires_at=NULL,completed_at=NULL,updated_at=? WHERE task_id=?",
                           (err, now, task_id))
                self._event(db, task["run_id"], "task.failed_cost_unknown", task_id, now,
                            {"attempt": task["attempts"], "actualCostMicrousd": None})
                self._refresh_run(db, task["run_id"], now)
                return self._status(db, task["run_id"])

            # Idempotent replay after the active lease has been cleared.
            if not task or task["status"] != "needs_reconciliation":
                raise LeaseError("Task or lease was not found.")
            attempt = db.execute("SELECT worker_id,principal_id,outcome,receipt_json FROM execution_attempts "
                                 "WHERE task_id=? AND attempt_number=?",
                                 (task_id, task["attempts"])).fetchone()
            if not attempt or attempt["outcome"] != "unknown" or not attempt["receipt_json"]:
                raise LeaseError("Task or lease was not found.")
            receipt = json.loads(attempt["receipt_json"])
            if receipt.get("reason") != "failure_cost_unknown":
                raise LeaseError("Task or lease was not found.")
            identity = self._authenticate_worker(db, attempt["worker_id"], credential, now)
            if identity["principal_id"] != attempt["principal_id"]:
                raise AccessDenied("Worker authentication failed.")
            if (not hmac.compare_digest(str(receipt.get("leaseTokenSha256", "")), token_hash)
                    or task["error"] != err):
                raise ConflictError("Unknown-cost failure replay does not match its original lease and detail.")
            return self._status(db, task["run_id"])

    def checkpoint_authenticated(self, task_id: str, lease_token: str,
                                 credential: str | None, checkpoint_id: str,
                                 value: Any) -> dict[str, Any]:
        """Persist bounded per-attempt generated output without settling cost."""
        task_id = _identifier(task_id, "task_id")
        token = _identifier(lease_token, "lease_token", 256)
        checkpoint = _identifier(checkpoint_id, "checkpoint_id")
        encoded = _json(value, maximum=MAX_CHECKPOINT_BYTES, label="checkpoint")
        _reject_checkpoint_fields(value)
        if credential is not None and credential in encoded:
            raise ControlError("Checkpoint must not contain the worker credential.")
        payload_bytes = len(encoded.encode("utf-8"))
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        now = self._now()
        with self._transaction() as db:
            task = self._leased_task(db, task_id, token, now)
            self._authenticate_lease(db, task, credential, now, check_grant=False)
            prior = db.execute("SELECT value_json,value_sha256,byte_length FROM worker_checkpoints "
                               "WHERE task_id=? AND attempt_number=? AND checkpoint_id=?",
                               (task_id, task["attempts"], checkpoint)).fetchone()
            if prior:
                if hmac.compare_digest(digest, prior["value_sha256"]) and encoded == prior["value_json"]:
                    return {"taskId": task_id, "attempt": task["attempts"],
                            "checkpointId": checkpoint, "sha256": digest,
                            "byteLength": prior["byte_length"], "value": json.loads(encoded),
                            "duplicate": True}
                raise ConflictError("Checkpoint ID already contains a different value.")
            aggregate = db.execute("SELECT COUNT(*),COALESCE(SUM(byte_length),0) FROM worker_checkpoints "
                                   "WHERE task_id=? AND attempt_number=?",
                                   (task_id, task["attempts"])).fetchone()
            if aggregate[0] >= MAX_CHECKPOINTS_PER_ATTEMPT:
                raise ControlError("Attempt checkpoint count limit exceeded.")
            if aggregate[1] + payload_bytes > MAX_CHECKPOINT_TOTAL_BYTES:
                raise ControlError("Attempt checkpoint byte limit exceeded.")
            if (checkpoint.endswith(":receipt") and isinstance(value, dict)
                    and value.get("provider") == "openrouter" and value.get("generationId") is not None):
                call_id = value.get("callId")
                model = value.get("model")
                if not isinstance(call_id, str) or checkpoint != call_id + ":receipt":
                    raise ControlError("OpenRouter receipt checkpoint call ID is invalid.")
                if not isinstance(model, str) or not model.strip():
                    raise ControlError("OpenRouter receipt checkpoint model is missing.")
                start_row = db.execute("SELECT value_json FROM worker_checkpoints WHERE task_id=? AND attempt_number=? AND checkpoint_id=?",
                                       (task_id, task["attempts"], call_id + ":started")).fetchone()
                if not start_row:
                    raise ConflictError("OpenRouter receipt checkpoint has no matching started call.")
                start = json.loads(start_row["value_json"])
                if (not isinstance(start, dict) or start.get("provider") != "openrouter"
                        or start.get("callId") != call_id or start.get("model") != model):
                    raise ConflictError("OpenRouter receipt checkpoint does not match its started call.")
                self._claim_provider_generation(db, provider="openrouter",
                                                generation_id=value["generationId"],
                                                task_id=task_id, run_id=task["run_id"],
                                                attempt=task["attempts"], call_id=call_id,
                                                model=model, claimed_at=now)
            db.execute("INSERT INTO worker_checkpoints(task_id,run_id,attempt_number,worker_id,checkpoint_id,value_json,value_sha256,byte_length,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                       (task_id, task["run_id"], task["attempts"], task["worker_id"],
                        checkpoint, encoded, digest, payload_bytes, now))
            self._event(db, task["run_id"], "task.checkpoint", task_id, now,
                        {"attempt": task["attempts"], "checkpointId": checkpoint,
                         "sha256": digest, "byteLength": payload_bytes})
            return {"taskId": task_id, "attempt": task["attempts"],
                    "checkpointId": checkpoint, "sha256": digest,
                    "byteLength": payload_bytes, "value": json.loads(encoded),
                    "duplicate": False}

    def read_checkpoints(self, task_id: str, *, attempt: int | None = None,
                         limit: int = MAX_CHECKPOINTS_PER_ATTEMPT) -> dict[str, Any]:
        task = _identifier(task_id, "task_id")
        if type(limit) is not int or not 1 <= limit <= MAX_CHECKPOINTS_PER_ATTEMPT:
            raise ControlError(f"checkpoint limit must be from 1 to {MAX_CHECKPOINTS_PER_ATTEMPT}.")
        if attempt is not None and (type(attempt) is not int or attempt < 1):
            raise ControlError("attempt must be a positive integer.")
        with self._lock:
            if attempt is None:
                rows = self._db.execute("SELECT * FROM worker_checkpoints WHERE task_id=? "
                                        "ORDER BY attempt_number DESC,created_at DESC LIMIT ?",
                                        (task, limit)).fetchall()
            else:
                rows = self._db.execute("SELECT * FROM worker_checkpoints WHERE task_id=? AND attempt_number=? "
                                        "ORDER BY created_at LIMIT ?", (task, attempt, limit)).fetchall()
        return {"taskId": task, "checkpoints": [
            {"attempt": row["attempt_number"], "checkpointId": row["checkpoint_id"],
             "workerId": row["worker_id"], "sha256": row["value_sha256"],
             "byteLength": row["byte_length"], "createdAt": row["created_at"],
             "value": json.loads(row["value_json"])} for row in rows]}

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
                    row = db.execute("SELECT execution_class,reserved_cost_microusd,attempts FROM tasks WHERE task_id=?", (task["task_id"],)).fetchone()
                    ambiguous = task["status"] == "running" and not (row["execution_class"] in {"fixture", "local_idempotent"} and row["reserved_cost_microusd"] == 0)
                    status = "needs_reconciliation" if ambiguous else "cancelled"
                    if task["status"] == "running":
                        self._settle_execution_attempt(db, task_id=task["task_id"], attempt=row["attempts"],
                                                       outcome="unknown" if ambiguous else "cancelled",
                                                       actual_cost_microusd=None if ambiguous else 0, settled_at=now,
                                                       receipt_json=_json({"outcome": "unknown" if ambiguous else "cancelled",
                                                           "reason": "cancel_requested",
                                                           **({} if ambiguous else {"actualCostMicrousd": 0})},
                                                          maximum=MAX_EVENT_BYTES, label="receipt"))
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

    def provider_receipt_context(self, task_id: str) -> dict[str, Any]:
        """Return bounded checkpoint metadata for local OpenRouter reconciliation."""
        task_id = _identifier(task_id, "task_id")
        with self._lock:
            task = self._db.execute("SELECT task_id,run_id,status,attempts,actual_cost_microusd,result_json,tool_id FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if not task:
                raise ControlError("Task not found.")
            rows = self._db.execute("SELECT attempt_number,checkpoint_id,value_json FROM worker_checkpoints WHERE task_id=? AND (checkpoint_id LIKE '%:started' OR checkpoint_id LIKE '%:receipt') ORDER BY attempt_number,created_at", (task_id,)).fetchall()
        return {"taskId": task["task_id"], "runId": task["run_id"], "status": task["status"],
                "attempts": task["attempts"], "actualCostMicrousd": task["actual_cost_microusd"],
                "resultPresent": task["result_json"] is not None, "tool": task["tool_id"],
                "checkpoints": [{"attempt": row["attempt_number"], "checkpointId": row["checkpoint_id"],
                                 "value": json.loads(row["value_json"])} for row in rows]}

    def receipt_reconciliation(self, task_id: str) -> dict[str, Any] | None:
        """Read normalized operator-asserted receipts attached to a settlement."""
        task_id = _identifier(task_id, "task_id")
        with self._lock:
            row = self._db.execute("SELECT evidence_sha256,evidence_json,created_at FROM provider_receipt_reconciliations WHERE task_id=?", (task_id,)).fetchone()
        if not row:
            return None
        evidence = json.loads(row["evidence_json"])
        return {"taskId": task_id, "sha256": row["evidence_sha256"], "createdAt": row["created_at"], **evidence}

    def reconcile_provider_receipts(self, task_id: str, receipts: list[dict[str, Any]],
                                    *, operator_id: str) -> dict[str, Any]:
        """Atomically settle OpenRouter attempts from complete normalized receipts.

        Receipt costs are recomputed from exact USD strings. Every saved started
        call must match one saved response identity and one normalized receipt.
        """
        task_id = _identifier(task_id, "task_id")
        operator = _identifier(operator_id, "operator_id", 128)
        if not isinstance(receipts, list) or not 1 <= len(receipts) <= MAX_ATTEMPTS * MAX_CHECKPOINTS_PER_ATTEMPT:
            raise ControlError("Receipt reconciliation requires a bounded non-empty receipt list.")
        normalized: list[dict[str, Any]] = []
        seen: set[tuple[int, str]] = set()
        for item in receipts:
            if not isinstance(item, dict) or set(item) != {"attempt", "callId", "receipt"}:
                raise ControlError("Each receipt must contain only attempt, callId, and receipt.")
            attempt = item["attempt"]
            if type(attempt) is not int or not 1 <= attempt <= MAX_ATTEMPTS:
                raise ControlError("Receipt attempt number is invalid.")
            call_id = _identifier(item["callId"], "callId")
            key = (attempt, call_id)
            if key in seen:
                raise ControlError("Duplicate call receipt.")
            seen.add(key)
            receipt = item["receipt"]
            if not isinstance(receipt, dict) or receipt.get("provider") != "openrouter":
                raise ControlError("Only normalized OpenRouter receipts are accepted here.")
            allowed_receipt_fields = {
                "provider", "receiptType", "generationId", "responseId", "model",
                "requestedModel", "providerName", "currency", "costUsd",
                "costMicrousd", "costRounding", "costSource", "tokenUsage",
                "reconciliation",
            }
            if set(receipt) != allowed_receipt_fields:
                raise ControlError("Normalized receipt contains unsupported metadata fields.")
            generation_id = _identifier(receipt.get("generationId"), "generationId", 256)
            model = _identifier(receipt.get("model"), "model", 256)
            if receipt.get("receiptType") not in {"completion_response", "generation_metadata"}:
                raise ControlError("Normalized receipt type is invalid.")
            if receipt.get("currency") != "USD" or receipt.get("costRounding") != "ROUND_CEILING":
                raise ControlError("Normalized receipt currency or rounding policy is invalid.")
            if receipt.get("reconciliation") != "expected-generation-id-match":
                raise ControlError("Normalized receipt generation reconciliation is invalid.")
            for optional_text in ("responseId", "requestedModel", "providerName"):
                value = receipt.get(optional_text)
                if value is not None and (not isinstance(value, str) or not value.strip() or len(value) > 256):
                    raise ControlError("Normalized receipt contains invalid optional metadata.")
            if receipt.get("requestedModel") is not None and receipt["requestedModel"] != model:
                raise ControlError("Normalized receipt requested model does not match its returned model.")
            allowed_cost_sources = {"usage.cost", "data.total_cost", "data.usage", "total_cost"}
            source_parts = receipt.get("costSource", "").split("+") if isinstance(receipt.get("costSource"), str) else []
            if (not source_parts or len(source_parts) > len(allowed_cost_sources)
                    or any(source not in allowed_cost_sources for source in source_parts)
                    or len(set(source_parts)) != len(source_parts)):
                raise ControlError("Normalized receipt cost source is invalid.")
            token_usage = receipt.get("tokenUsage")
            token_fields = {"prompt", "completion", "total", "reasoning", "cachedPrompt"}
            if not isinstance(token_usage, dict) or set(token_usage) != token_fields:
                raise ControlError("Normalized receipt token usage shape is invalid.")
            if any(value is not None and (type(value) is not int or value < 0 or value > 1_000_000_000)
                   for value in token_usage.values()):
                raise ControlError("Normalized receipt token usage values are invalid.")
            cost_usd = receipt.get("costUsd")
            cost_microusd = _microdollars(receipt.get("costMicrousd"), "receipt costMicrousd")
            if not isinstance(cost_usd, str) or len(cost_usd) > 80:
                raise ControlError("Normalized receipt must include its exact USD decimal string.")
            try:
                amount = Decimal(cost_usd)
            except (InvalidOperation, ValueError):
                raise ControlError("Normalized receipt USD amount is invalid.") from None
            if not amount.is_finite() or amount < 0:
                raise ControlError("Normalized receipt USD amount is invalid.")
            expected_microusd = int((amount * Decimal(1_000_000)).to_integral_value(rounding=ROUND_CEILING))
            if expected_microusd != cost_microusd:
                raise ControlError("Normalized receipt micro-USD does not reconcile to exact USD cost.")
            normalized.append({"attempt": attempt, "callId": call_id, "receipt": receipt})
        normalized.sort(key=lambda row: (row["attempt"], row["callId"]))
        evidence = {"provenance": "trusted_local_operator_assertion", "operatorId": operator,
                    "provider": "openrouter", "receipts": normalized}
        evidence_json = _json(evidence, maximum=MAX_RESULT_BYTES, label="receipt evidence")
        evidence_digest = hashlib.sha256(evidence_json.encode("utf-8")).hexdigest()
        now = self._now()
        with self._transaction() as db:
            prior = db.execute("SELECT evidence_sha256 FROM provider_receipt_reconciliations WHERE task_id=?", (task_id,)).fetchone()
            if prior:
                if hmac.compare_digest(prior["evidence_sha256"], evidence_digest):
                    task = db.execute("SELECT run_id FROM tasks WHERE task_id=?", (task_id,)).fetchone()
                    if not task:
                        raise ControlError("Task not found.")
                    return self._status(db, task["run_id"])
                raise ConflictError("Task was already reconciled with different provider receipt evidence.")
            task = db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if not task or task["status"] != "needs_reconciliation":
                raise ConflictError("Task is not awaiting receipt reconciliation.")
            if task["tool_id"] not in {"integration:openrouter:review", "integration:openrouter:delegate"}:
                raise ConflictError("This task is not an OpenRouter integration task.")
            checkpoint_rows = db.execute("SELECT attempt_number,checkpoint_id,value_json FROM worker_checkpoints WHERE task_id=? AND (checkpoint_id LIKE '%:started' OR checkpoint_id LIKE '%:receipt') ORDER BY attempt_number,created_at", (task_id,)).fetchall()
            started: dict[tuple[int, str], dict[str, Any]] = {}
            responses: dict[tuple[int, str], dict[str, Any]] = {}
            for row in checkpoint_rows:
                checkpoint_id = row["checkpoint_id"]
                value = json.loads(row["value_json"])
                call_id = value.get("callId") if isinstance(value, dict) else None
                if not isinstance(call_id, str) or checkpoint_id not in {call_id + ":started", call_id + ":receipt"}:
                    raise ConflictError("Saved provider checkpoint identity is incomplete or inconsistent.")
                key = (row["attempt_number"], call_id)
                target = started if checkpoint_id.endswith(":started") else responses
                if key in target:
                    raise ConflictError("Saved provider checkpoints contain duplicate call identities.")
                target[key] = value
            if not started or set(started) != set(responses):
                raise ConflictError("Every started provider call must have a saved response identity before reconciliation.")
            if set(seen) != set(started):
                raise ConflictError("Receipt evidence must cover every started call exactly once.")
            receipt_by_key = {(row["attempt"], row["callId"]): row["receipt"] for row in normalized}
            call_costs: dict[int, int] = {}
            call_summaries: dict[int, list[dict[str, Any]]] = {}
            for key, start in started.items():
                response = responses[key]
                receipt = receipt_by_key[key]
                if start.get("provider") != "openrouter" or response.get("provider") != "openrouter":
                    raise ConflictError("A started call was not recorded as OpenRouter.")
                saved_model = response.get("model")
                saved_generation_id = response.get("generationId")
                if not isinstance(saved_model, str) or start.get("model") != saved_model:
                    raise ConflictError("Saved request and response model IDs do not match.")
                if not isinstance(saved_generation_id, str) or not saved_generation_id:
                    raise ConflictError("Saved generation ID is missing; receipt cannot be bound safely.")
                if receipt["model"] != saved_model or receipt["generationId"] != saved_generation_id:
                    raise ConflictError("Supplied receipt does not match the saved generation and model IDs.")
                self._claim_provider_generation(db, provider="openrouter",
                                                generation_id=saved_generation_id,
                                                task_id=task_id, run_id=task["run_id"],
                                                attempt=key[0], call_id=key[1],
                                                model=saved_model, claimed_at=now)
                saved_cost = response.get("costMicrousd")
                if saved_cost is not None and saved_cost != receipt["costMicrousd"]:
                    raise ConflictError("Supplied receipt conflicts with previously saved provider cost.")
                saved_usd = response.get("costUsd")
                if saved_usd is not None and saved_usd != receipt["costUsd"]:
                    raise ConflictError("Supplied receipt conflicts with previously saved exact USD cost.")
                call_costs[key[0]] = call_costs.get(key[0], 0) + receipt["costMicrousd"]
                if call_costs[key[0]] > 2**63 - 1:
                    raise BudgetError("Reconciled attempt cost exceeds supported accounting range.")
                call_summaries.setdefault(key[0], []).append({"callId": key[1], "generationId": saved_generation_id,
                                                               "model": saved_model, "costUsd": receipt["costUsd"],
                                                               "costMicrousd": receipt["costMicrousd"]})
            attempts = db.execute("SELECT * FROM execution_attempts WHERE task_id=? ORDER BY attempt_number", (task_id,)).fetchall()
            if len(attempts) != task["attempts"] or [row["attempt_number"] for row in attempts] != list(range(1, task["attempts"] + 1)):
                raise ConflictError("Execution attempt history is incomplete.")
            prior_actual = 0
            unresolved_cost = 0
            unresolved_rows = []
            for attempt_row in attempts:
                number = attempt_row["attempt_number"]
                computed = call_costs.get(number, 0)
                if attempt_row["outcome"] == "unknown":
                    if not any(key[0] == number for key in started):
                        raise ConflictError("An unresolved attempt has no started-call evidence.")
                    if attempt_row["actual_cost_microusd"] is not None:
                        raise ConflictError("Unknown attempt unexpectedly already has a settled cost.")
                    unresolved_cost += computed
                    unresolved_rows.append(attempt_row)
                else:
                    known = attempt_row["actual_cost_microusd"]
                    if known is None or known != computed:
                        raise ConflictError("Saved settled attempt cost does not match its provider receipts.")
                    prior_actual += known
            if prior_actual != task["actual_cost_microusd"]:
                raise ConflictError("Task cumulative cost does not match its settled attempt history.")
            _microdollars(unresolved_cost, "unresolved provider cost")
            _microdollars(prior_actual + unresolved_cost, "total provider cost")
            self._settle(db, task, unresolved_cost)
            run = db.execute("SELECT cancel_requested FROM runs WHERE id=?", (task["run_id"],)).fetchone()
            final_status = "succeeded" if task["result_json"] is not None else ("cancelled" if run["cancel_requested"] else "failed")
            for attempt_row in unresolved_rows:
                number = attempt_row["attempt_number"]
                per_attempt = call_costs.get(number, 0)
                attempt_receipt = _json({"outcome": final_status, "actualCostMicrousd": per_attempt,
                                         "reconciledFrom": "openrouter_receipts", "evidenceSha256": evidence_digest,
                                         "calls": call_summaries.get(number, [])},
                                        maximum=MAX_EVENT_BYTES, label="receipt")
                self._settle_execution_attempt(db, task_id=task_id, attempt=number,
                                               outcome=final_status, actual_cost_microusd=per_attempt,
                                               settled_at=now, receipt_json=attempt_receipt)
            db.execute("UPDATE tasks SET status=?,actual_cost_microusd=actual_cost_microusd+?,error=?,worker_id=NULL,lease_token=NULL,lease_expires_at=NULL,completed_at=?,updated_at=? WHERE task_id=?",
                       (final_status, unresolved_cost, None if final_status == "succeeded" else "Provider receipts reconciled; no successful output was retained.", now, now, task_id))
            db.execute("INSERT INTO provider_receipt_reconciliations(task_id,run_id,evidence_sha256,evidence_json,created_at) VALUES(?,?,?,?,?)",
                       (task_id, task["run_id"], evidence_digest, evidence_json, now))
            self._event(db, task["run_id"], "task.provider_receipts_reconciled", task_id, now,
                        {"status": final_status, "provenance": evidence["provenance"], "operatorId": operator,
                         "receiptCount": len(normalized), "evidenceSha256": evidence_digest,
                         "actualCostMicrousd": unresolved_cost})
            self._refresh_run(db, task["run_id"], now)
            return self._status(db, task["run_id"])

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
        encoded = _json(result, maximum=MAX_RESULT_BYTES, label="result") if outcome == "succeeded" and result is not None else None
        now = self._now()
        with self._transaction() as db:
            task = db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if not task or task["status"] != "needs_reconciliation":
                raise ConflictError("Task is not awaiting reconciliation.")
            if task["tool_id"] in {"integration:openrouter:review", "integration:openrouter:delegate"}:
                raise ConflictError("OpenRouter tasks require normalized generation receipts; use receipt reconciliation.")
            run = db.execute("SELECT cancel_requested FROM runs WHERE id=?", (task["run_id"],)).fetchone()
            if outcome == "not_started":
                if task["result_json"] is not None:
                    raise ConflictError("A persisted successful output cannot be reconciled as not_started.")
                self._settle_execution_attempt(db, task_id=task_id, attempt=task["attempts"], outcome="not_started",
                                               actual_cost_microusd=0, settled_at=now,
                                               receipt_json=_json({"outcome": "not_started", "actualCostMicrousd": 0}, maximum=MAX_EVENT_BYTES, label="receipt"))
                status = "cancelled" if run["cancel_requested"] else ("pending" if task["attempts"] < task["max_attempts"] else "failed")
                db.execute("UPDATE tasks SET status=?,error=NULL,worker_id=NULL,lease_token=NULL,lease_expires_at=NULL,completed_at=?,updated_at=? WHERE task_id=?",
                           (status, None if status == "pending" else now, now, task_id))
            else:
                self._settle(db, task, actual)
                self._settle_execution_attempt(db, task_id=task_id, attempt=task["attempts"], outcome=outcome,
                                               actual_cost_microusd=actual, settled_at=now,
                                               receipt_json=_json({"outcome": outcome, "actualCostMicrousd": actual}, maximum=MAX_EVENT_BYTES, label="receipt"))
                status = outcome
                db.execute("UPDATE tasks SET status=?,actual_cost_microusd=actual_cost_microusd+?,result_json=COALESCE(?,result_json),error=?,worker_id=NULL,lease_token=NULL,lease_expires_at=NULL,completed_at=?,updated_at=? WHERE task_id=?",
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
        resource_limits: dict[str, int] = {}
        resource_tasks: dict[str, list[dict[str, Any]]] = {}
        reservation = 0
        for row in tasks_raw:
            if not isinstance(row, dict) or set(row) - {"id", "agentId", "dependencies", "payload", "reservedCostMicrousd", "maxAttempts", "executionClass", "tool", "resource", "requireResourceCapacity", "resourceConcurrencyLimit", "specialistContractId"}:
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
            tool_id = row.get("tool")
            resource_id = row.get("resource")
            require_capacity = row.get("requireResourceCapacity", False)
            if type(require_capacity) is not bool:
                raise ControlError(f"Task {task_id} requireResourceCapacity must be a boolean.")
            resource_limit = row.get("resourceConcurrencyLimit")
            if resource_limit is not None:
                if (type(resource_limit) is not int
                        or not 1 <= resource_limit <= MAX_RESOURCE_CONCURRENCY):
                    raise ControlError(f"Task {task_id} resourceConcurrencyLimit must be from 1 to {MAX_RESOURCE_CONCURRENCY}.")
                if not require_capacity:
                    raise ControlError(f"Task {task_id} resourceConcurrencyLimit requires requireResourceCapacity=true.")
            specialist_contract_id = row.get("specialistContractId")
            if specialist_contract_id is not None:
                specialist_contract_id = _identifier(specialist_contract_id,
                                                     f"task {task_id} specialistContractId")
                if execution_class == "fixture" or resource_id is None or tool_id is None:
                    raise ControlError(f"Task {task_id} specialist contracts require an exact external tool/resource scope.")
                if not require_capacity:
                    raise ControlError(f"Task {task_id} specialist contracts require configured resource capacity.")
            if execution_class == "fixture":
                if cost != 0:
                    raise BudgetError(f"Task {task_id} fixture execution must have zero reserved cost.")
                if tool_id is not None or resource_id is not None:
                    raise ControlError(f"Task {task_id} fixture execution cannot declare external capabilities.")
                if require_capacity or resource_limit is not None:
                    raise ControlError(f"Task {task_id} fixture execution cannot require resource capacity.")
            else:
                if (tool_id is None) != (resource_id is None):
                    raise ControlError(f"Task {task_id} must declare both tool and resource or neither.")
                if tool_id is not None:
                    tool_id = _identifier(tool_id, f"task {task_id} tool")
                    resource_id = _identifier(resource_id, f"task {task_id} resource")
            if require_capacity and (execution_class == "fixture" or resource_id is None):
                raise ControlError(f"Task {task_id} requires exact nonfixture tool and resource capacity scope.")
            if resource_limit is not None:
                previous_limit = resource_limits.setdefault(resource_id, resource_limit)
                if previous_limit != resource_limit:
                    raise ControlError(f"Tasks using resource {resource_id!r} must declare the same per-run concurrency limit.")
            attempts = row.get("maxAttempts", 1)
            if type(attempts) is not int or not 1 <= attempts <= MAX_ATTEMPTS:
                raise ControlError(f"Task {task_id} maxAttempts must be from 1 to {MAX_ATTEMPTS}.")
            payload = _json(row.get("payload", {}), maximum=MAX_RESULT_BYTES, label=f"task {task_id} payload")
            _reject_secret_fields(json.loads(payload))
            reservation += cost
            if reservation > 2**63 - 1:
                raise BudgetError("Combined task reservations exceed the supported integer range.")
            task_ids.add(task_id)
            normalized_task = {"id": task_id, "agentId": agent_id, "dependencies": deps,
                               "payloadJson": payload, "reservedCostMicrousd": cost,
                               "maxAttempts": attempts, "executionClass": execution_class,
                               "toolId": tool_id, "resourceId": resource_id,
                               "requireResourceCapacity": require_capacity,
                               "resourceConcurrencyLimit": resource_limit,
                               "specialistContractId": specialist_contract_id}
            tasks.append(normalized_task)
            if resource_id is not None:
                resource_tasks.setdefault(resource_id, []).append(normalized_task)
        for resource_id, limit in resource_limits.items():
            if any(task["resourceConcurrencyLimit"] != limit or not task["requireResourceCapacity"]
                   for task in resource_tasks[resource_id]):
                raise ControlError(f"All tasks using resource {resource_id!r} must opt in and declare the same per-run concurrency limit.")
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
                                       "executionClass": t["executionClass"],
                                       **({"tool": t["toolId"], "resource": t["resourceId"]} if t["toolId"] is not None else {}),
                                       **({"requireResourceCapacity": True} if t["requireResourceCapacity"] else {}),
                                       **({"resourceConcurrencyLimit": t["resourceConcurrencyLimit"]} if t["resourceConcurrencyLimit"] is not None else {}),
                                       **({"specialistContractId": t["specialistContractId"]} if t["specialistContractId"] is not None else {})} for t in tasks), key=lambda t: t["id"])}
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
            if ambiguous:
                self._settle_execution_attempt(db, task_id=task["task_id"], attempt=task["attempts"], outcome="unknown",
                                               actual_cost_microusd=None, settled_at=now,
                                               receipt_json=_json({"outcome": "unknown", "reason": "lease_expired"}, maximum=MAX_EVENT_BYTES, label="receipt"))
            else:
                self._settle_execution_attempt(db, task_id=task["task_id"], attempt=task["attempts"], outcome="expired_retryable",
                                               actual_cost_microusd=0, settled_at=now,
                                               receipt_json=_json({"outcome": "expired_retryable", "actualCostMicrousd": 0}, maximum=MAX_EVENT_BYTES, label="receipt"))
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
                "agents": agents, "tasks": tasks, "events": events,
                "ledger": self._ledger_view(db, run_id, 100)}

    def _task(self, db: sqlite3.Connection, task_id: str, *, include_token: bool = False) -> dict[str, Any]:
        row = db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        dependencies = [item[0] for item in db.execute("SELECT dependency_key FROM dependencies WHERE run_id=? AND task_key=? ORDER BY dependency_key", (row["run_id"], row["task_key"]))]
        checkpoint_rows = db.execute("SELECT checkpoint_id,value_sha256,byte_length,created_at "
                                     "FROM worker_checkpoints WHERE task_id=? AND attempt_number=? "
                                     "ORDER BY created_at LIMIT ?",
                                     (task_id, row["attempts"], MAX_CHECKPOINTS_PER_ATTEMPT)).fetchall()
        capacity = None
        if row["resource_id"] is not None:
            configured = db.execute("SELECT max_concurrency FROM resource_capacities WHERE resource_id=?",
                                    (row["resource_id"],)).fetchone()
            global_occupied = self._resource_occupancy(db, row["resource_id"])
            run_occupied = self._resource_occupancy(db, row["resource_id"], run_id=row["run_id"])
            run_limit = row["resource_concurrency_limit"]
            global_limit = configured[0] if configured else None
            limits = [limit for limit in (global_limit, run_limit) if limit is not None]
            effective_limit = min(limits) if limits else None
            available = [max(0, global_limit - global_occupied) if global_limit is not None else None,
                         max(0, run_limit - run_occupied) if run_limit is not None else None]
            available = [value for value in available if value is not None]
            capacity = {"globalLimit": global_limit, "globalOccupied": global_occupied,
                        "runOccupied": run_occupied, "runLimit": run_limit,
                        "effectiveLimit": effective_limit,
                        "availableCount": min(available) if available else None}
        task = {"taskId": row["task_id"], "id": row["task_key"], "agentId": row["agent_id"],
                "status": row["status"], "dependencies": dependencies, "payload": json.loads(row["payload_json"]),
                "attempts": row["attempts"], "maxAttempts": row["max_attempts"],
                "executionClass": row["execution_class"], "tool": row["tool_id"], "resource": row["resource_id"],
                "requireResourceCapacity": bool(row["require_resource_capacity"]),
                "resourceConcurrencyLimit": row["resource_concurrency_limit"],
                "specialistContractId": row["specialist_contract_id"],
                "resourceCapacity": capacity,
                "reservedCostMicrousd": row["reserved_cost_microusd"],
                "actualCostMicrousd": row["actual_cost_microusd"], "workerId": row["worker_id"],
                "leaseExpiresAt": row["lease_expires_at"], "claimedAt": row["claimed_at"],
                "completedAt": row["completed_at"], "result": json.loads(row["result_json"]) if row["result_json"] is not None else None,
                "checkpoints": [{"checkpointId": cp["checkpoint_id"], "sha256": cp["value_sha256"],
                                 "byteLength": cp["byte_length"], "createdAt": cp["created_at"]}
                                for cp in checkpoint_rows],
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
        if action == "grantAccess":
            return store.grant_access(principal_id=request.get("principalId"),
                                      tool_id=request.get("tool"), resource_id=request.get("resource"),
                                      max_budget_microusd=request.get("maxBudgetMicrousd"),
                                      expires_at=request.get("expiresAt"))
        if action == "revokeAccess":
            return {"revoked": store.revoke_access(request.get("grantId"))}
        if action == "configureResourceCapacity":
            return store.configure_resource_capacity(request.get("resourceId"), request.get("maxConcurrency"))
        if action == "resourceCapacities":
            return store.resource_capacity_status(limit=request.get("limit", 1000))
        if action == "configureSpecialistApprovers":
            return store.configure_specialist_approvers(request.get("principalIds"))
        if action == "createSpecialistContract":
            return store.create_specialist_contract(idempotency_key=request.get("idempotencyKey"),
                                                    design=request.get("design"),
                                                    assignment=request.get("assignment"))
        if action == "approveSpecialistContract":
            return store.approve_specialist_contract(request.get("contractId"),
                                                     request.get("workerId"),
                                                     request.get("credential"))
        if action == "activateSpecialistContract":
            return store.activate_specialist_contract(request.get("contractId"))
        if action == "revokeSpecialistContract":
            return {"revoked": store.revoke_specialist_contract(request.get("contractId"))}
        if action == "specialistContractStatus":
            return store.specialist_contract_status(request.get("contractId"))
        if action == "bindSpecialistContract":
            return store.bind_specialist_contract(contract_id=request.get("contractId"),
                                                  plan=request.get("plan"),
                                                  task_id=request.get("taskId"))
        if action == "ledger":
            return store.ledger(request.get("runId"), limit=request.get("limit", 1000))
        if action == "status":
            result = store.status(request.get("runId"))
            if result is None:
                raise ControlError("Run not found.")
            return result
        if action == "enrollWorker":
            return store.enroll_worker(worker_id=request.get("workerId"),
                                       principal_id=request.get("principalId"),
                                       expires_at=request.get("expiresAt"))
        if action == "revokeWorker":
            return {"revoked": store.revoke_worker(request.get("workerId"))}
        if action == "authClaim":
            return {"task": store.claim_authenticated(request.get("runId"), request.get("workerId"),
                                                       request.get("credential"),
                                                       lease_seconds=request.get("leaseSeconds", 30),
                                                       agent_id=request.get("agentId"),
                                                       task_id=request.get("taskId"))}
        if action == "authHeartbeat":
            return {"task": store.heartbeat_authenticated(request.get("taskId"), request.get("leaseToken"),
                                                           request.get("credential"),
                                                           lease_seconds=request.get("leaseSeconds", 30))}
        if action == "authComplete":
            return store.complete_authenticated(request.get("taskId"), request.get("leaseToken"),
                                                request.get("credential"), request.get("result"),
                                                request.get("actualCostMicrousd"))
        if action == "authFail":
            return store.fail_authenticated(request.get("taskId"), request.get("leaseToken"),
                                            request.get("credential"), request.get("error"),
                                            retryable=request.get("retryable", False),
                                            actual_cost_microusd=request.get("actualCostMicrousd"))
        if action == "authCheckpoint":
            return store.checkpoint_authenticated(request.get("taskId"), request.get("leaseToken"),
                                                  request.get("credential"), request.get("checkpointId"),
                                                  request.get("value"))
        if action == "checkpoints":
            return store.read_checkpoints(request.get("taskId"), attempt=request.get("attempt"),
                                          limit=request.get("limit", MAX_CHECKPOINTS_PER_ATTEMPT))
        if action in {"claim", "heartbeat", "complete", "fail"}:
            raise ControlError("Use authenticated authClaim/authHeartbeat/authComplete/authFail CLI actions.")
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
