"""AI judge for evaluating escrow disputes.

The judge evaluates evidence from both parties and renders a decision.
In production this would call an LLM; here we provide a deterministic
rule-based judge that can be replaced with an LLM-backed implementation.
"""
from __future__ import annotations

import hashlib
from typing import Any, Callable

from .types import Dispute, DisputeStatus, EscrowState, MilestoneStatus


class JudgeError(ValueError):
    """Invalid judge operation."""


class AIJudge:
    """Evaluates disputes and renders decisions.

    The judge uses a scoring function to evaluate evidence. The default
    implementation uses a simple hash-based scoring that can be replaced
    with an LLM-backed evaluator.
    """

    def __init__(
        self,
        *,
        evaluator: Callable[[Dispute, EscrowState], dict[str, Any]] | None = None,
    ):
        self._evaluator = evaluator or self._default_evaluator

    def evaluate(
        self,
        dispute: Dispute,
        escrow: EscrowState,
    ) -> dict[str, Any]:
        """Evaluate a dispute and return a structured decision.

        Returns a dict with:
          - pay_worker: bool — whether the worker should be paid
          - confidence: float — 0.0 to 1.0
          - reasoning: str — human-readable explanation
          - scores: dict — per-party scores
        """
        if dispute.status != DisputeStatus.JUDGING:
            raise JudgeError(f"Cannot evaluate dispute in {dispute.status.value} state.")
        return self._evaluator(dispute, escrow)

    def render_decision(
        self,
        dispute: Dispute,
        escrow: EscrowState,
    ) -> tuple[bool, str]:
        """Render a final decision: (pay_worker, resolution_text)."""
        result = self.evaluate(dispute, escrow)
        pay_worker = result["pay_worker"]
        confidence = result["confidence"]
        reasoning = result["reasoning"]

        resolution = (
            f"Decision: {'Pay worker' if pay_worker else 'Reject worker'}. "
            f"Confidence: {confidence:.0%}. "
            f"Reasoning: {reasoning}"
        )
        return pay_worker, resolution

    # ── Default evaluator ────────────────────────────────────────────────

    @staticmethod
    def _default_evaluator(
        dispute: Dispute,
        escrow: EscrowState,
    ) -> dict[str, Any]:
        """Deterministic rule-based evaluator.

        Scores evidence based on:
          - Number of evidence items submitted by each party
          - Quality signals in evidence (hashes, timestamps, references)
          - Whether the milestone was delivered (deliverable_hash present)
        """
        worker_score = 0.0
        requester_score = 0.0

        worker_evidence = [
            e for e in dispute.evidence
            if e.get("submitter") == escrow.worker.address
        ]
        requester_evidence = [
            e for e in dispute.evidence
            if e.get("submitter") == escrow.requester.address
        ]

        # Score based on evidence count
        worker_score += len(worker_evidence) * 0.15
        requester_score += len(requester_evidence) * 0.15

        # Score based on evidence quality
        for ev in worker_evidence:
            if ev.get("deliverableHash"):
                worker_score += 0.2
            if ev.get("proofOfWork"):
                worker_score += 0.15
            if ev.get("timestamp"):
                worker_score += 0.05

        for ev in requester_evidence:
            if ev.get("rejectionReason"):
                requester_score += 0.2
            if ev.get("proofOfDefect"):
                requester_score += 0.15
            if ev.get("timestamp"):
                requester_score += 0.05

        # Check if milestone was delivered
        if dispute.milestone_index is not None:
            ms = None
            for m in escrow.milestones:
                if m.index == dispute.milestone_index:
                    ms = m
                    break
            if ms and ms.deliverable_hash:
                worker_score += 0.25
            if ms and ms.status == MilestoneStatus.DELIVERED:
                worker_score += 0.1

        # Normalize
        total = worker_score + requester_score
        if total > 0:
            worker_score /= total
            requester_score /= total

        # Decision threshold
        pay_worker = worker_score >= 0.5
        confidence = abs(worker_score - requester_score)

        if pay_worker:
            reasoning = (
                f"Worker evidence score {worker_score:.2f} meets threshold. "
                f"Deliverable was provided and work appears satisfactory."
            )
        else:
            reasoning = (
                f"Worker evidence score {worker_score:.2f} below threshold. "
                f"Requester concerns appear valid based on submitted evidence."
            )

        return {
            "pay_worker": pay_worker,
            "confidence": confidence,
            "reasoning": reasoning,
            "scores": {
                "worker": round(worker_score, 4),
                "requester": round(requester_score, 4),
            },
        }
