"""Persistent local worker enrollment and token verification primitives."""
from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3


class WorkerIdentityError(PermissionError):
    """Worker credential is missing, invalid, revoked, or expired."""


def initialize_identity_schema(db: sqlite3.Connection) -> None:
    db.executescript("""
        CREATE TABLE IF NOT EXISTS workers (
            worker_id TEXT PRIMARY KEY,
            principal_id TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            expires_at REAL NOT NULL,
            revoked_at REAL,
            created_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS workers_expiry ON workers(expires_at, revoked_at);
    """)


def issue_credential() -> str:
    """Mint a high-entropy opaque token. Callers must return it only once."""
    return secrets.token_urlsafe(32)


def token_digest(credential: str) -> str:
    return hashlib.sha256(credential.encode("utf-8")).hexdigest()


def verify_credential(db: sqlite3.Connection, *, worker_id: str,
                      credential: str | None, now: float):
    """Return active worker row after constant-time hash comparison."""
    if not isinstance(credential, str) or not 32 <= len(credential) <= 512:
        raise WorkerIdentityError("Worker authentication failed.")
    row = db.execute("SELECT * FROM workers WHERE worker_id=?", (worker_id,)).fetchone()
    candidate = token_digest(credential)
    if row is None:
        # Still compare fixed-length digests on the absent-identity path.
        hmac.compare_digest(candidate, "0" * 64)
        raise WorkerIdentityError("Worker authentication failed.")
    matched = hmac.compare_digest(candidate, row["token_hash"])
    if not matched or row["revoked_at"] is not None or row["expires_at"] <= now:
        raise WorkerIdentityError("Worker authentication failed.")
    return row
