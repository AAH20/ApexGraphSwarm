"""Crash-safe, fail-closed idempotency registry for integration HTTP requests.

Only precomputed SHA-256 digests and a stable runtime job UUID are persisted.
This registry suppresses duplicate dispatch; it is not a durable job runner and
cannot safely resume an interrupted in-memory integration after a restart.
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import uuid
from pathlib import Path
from typing import Any

MAX_REQUEST_RECORDS = 100_000
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class RequestRegistryError(ValueError):
    """The request cannot be safely registered or deduplicated."""


class RequestConflictError(RequestRegistryError):
    """A scoped idempotency key was already used with another payload."""


def _digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise RequestRegistryError(f"{label} must be a lowercase SHA-256 digest.")
    return value


def _job_id(value: Any) -> str:
    if not isinstance(value, str):
        raise RequestRegistryError("candidate_job_id must be a UUID.")
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError):
        raise RequestRegistryError("candidate_job_id must be a UUID.") from None
    canonical = str(parsed)
    if canonical != value.lower():
        raise RequestRegistryError("candidate_job_id must be a canonical UUID.")
    return canonical


def register_hashed_request(db_path: str | Path, *, request_key_hash: str,
                            scope_hash: str, payload_digest: str,
                            candidate_job_id: str) -> dict[str, Any]:
    """Atomically create or look up a scoped request entry.

    Callers must hash the raw key, authenticated scope, and canonical request
    JSON before passing them here. No raw values are accepted or stored.
    """
    key_hash = _digest(request_key_hash, "request_key_hash")
    scope = _digest(scope_hash, "scope_hash")
    payload = _digest(payload_digest, "payload_digest")
    job = _job_id(candidate_job_id)
    path = Path(db_path)
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    connection = sqlite3.connect(str(path), timeout=15, isolation_level=None)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA busy_timeout=15000")
        connection.execute("""CREATE TABLE IF NOT EXISTS integration_request_registry (
            scope_hash TEXT NOT NULL CHECK(length(scope_hash)=64),
            request_key_hash TEXT NOT NULL CHECK(length(request_key_hash)=64),
            payload_digest TEXT NOT NULL CHECK(length(payload_digest)=64),
            job_id TEXT NOT NULL UNIQUE,
            PRIMARY KEY(scope_hash,request_key_hash)
        ) WITHOUT ROWID""")
        connection.execute("BEGIN IMMEDIATE")
        prior = connection.execute("SELECT payload_digest,job_id FROM integration_request_registry "
                                   "WHERE scope_hash=? AND request_key_hash=?",
                                   (scope, key_hash)).fetchone()
        if prior:
            if prior["payload_digest"] != payload:
                raise RequestConflictError("Idempotency-Key was already used for a different integration request.")
            connection.execute("COMMIT")
            return {"created": False, "jobId": prior["job_id"]}
        count = connection.execute("SELECT COUNT(*) FROM integration_request_registry").fetchone()[0]
        if count >= MAX_REQUEST_RECORDS:
            raise RequestRegistryError("Durable integration request registry is full; refusing new dispatches.")
        connection.execute("INSERT INTO integration_request_registry "
                           "(scope_hash,request_key_hash,payload_digest,job_id) VALUES(?,?,?,?)",
                           (scope, key_hash, payload, job))
        connection.execute("COMMIT")
        return {"created": True, "jobId": job}
    except Exception:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()


def lookup_durable_run_id(db_path: str | Path, job_id: str) -> str | None:
    """Read an existing durable control run for a registered runtime job."""
    job = _job_id(job_id)
    path = Path(db_path)
    if not path.is_file():
        return None
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5)
    try:
        exists = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='runs'").fetchone()
        if not exists:
            return None
        row = connection.execute("SELECT id FROM runs WHERE idempotency_key=?",
                                 (f"integration-{job}",)).fetchone()
        return row[0] if row else None
    finally:
        connection.close()


def _cli_request(request: Any) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise RequestRegistryError("Unsupported request registry action.")
    if request.get("action") == "lookupRun":
        return {"runId": lookup_durable_run_id(request.get("dbPath"), request.get("jobId"))}
    if request.get("action") != "register":
        raise RequestRegistryError("Unsupported request registry action.")
    return register_hashed_request(
        request.get("dbPath"),
        request_key_hash=request.get("requestKeyHash"),
        scope_hash=request.get("scopeHash"),
        payload_digest=request.get("payloadDigest"),
        candidate_job_id=request.get("candidateJobId"),
    )


def main() -> int:
    try:
        request = json.load(sys.stdin)
        result = _cli_request(request)
        sys.stdout.write(json.dumps({"data": result}, separators=(",", ":")))
        return 0
    except (RequestRegistryError, sqlite3.Error, OSError, TypeError) as exc:
        sys.stdout.write(json.dumps({"error": str(exc)}, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
