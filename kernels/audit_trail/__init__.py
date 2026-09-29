"""Cryptographic audit trail kernel."""
from .audit_trail import (
    AuditEntry,
    AuditTrail,
    AuditTrailError,
    ChainBrokenError,
    EntryNotFoundError,
    EvidenceNotFoundError,
    EvidenceRecord,
    compute_content_hash,
    compute_hash,
    create_trail,
)

__all__ = [
    "AuditEntry",
    "AuditTrail",
    "AuditTrailError",
    "ChainBrokenError",
    "EntryNotFoundError",
    "EvidenceNotFoundError",
    "EvidenceRecord",
    "compute_content_hash",
    "compute_hash",
    "create_trail",
]
