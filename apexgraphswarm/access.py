"""Exact capability checks for the trusted local scheduler boundary.

This module provides policy bookkeeping primitives; it does not authenticate
principals or isolate code executed by an external harness.
"""
from __future__ import annotations

import sqlite3
import uuid


class AccessDenied(PermissionError):
    """No unrevoked, unexpired exact capability covers this dispatch."""


def initialize_access_schema(db: sqlite3.Connection) -> None:
    db.executescript("""
        CREATE TABLE IF NOT EXISTS access_grants (
            grant_id TEXT PRIMARY KEY, principal_id TEXT NOT NULL, tool_id TEXT NOT NULL,
            resource_id TEXT NOT NULL, max_budget_microusd INTEGER NOT NULL,
            expires_at REAL NOT NULL, revoked_at REAL, created_at REAL NOT NULL,
            spent_microusd INTEGER NOT NULL DEFAULT 0,
            reserved_microusd INTEGER NOT NULL DEFAULT 0,
            UNIQUE(principal_id, tool_id, resource_id, grant_id)
        );
        CREATE INDEX IF NOT EXISTS access_grants_lookup
            ON access_grants(principal_id, tool_id, resource_id, expires_at, revoked_at);
    """)
    columns = {row[1] for row in db.execute("PRAGMA table_info(access_grants)")}
    if "spent_microusd" not in columns:
        db.execute("ALTER TABLE access_grants ADD COLUMN spent_microusd INTEGER NOT NULL DEFAULT 0")
    if "reserved_microusd" not in columns:
        db.execute("ALTER TABLE access_grants ADD COLUMN reserved_microusd INTEGER NOT NULL DEFAULT 0")

def authorize(db: sqlite3.Connection, *, principal_id: str | None, tool_id: str,
              resource_id: str, budget_microusd: int, now: float) -> str:
    """Authorize exact tuple; caller must run this in dispatch transaction."""
    if principal_id is None:
        raise AccessDenied("A principal is required for capability-scoped dispatch.")
    rows = db.execute(
        "SELECT grant_id,max_budget_microusd,spent_microusd,reserved_microusd FROM access_grants "
        "WHERE principal_id=? AND tool_id=? AND resource_id=? AND expires_at>? "
        "AND revoked_at IS NULL ORDER BY created_at DESC",
        (principal_id, tool_id, resource_id, now),
    ).fetchall()
    for row in rows:
        if row["spent_microusd"] + row["reserved_microusd"] + budget_microusd <= row["max_budget_microusd"]:
            return row["grant_id"]
    raise AccessDenied("No active exact capability covers this dispatch budget.")

def new_grant_id() -> str:
    return str(uuid.uuid4())
