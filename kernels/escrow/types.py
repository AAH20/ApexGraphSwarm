"""Core data types for the 3-party escrow system."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AssetType(Enum):
    ETH = "ETH"
    ERC20 = "ERC20"


class EscrowStatus(Enum):
    PENDING = "PENDING"
    FUNDED = "FUNDED"
    IN_PROGRESS = "IN_PROGRESS"
    DELIVERED = "DELIVERED"
    DISPUTED = "DISPUTED"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


class MilestoneStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DELIVERED = "DELIVERED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISPUTED = "DISPUTED"


class DisputeStatus(Enum):
    OPEN = "OPEN"
    EVIDENCE_PERIOD = "EVIDENCE_PERIOD"
    JUDGING = "JUDGING"
    RESOLVED = "RESOLVED"


@dataclass(frozen=True)
class Party:
    """A participant in the escrow (requester, worker, or judge)."""
    address: str
    role: str  # "requester", "worker", "judge"


@dataclass
class Milestone:
    """A single milestone within an escrow contract."""
    index: int
    description: str
    amount: int  # in wei (or smallest token unit)
    status: MilestoneStatus = MilestoneStatus.PENDING
    deliverable_hash: str | None = None
    approved_at: float | None = None


@dataclass
class EscrowState:
    """Full state of an escrow contract."""
    escrow_id: str
    requester: Party
    worker: Party
    judge: Party
    asset_type: AssetType
    token_address: str | None  # None for ETH
    total_amount: int
    milestones: list[Milestone]
    status: EscrowStatus = EscrowStatus.PENDING
    created_at: float = 0.0
    funded_at: float | None = None
    delivered_at: float | None = None
    resolved_at: float | None = None
    dispute: Dispute | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Dispute:
    """A dispute raised against a milestone or the full escrow."""
    dispute_id: str
    escrow_id: str
    milestone_index: int | None  # None = full escrow dispute
    raised_by: str  # address
    reason: str
    status: DisputeStatus = DisputeStatus.OPEN
    evidence: list[dict[str, Any]] = field(default_factory=list)
    resolution: str | None = None
    resolved_at: float | None = None


@dataclass
class Settlement:
    """On-chain settlement record."""
    settlement_id: str
    escrow_id: str
    milestone_index: int | None
    recipient: str
    amount: int
    asset_type: AssetType
    token_address: str | None
    tx_hash: str
    settled_at: float
    block_number: int | None = None
