"""Stable, attributable attempt and settlement receipt helpers."""
from __future__ import annotations

import hashlib


def attempt_id(task_id: str, attempt: int) -> str:
    """Return a deterministic ID stable across retries of the same DB operation."""
    return hashlib.sha256(f"{task_id}:{attempt}".encode("utf-8")).hexdigest()

def record_attempt_start(db, *, task_id: str, run_id: str, attempt: int, worker_id: str,
                         principal_id: str | None, grant_id: str | None, reserved_microusd: int,
                         tool_id: str | None, resource_id: str | None, started_at: float) -> str:
    identifier = attempt_id(task_id, attempt)
    db.execute("""INSERT OR IGNORE INTO execution_attempts
        (attempt_id,task_id,run_id,attempt_number,worker_id,principal_id,grant_id,tool_id,resource_id,
         reserved_microusd,started_at,outcome,actual_cost_microusd)
         VALUES(?,?,?,?,?,?,?,?,?,?,?,'running',NULL)""",
        (identifier, task_id, run_id, attempt, worker_id, principal_id, grant_id,
         tool_id, resource_id, reserved_microusd, started_at))
    return identifier

def settle_attempt(db, *, task_id: str, attempt: int, outcome: str,
                   actual_cost_microusd: int | None, settled_at: float, receipt_json: str | None) -> None:
    identifier = attempt_id(task_id, attempt)
    row = db.execute("SELECT outcome,actual_cost_microusd FROM execution_attempts WHERE attempt_id=?", (identifier,)).fetchone()
    if row is None:
        return
    if row["outcome"] not in {"running", "unknown"}:
        # Idempotent replay is accepted only for equivalent settlement.
        if row["outcome"] == outcome and row["actual_cost_microusd"] == actual_cost_microusd:
            return
        raise ValueError("Attempt already has a different settlement receipt.")
    db.execute("""UPDATE execution_attempts SET outcome=?,actual_cost_microusd=?,
        settled_at=?,receipt_json=? WHERE attempt_id=? AND outcome IN ('running','unknown')""",
        (outcome, actual_cost_microusd, settled_at, receipt_json, identifier))
