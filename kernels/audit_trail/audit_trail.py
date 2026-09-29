"""Cryptographic audit trail with hash chaining and tamper-evident logging.

Zero-dependency Python 3.10+ implementation. Each entry is linked to its
predecessor via SHA-256, forming a tamper-evident chain. Any modification,
deletion, or reordering of historical entries is detectable by verify().

Evidence vault integration allows storing arbitrary artifacts (results,
receipts, checkpoints) with their content hashes recorded in the chain.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator


# ── Exceptions ───────────────────────────────────────────────────────────────


class AuditTrailError(ValueError):
    """Base exception for audit trail operations."""


class ChainBrokenError(AuditTrailError):
    """The hash chain is broken at the given sequence number."""

    def __init__(self, sequence: int, expected: str, actual: str):
        self.sequence = sequence
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Chain broken at sequence {sequence}: expected {expected[:16]}…, got {actual[:16]}…"
        )


class EntryNotFoundError(AuditTrailError):
    """No entry exists at the given sequence number."""


class EvidenceNotFoundError(AuditTrailError):
    """No evidence artifact exists with the given ID."""


# ── Data model ───────────────────────────────────────────────────────────────


GENESIS_HASH = "0" * 64


@dataclass(frozen=True)
class AuditEntry:
    """A single immutable entry in the audit chain."""

    sequence: int
    timestamp: float
    event_type: str
    payload: dict[str, Any]
    previous_hash: str
    entry_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "payload": self.payload,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditEntry:
        return cls(
            sequence=data["sequence"],
            timestamp=data["timestamp"],
            event_type=data["event_type"],
            payload=data["payload"],
            previous_hash=data["previous_hash"],
            entry_hash=data["entry_hash"],
        )


@dataclass(frozen=True)
class EvidenceRecord:
    """A stored evidence artifact with its content hash."""

    evidence_id: str
    content_hash: str
    byte_length: int
    media_type: str
    created_at: float
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Hash utilities ───────────────────────────────────────────────────────────


def _canonical_json(value: Any) -> str:
    """Deterministic JSON encoding for hashing."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def compute_hash(sequence: int, timestamp: float, event_type: str,
                 payload: dict[str, Any], previous_hash: str) -> str:
    """Compute the SHA-256 hash for a chain entry."""
    data = {
        "sequence": sequence,
        "timestamp": timestamp,
        "event_type": event_type,
        "payload": payload,
        "previous_hash": previous_hash,
    }
    return hashlib.sha256(_canonical_json(data).encode("utf-8")).hexdigest()


def compute_content_hash(content: bytes) -> str:
    """Compute the SHA-256 hash of evidence content."""
    return hashlib.sha256(content).hexdigest()


# ── Audit trail ──────────────────────────────────────────────────────────────


class AuditTrail:
    """Tamper-evident, hash-chained audit log backed by SQLite.

    Each entry's hash depends on its content and the previous entry's hash,
    forming a cryptographic chain. verify() detects any tampering.
    """

    def __init__(self, db_path: str | os.PathLike[str], *, clock=time.time):
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

    def _initialize(self) -> None:
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS audit_chain (
                sequence INTEGER PRIMARY KEY,
                timestamp REAL NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                entry_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS evidence_vault (
                evidence_id TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL,
                byte_length INTEGER NOT NULL,
                media_type TEXT NOT NULL,
                created_at REAL NOT NULL,
                metadata_json TEXT NOT NULL,
                content BLOB
            );
            CREATE INDEX IF NOT EXISTS evidence_hash ON evidence_vault(content_hash);
        """)

    def append(self, event_type: str, payload: dict[str, Any]) -> AuditEntry:
        """Append a new entry to the chain. Returns the created entry."""
        with self._lock:
            now = self._now()
            previous = self._db.execute(
                "SELECT entry_hash FROM audit_chain ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
            previous_hash = previous["entry_hash"] if previous else GENESIS_HASH
            sequence = (self._db.execute(
                "SELECT COALESCE(MAX(sequence),0) + 1 FROM audit_chain"
            ).fetchone()[0])
            entry_hash = compute_hash(sequence, now, event_type, payload, previous_hash)
            encoded = _canonical_json(payload)
            self._db.execute(
                "INSERT INTO audit_chain(sequence,timestamp,event_type,payload_json,"
                "previous_hash,entry_hash) VALUES(?,?,?,?,?,?)",
                (sequence, now, event_type, encoded, previous_hash, entry_hash),
            )
            return AuditEntry(
                sequence=sequence,
                timestamp=now,
                event_type=event_type,
                payload=payload,
                previous_hash=previous_hash,
                entry_hash=entry_hash,
            )

    def get(self, sequence: int) -> AuditEntry:
        """Retrieve a single entry by sequence number."""
        row = self._db.execute(
            "SELECT * FROM audit_chain WHERE sequence=?", (sequence,)
        ).fetchone()
        if row is None:
            raise EntryNotFoundError(f"No entry at sequence {sequence}.")
        return AuditEntry(
            sequence=row["sequence"],
            timestamp=row["timestamp"],
            event_type=row["event_type"],
            payload=json.loads(row["payload_json"]),
            previous_hash=row["previous_hash"],
            entry_hash=row["entry_hash"],
        )

    def entries(self, *, start: int = 1, limit: int | None = None) -> list[AuditEntry]:
        """Retrieve entries in order, optionally from a starting sequence."""
        query = "SELECT * FROM audit_chain WHERE sequence>=? ORDER BY sequence"
        params: list[Any] = [start]
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative.")
            query += " LIMIT ?"
            params.append(limit)
        rows = self._db.execute(query, params).fetchall()
        return [
            AuditEntry(
                sequence=r["sequence"],
                timestamp=r["timestamp"],
                event_type=r["event_type"],
                payload=json.loads(r["payload_json"]),
                previous_hash=r["previous_hash"],
                entry_hash=r["entry_hash"],
            )
            for r in rows
        ]

    def verify(self) -> tuple[bool, int | None]:
        """Verify the entire chain. Returns (is_valid, broken_at_sequence).

        If valid, broken_at_sequence is None. If broken, it is the sequence
        number where the chain first fails verification.
        """
        previous_hash = GENESIS_HASH
        expected_sequence = 1
        for row in self._db.execute(
            "SELECT * FROM audit_chain ORDER BY sequence"
        ).fetchall():
            if row["sequence"] != expected_sequence:
                return False, expected_sequence
            entry_hash = compute_hash(
                row["sequence"],
                row["timestamp"],
                row["event_type"],
                json.loads(row["payload_json"]),
                row["previous_hash"],
            )
            if row["previous_hash"] != previous_hash:
                return False, row["sequence"]
            if row["entry_hash"] != entry_hash:
                return False, row["sequence"]
            previous_hash = row["entry_hash"]
            expected_sequence += 1
        return True, None

    def verify_up_to(self, sequence: int) -> tuple[bool, int | None]:
        """Verify the chain up to and including the given sequence."""
        previous_hash = GENESIS_HASH
        for row in self._db.execute(
            "SELECT * FROM audit_chain WHERE sequence<=? ORDER BY sequence",
            (sequence,),
        ).fetchall():
            entry_hash = compute_hash(
                row["sequence"],
                row["timestamp"],
                row["event_type"],
                json.loads(row["payload_json"]),
                row["previous_hash"],
            )
            if row["previous_hash"] != previous_hash:
                return False, row["sequence"]
            if row["entry_hash"] != entry_hash:
                return False, row["sequence"]
            previous_hash = row["entry_hash"]
        return True, None

    def store_evidence(self, content: bytes, *, media_type: str = "application/octet-stream",
                       metadata: dict[str, Any] | None = None) -> EvidenceRecord:
        """Store an evidence artifact and return its record."""
        with self._lock:
            now = self._now()
            content_hash = compute_content_hash(content)
            evidence_id = hashlib.sha256(
                f"{content_hash}:{now}".encode("utf-8")
            ).hexdigest()[:32]
            meta = metadata or {}
            self._db.execute(
                "INSERT INTO evidence_vault(evidence_id,content_hash,byte_length,"
                "media_type,created_at,metadata_json,content) VALUES(?,?,?,?,?,?,?)",
                (evidence_id, content_hash, len(content), media_type, now,
                 _canonical_json(meta), content),
            )
            return EvidenceRecord(
                evidence_id=evidence_id,
                content_hash=content_hash,
                byte_length=len(content),
                media_type=media_type,
                created_at=now,
                metadata=meta,
            )

    def get_evidence(self, evidence_id: str) -> tuple[EvidenceRecord, bytes]:
        """Retrieve an evidence artifact and its content."""
        row = self._db.execute(
            "SELECT * FROM evidence_vault WHERE evidence_id=?", (evidence_id,)
        ).fetchone()
        if row is None:
            raise EvidenceNotFoundError(f"No evidence with ID {evidence_id}.")
        record = EvidenceRecord(
            evidence_id=row["evidence_id"],
            content_hash=row["content_hash"],
            byte_length=row["byte_length"],
            media_type=row["media_type"],
            created_at=row["created_at"],
            metadata=json.loads(row["metadata_json"]),
        )
        return record, row["content"]

    def verify_evidence(self, evidence_id: str) -> bool:
        """Verify that stored evidence matches its recorded hash."""
        try:
            record, content = self.get_evidence(evidence_id)
        except EvidenceNotFoundError:
            return False
        return compute_content_hash(content) == record.content_hash

    def link_evidence(self, event_type: str, payload: dict[str, Any],
                      evidence_id: str) -> AuditEntry:
        """Append an entry that references a stored evidence artifact."""
        if not self.verify_evidence(evidence_id):
            raise AuditTrailError(f"Evidence {evidence_id} failed verification.")
        enriched = {**payload, "evidenceId": evidence_id}
        return self.append(event_type, enriched)

    def summary(self) -> dict[str, Any]:
        """Return a summary of the audit trail state."""
        count = self._db.execute(
            "SELECT COUNT(*) FROM audit_chain"
        ).fetchone()[0]
        evidence_count = self._db.execute(
            "SELECT COUNT(*) FROM evidence_vault"
        ).fetchone()[0]
        valid, broken_at = self.verify()
        return {
            "entryCount": count,
            "evidenceCount": evidence_count,
            "isValid": valid,
            "brokenAt": broken_at,
        }

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> AuditTrail:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _now(self) -> float:
        value = float(self._clock())
        if value < 0:
            raise AuditTrailError("Clock returned a negative timestamp.")
        return value


# ── Convenience helpers ──────────────────────────────────────────────────────


def create_trail(db_path: str | os.PathLike[str], *, clock=time.time) -> AuditTrail:
    """Create or open an audit trail at the given path."""
    return AuditTrail(db_path, clock=clock)


# ── Tests ────────────────────────────────────────────────────────────────────


def test_genesis_and_append():
    trail = AuditTrail(":memory:")
    entry = trail.append("test.event", {"key": "value"})
    assert entry.sequence == 1
    assert entry.previous_hash == GENESIS_HASH
    assert len(entry.entry_hash) == 64
    valid, broken = trail.verify()
    assert valid and broken is None
    trail.close()


def test_chain_linking():
    trail = AuditTrail(":memory:")
    e1 = trail.append("first", {"n": 1})
    e2 = trail.append("second", {"n": 2})
    assert e2.previous_hash == e1.entry_hash
    assert e1.sequence == 1 and e2.sequence == 2
    trail.close()


def test_tamper_detection():
    trail = AuditTrail(":memory:")
    trail.append("event", {"data": "original"})
    # Tamper with the payload directly in the DB
    trail._db.execute(
        "UPDATE audit_chain SET payload_json='{\"data\":\"tampered\"}' WHERE sequence=1"
    )
    valid, broken = trail.verify()
    assert not valid
    assert broken == 1
    trail.close()


def test_tamper_detection_hash_modification():
    trail = AuditTrail(":memory:")
    trail.append("event", {"data": "original"})
    # Tamper with the hash directly
    trail._db.execute(
        "UPDATE audit_chain SET entry_hash='0'*64 WHERE sequence=1"
    )
    valid, broken = trail.verify()
    assert not valid
    assert broken == 1
    trail.close()


def test_evidence_vault():
    trail = AuditTrail(":memory:")
    content = b"test evidence content"
    record = trail.store_evidence(content, media_type="text/plain",
                                  metadata={"source": "test"})
    assert record.byte_length == len(content)
    assert record.content_hash == compute_content_hash(content)
    retrieved_record, retrieved_content = trail.get_evidence(record.evidence_id)
    assert retrieved_content == content
    assert retrieved_record.content_hash == record.content_hash
    assert trail.verify_evidence(record.evidence_id)
    trail.close()


def test_evidence_tamper_detection():
    trail = AuditTrail(":memory:")
    content = b"original"
    record = trail.store_evidence(content)
    # Tamper with stored content
    trail._db.execute(
        "UPDATE evidence_vault SET content=? WHERE evidence_id=?",
        (b"tampered", record.evidence_id),
    )
    assert not trail.verify_evidence(record.evidence_id)
    trail.close()


def test_link_evidence():
    trail = AuditTrail(":memory:")
    content = b"evidence bytes"
    record = trail.store_evidence(content)
    entry = trail.link_evidence("task.completed", {"taskId": "t1"}, record.evidence_id)
    assert entry.payload["evidenceId"] == record.evidence_id
    assert entry.payload["taskId"] == "t1"
    trail.close()


def test_verify_up_to():
    trail = AuditTrail(":memory:")
    for i in range(5):
        trail.append("event", {"n": i})
    valid, broken = trail.verify_up_to(3)
    assert valid and broken is None
    trail.close()


def test_entry_not_found():
    trail = AuditTrail(":memory:")
    try:
        trail.get(99)
        assert False, "Should have raised"
    except EntryNotFoundError:
        pass
    trail.close()


def test_evidence_not_found():
    trail = AuditTrail(":memory:")
    try:
        trail.get_evidence("nonexistent")
        assert False, "Should have raised"
    except EvidenceNotFoundError:
        pass
    trail.close()


def test_summary():
    trail = AuditTrail(":memory:")
    trail.append("event", {})
    trail.store_evidence(b"data")
    s = trail.summary()
    assert s["entryCount"] == 1
    assert s["evidenceCount"] == 1
    assert s["isValid"] is True
    assert s["brokenAt"] is None
    trail.close()


def test_persistence():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "audit.sqlite3")
        trail = AuditTrail(path)
        trail.append("event", {"key": "value"})
        trail.store_evidence(b"evidence")
        trail.close()

        trail2 = AuditTrail(path)
        valid, _ = trail2.verify()
        assert valid
        assert trail2.summary()["entryCount"] == 1
        assert trail2.summary()["evidenceCount"] == 1
        trail2.close()


def test_concurrent_appends():
    trail = AuditTrail(":memory:")
    entries = []
    for i in range(10):
        entries.append(trail.append("concurrent", {"n": i}))
    assert len(entries) == 10
    valid, _ = trail.verify()
    assert valid
    trail.close()


if __name__ == "__main__":
    test_genesis_and_append()
    test_chain_linking()
    test_tamper_detection()
    test_tamper_detection_hash_modification()
    test_evidence_vault()
    test_evidence_tamper_detection()
    test_link_evidence()
    test_verify_up_to()
    test_entry_not_found()
    test_evidence_not_found()
    test_summary()
    test_persistence()
    test_concurrent_appends()
    print("All tests passed.")
