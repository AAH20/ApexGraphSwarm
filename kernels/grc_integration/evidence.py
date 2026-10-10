"""Evidence collection primitives for GRC compliance.

Provides tamper-evident evidence records with SHA-256 integrity verification.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


class EvidenceError(ValueError):
    """Base error for evidence operations."""


class EvidenceNotFoundError(EvidenceError):
    """Evidence record does not exist."""


class EvidenceIntegrityError(EvidenceError):
    """Evidence integrity verification failed."""


@dataclass
class Evidence:
    """A single piece of compliance evidence.

    Attributes:
        evidence_id: Unique identifier for this evidence record.
        control_id: The control this evidence supports.
        framework: The compliance framework (e.g., "ISO42001", "SOC2").
        description: Human-readable description of the evidence.
        collected_at: Unix timestamp when evidence was collected.
        collector_id: Identifier of the entity that collected the evidence.
        data: Arbitrary JSON-serializable evidence data.
        sha256: SHA-256 hash of the canonical evidence data.
    """

    evidence_id: str
    control_id: str
    framework: str
    description: str
    collected_at: float
    collector_id: str
    data: dict[str, Any]
    sha256: str = ""

    def __post_init__(self) -> None:
        if not self.sha256:
            self.sha256 = self._compute_hash()

    def _compute_hash(self) -> str:
        canonical = json.dumps(
            {
                "evidence_id": self.evidence_id,
                "control_id": self.control_id,
                "framework": self.framework,
                "description": self.description,
                "collected_at": self.collected_at,
                "collector_id": self.collector_id,
                "data": self.data,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def verify(self) -> bool:
        """Verify evidence integrity by recomputing the hash."""
        return self.sha256 == self._compute_hash()

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidenceId": self.evidence_id,
            "controlId": self.control_id,
            "framework": self.framework,
            "description": self.description,
            "collectedAt": self.collected_at,
            "collectorId": self.collector_id,
            "data": self.data,
            "sha256": self.sha256,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Evidence:
        return cls(
            evidence_id=d["evidenceId"],
            control_id=d["controlId"],
            framework=d["framework"],
            description=d["description"],
            collected_at=d["collectedAt"],
            collector_id=d["collectorId"],
            data=d["data"],
            sha256=d.get("sha256", ""),
        )


class EvidenceStore:
    """In-memory evidence store with integrity verification."""

    def __init__(self) -> None:
        self._evidence: dict[str, Evidence] = {}

    def add(self, evidence: Evidence) -> Evidence:
        """Add evidence to the store. Returns the stored evidence."""
        if not evidence.verify():
            raise EvidenceIntegrityError(
                f"Evidence {evidence.evidence_id} failed integrity check."
            )
        self._evidence[evidence.evidence_id] = evidence
        return evidence

    def get(self, evidence_id: str) -> Evidence:
        """Retrieve evidence by ID."""
        if evidence_id not in self._evidence:
            raise EvidenceNotFoundError(
                f"Evidence {evidence_id} not found."
            )
        return self._evidence[evidence_id]

    def list_by_control(self, control_id: str) -> list[Evidence]:
        """List all evidence for a given control."""
        return [e for e in self._evidence.values() if e.control_id == control_id]

    def list_by_framework(self, framework: str) -> list[Evidence]:
        """List all evidence for a given framework."""
        return [e for e in self._evidence.values() if e.framework == framework]

    def verify_all(self) -> dict[str, bool]:
        """Verify integrity of all stored evidence."""
        return {eid: e.verify() for eid, e in self._evidence.items()}

    def create(
        self,
        *,
        control_id: str,
        framework: str,
        description: str,
        collector_id: str,
        data: dict[str, Any],
        collected_at: float | None = None,
    ) -> Evidence:
        """Create and store a new evidence record."""
        evidence = Evidence(
            evidence_id=str(uuid.uuid4()),
            control_id=control_id,
            framework=framework,
            description=description,
            collected_at=collected_at if collected_at is not None else time.time(),
            collector_id=collector_id,
            data=data,
        )
        return self.add(evidence)

    def __len__(self) -> int:
        return len(self._evidence)
