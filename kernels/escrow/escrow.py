"""Escrow contract logic: funding, milestone delivery, approval, and dispute flow."""
from __future__ import annotations

import hashlib
import secrets
import time
from typing import Any

from .types import (
    AssetType,
    Dispute,
    DisputeStatus,
    EscrowState,
    EscrowStatus,
    Milestone,
    MilestoneStatus,
    Party,
)


class EscrowError(ValueError):
    """Invalid escrow operation."""


class EscrowContract:
    """Manages the lifecycle of a 3-party escrow.

    States: PENDING → FUNDED → IN_PROGRESS → DELIVERED → RESOLVED
                    ↘ CANCELLED        ↘ DISPUTED → RESOLVED
    """

    def __init__(self, clock=time.time):
        self._clock = clock
        self._escrows: dict[str, EscrowState] = {}
        self._disputes: dict[str, Dispute] = {}

    # ── Creation ──────────────────────────────────────────────────────────

    def create_escrow(
        self,
        *,
        requester_address: str,
        worker_address: str,
        judge_address: str,
        asset_type: AssetType,
        total_amount: int,
        milestones: list[dict[str, Any]],
        token_address: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EscrowState:
        """Create a new escrow contract. Does not fund it."""
        if not requester_address or not worker_address or not judge_address:
            raise EscrowError("All three party addresses are required.")
        if requester_address == worker_address:
            raise EscrowError("Requester and worker must be different addresses.")
        if judge_address in (requester_address, worker_address):
            raise EscrowError("Judge must be a neutral third party.")
        if total_amount <= 0:
            raise EscrowError("Total amount must be positive.")
        if not milestones:
            raise EscrowError("At least one milestone is required.")

        milestone_objs: list[Milestone] = []
        allocated = 0
        for i, ms in enumerate(milestones):
            desc = ms.get("description", "")
            amount = ms.get("amount", 0)
            if not desc or not isinstance(desc, str):
                raise EscrowError(f"Milestone {i}: description is required.")
            if not isinstance(amount, int) or amount <= 0:
                raise EscrowError(f"Milestone {i}: amount must be a positive integer.")
            allocated += amount
            milestone_objs.append(Milestone(index=i, description=desc, amount=amount))

        if allocated != total_amount:
            raise EscrowError(
                f"Milestone amounts sum to {allocated}, but total_amount is {total_amount}."
            )

        escrow_id = self._generate_id("escrow")
        state = EscrowState(
            escrow_id=escrow_id,
            requester=Party(requester_address, "requester"),
            worker=Party(worker_address, "worker"),
            judge=Party(judge_address, "judge"),
            asset_type=asset_type,
            token_address=token_address,
            total_amount=total_amount,
            milestones=milestone_objs,
            status=EscrowStatus.PENDING,
            created_at=self._clock(),
            metadata=metadata or {},
        )
        self._escrows[escrow_id] = state
        return state

    # ── Funding ──────────────────────────────────────────────────────────

    def fund(self, escrow_id: str, amount: int) -> EscrowState:
        """Fund the escrow. Transitions PENDING → FUNDED."""
        state = self._get_escrow(escrow_id)
        if state.status != EscrowStatus.PENDING:
            raise EscrowError(f"Cannot fund escrow in {state.status.value} state.")
        if amount != state.total_amount:
            raise EscrowError(
                f"Funding amount {amount} does not match required {state.total_amount}."
            )
        state.status = EscrowStatus.FUNDED
        state.funded_at = self._clock()
        return state

    # ── Milestone lifecycle ──────────────────────────────────────────────

    def start_milestone(self, escrow_id: str, milestone_index: int) -> EscrowState:
        """Worker starts working on a milestone. FUNDED/IN_PROGRESS → IN_PROGRESS."""
        state = self._get_escrow(escrow_id)
        if state.status not in (EscrowStatus.FUNDED, EscrowStatus.IN_PROGRESS):
            raise EscrowError(f"Cannot start milestone in {state.status.value} state.")
        ms = self._get_milestone(state, milestone_index)
        if ms.status != MilestoneStatus.PENDING:
            raise EscrowError(f"Milestone {milestone_index} is not pending.")
        ms.status = MilestoneStatus.IN_PROGRESS
        state.status = EscrowStatus.IN_PROGRESS
        return state

    def deliver_milestone(
        self, escrow_id: str, milestone_index: int, deliverable_hash: str
    ) -> EscrowState:
        """Worker delivers a milestone. IN_PROGRESS → DELIVERED (if all done)."""
        state = self._get_escrow(escrow_id)
        if state.status not in (EscrowStatus.FUNDED, EscrowStatus.IN_PROGRESS):
            raise EscrowError(f"Cannot deliver in {state.status.value} state.")
        ms = self._get_milestone(state, milestone_index)
        if ms.status != MilestoneStatus.IN_PROGRESS:
            raise EscrowError(f"Milestone {milestone_index} is not in progress.")
        if not deliverable_hash or not isinstance(deliverable_hash, str):
            raise EscrowError("Deliverable hash is required.")
        ms.status = MilestoneStatus.DELIVERED
        ms.deliverable_hash = deliverable_hash
        # Check if all milestones are delivered
        if all(m.status == MilestoneStatus.DELIVERED for m in state.milestones):
            state.status = EscrowStatus.DELIVERED
            state.delivered_at = self._clock()
        return state

    def approve_milestone(self, escrow_id: str, milestone_index: int) -> EscrowState:
        """Requester approves a delivered milestone."""
        state = self._get_escrow(escrow_id)
        ms = self._get_milestone(state, milestone_index)
        if ms.status != MilestoneStatus.DELIVERED:
            raise EscrowError(f"Milestone {milestone_index} is not delivered.")
        ms.status = MilestoneStatus.APPROVED
        ms.approved_at = self._clock()
        # Check if all milestones are approved
        if all(m.status == MilestoneStatus.APPROVED for m in state.milestones):
            state.status = EscrowStatus.RESOLVED
            state.resolved_at = self._clock()
        return state

    def reject_milestone(self, escrow_id: str, milestone_index: int, reason: str) -> EscrowState:
        """Requester rejects a delivered milestone."""
        state = self._get_escrow(escrow_id)
        ms = self._get_milestone(state, milestone_index)
        if ms.status != MilestoneStatus.DELIVERED:
            raise EscrowError(f"Milestone {milestone_index} is not delivered.")
        if not reason:
            raise EscrowError("Rejection reason is required.")
        ms.status = MilestoneStatus.REJECTED
        return state

    # ── Dispute resolution ───────────────────────────────────────────────

    def raise_dispute(
        self,
        escrow_id: str,
        milestone_index: int | None,
        raised_by: str,
        reason: str,
    ) -> Dispute:
        """Raise a dispute. Transitions to DISPUTED state."""
        state = self._get_escrow(escrow_id)
        if state.status not in (
            EscrowStatus.FUNDED,
            EscrowStatus.IN_PROGRESS,
            EscrowStatus.DELIVERED,
        ):
            raise EscrowError(f"Cannot dispute in {state.status.value} state.")
        if raised_by not in (state.requester.address, state.worker.address):
            raise EscrowError("Only requester or worker can raise a dispute.")
        if not reason:
            raise EscrowError("Dispute reason is required.")

        dispute_id = self._generate_id("dispute")
        dispute = Dispute(
            dispute_id=dispute_id,
            escrow_id=escrow_id,
            milestone_index=milestone_index,
            raised_by=raised_by,
            reason=reason,
            status=DisputeStatus.OPEN,
        )
        self._disputes[dispute_id] = dispute
        state.dispute = dispute
        state.status = EscrowStatus.DISPUTED

        # Mark the disputed milestone
        if milestone_index is not None:
            ms = self._get_milestone(state, milestone_index)
            ms.status = MilestoneStatus.DISPUTED

        return dispute

    def submit_evidence(
        self, dispute_id: str, submitter: str, evidence: dict[str, Any]
    ) -> Dispute:
        """Submit evidence for a dispute."""
        dispute = self._get_dispute(dispute_id)
        state = self._get_escrow(dispute.escrow_id)
        if submitter not in (state.requester.address, state.worker.address):
            raise EscrowError("Only parties can submit evidence.")
        if dispute.status not in (DisputeStatus.OPEN, DisputeStatus.EVIDENCE_PERIOD):
            raise EscrowError(f"Cannot submit evidence in {dispute.status.value} state.")
        if not evidence or not isinstance(evidence, dict):
            raise EscrowError("Evidence must be a non-empty object.")
        evidence["submitter"] = submitter
        evidence["submitted_at"] = self._clock()
        dispute.evidence.append(evidence)
        return dispute

    def start_judging(self, dispute_id: str, judge_address: str) -> Dispute:
        """Judge signals they are ready to evaluate. Transitions to JUDGING."""
        dispute = self._get_dispute(dispute_id)
        state = self._get_escrow(dispute.escrow_id)
        if judge_address != state.judge.address:
            raise EscrowError("Only the assigned judge can start judging.")
        if dispute.status not in (DisputeStatus.OPEN, DisputeStatus.EVIDENCE_PERIOD):
            raise EscrowError(f"Cannot start judging in {dispute.status.value} state.")
        dispute.status = DisputeStatus.JUDGING
        return dispute

    def resolve_dispute(
        self,
        dispute_id: str,
        judge_address: str,
        resolution: str,
        pay_worker: bool,
        milestone_index: int | None = None,
    ) -> EscrowState:
        """Judge resolves a dispute. Transitions to RESOLVED."""
        dispute = self._get_dispute(dispute_id)
        state = self._get_escrow(dispute.escrow_id)
        if judge_address != state.judge.address:
            raise EscrowError("Only the assigned judge can resolve a dispute.")
        if dispute.status != DisputeStatus.JUDGING:
            raise EscrowError(f"Cannot resolve in {dispute.status.value} state.")
        if not resolution:
            raise EscrowError("Resolution text is required.")

        dispute.status = DisputeStatus.RESOLVED
        dispute.resolution = resolution
        dispute.resolved_at = self._clock()

        # Update milestone status based on resolution
        target_milestone = milestone_index if milestone_index is not None else dispute.milestone_index
        if target_milestone is not None:
            ms = self._get_milestone(state, target_milestone)
            if pay_worker:
                ms.status = MilestoneStatus.APPROVED
                ms.approved_at = self._clock()
            else:
                ms.status = MilestoneStatus.REJECTED

        # Check if all milestones are resolved
        if all(
            m.status in (MilestoneStatus.APPROVED, MilestoneStatus.REJECTED)
            for m in state.milestones
        ):
            state.status = EscrowStatus.RESOLVED
            state.resolved_at = self._clock()
            state.dispute = None

        return state

    # ── Cancellation ─────────────────────────────────────────────────────

    def cancel(self, escrow_id: str, requester_address: str) -> EscrowState:
        """Requester cancels before funding or if no work has started."""
        state = self._get_escrow(escrow_id)
        if requester_address != state.requester.address:
            raise EscrowError("Only the requester can cancel.")
        if state.status not in (EscrowStatus.PENDING, EscrowStatus.FUNDED):
            raise EscrowError(f"Cannot cancel in {state.status.value} state.")
        # If funded but no milestone started, allow cancel
        if state.status == EscrowStatus.FUNDED:
            if any(m.status != MilestoneStatus.PENDING for m in state.milestones):
                raise EscrowError("Cannot cancel: work has already started.")
        state.status = EscrowStatus.CANCELLED
        return state

    # ── Queries ──────────────────────────────────────────────────────────

    def get_escrow(self, escrow_id: str) -> EscrowState:
        return self._get_escrow(escrow_id)

    def get_dispute(self, dispute_id: str) -> Dispute:
        return self._get_dispute(dispute_id)

    def get_milestone(self, escrow_id: str, milestone_index: int) -> Milestone:
        state = self._get_escrow(escrow_id)
        return self._get_milestone(state, milestone_index)

    def list_escrows(self) -> list[EscrowState]:
        return list(self._escrows.values())

    def list_disputes(self) -> list[Dispute]:
        return list(self._disputes.values())

    def get_pending_milestones(self, escrow_id: str) -> list[Milestone]:
        state = self._get_escrow(escrow_id)
        return [m for m in state.milestones if m.status == MilestoneStatus.PENDING]

    def get_approved_milestones(self, escrow_id: str) -> list[Milestone]:
        state = self._get_escrow(escrow_id)
        return [m for m in state.milestones if m.status == MilestoneStatus.APPROVED]

    def get_rejected_milestones(self, escrow_id: str) -> list[Milestone]:
        state = self._get_escrow(escrow_id)
        return [m for m in state.milestones if m.status == MilestoneStatus.REJECTED]

    def get_total_approved_amount(self, escrow_id: str) -> int:
        state = self._get_escrow(escrow_id)
        return sum(m.amount for m in state.milestones if m.status == MilestoneStatus.APPROVED)

    def get_total_rejected_amount(self, escrow_id: str) -> int:
        state = self._get_escrow(escrow_id)
        return sum(m.amount for m in state.milestones if m.status == MilestoneStatus.REJECTED)

    # ── Serialization ────────────────────────────────────────────────────

    def to_dict(self, escrow_id: str) -> dict[str, Any]:
        state = self._get_escrow(escrow_id)
        return {
            "escrowId": state.escrow_id,
            "requester": {"address": state.requester.address, "role": state.requester.role},
            "worker": {"address": state.worker.address, "role": state.worker.role},
            "judge": {"address": state.judge.address, "role": state.judge.role},
            "assetType": state.asset_type.value,
            "tokenAddress": state.token_address,
            "totalAmount": state.total_amount,
            "milestones": [
                {
                    "index": m.index,
                    "description": m.description,
                    "amount": m.amount,
                    "status": m.status.value,
                    "deliverableHash": m.deliverable_hash,
                    "approvedAt": m.approved_at,
                }
                for m in state.milestones
            ],
            "status": state.status.value,
            "createdAt": state.created_at,
            "fundedAt": state.funded_at,
            "deliveredAt": state.delivered_at,
            "resolvedAt": state.resolved_at,
            "dispute": self._dispute_to_dict(state.dispute) if state.dispute else None,
            "metadata": state.metadata,
        }

    # ── Internal helpers ─────────────────────────────────────────────────

    def _get_escrow(self, escrow_id: str) -> EscrowState:
        if escrow_id not in self._escrows:
            raise EscrowError(f"Escrow {escrow_id} not found.")
        return self._escrows[escrow_id]

    def _get_dispute(self, dispute_id: str) -> Dispute:
        if dispute_id not in self._disputes:
            raise EscrowError(f"Dispute {dispute_id} not found.")
        return self._disputes[dispute_id]

    @staticmethod
    def _get_milestone(state: EscrowState, index: int) -> Milestone:
        for ms in state.milestones:
            if ms.index == index:
                return ms
        raise EscrowError(f"Milestone {index} not found.")

    @staticmethod
    def _generate_id(prefix: str) -> str:
        return f"{prefix}_{secrets.token_hex(16)}"

    @staticmethod
    def _dispute_to_dict(dispute: Dispute) -> dict[str, Any]:
        return {
            "disputeId": dispute.dispute_id,
            "escrowId": dispute.escrow_id,
            "milestoneIndex": dispute.milestone_index,
            "raisedBy": dispute.raised_by,
            "reason": dispute.reason,
            "status": dispute.status.value,
            "evidence": dispute.evidence,
            "resolution": dispute.resolution,
            "resolvedAt": dispute.resolved_at,
        }
