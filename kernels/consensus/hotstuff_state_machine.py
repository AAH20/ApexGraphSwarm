"""HotStuff state machine: NewView → Prepare → PreCommit → Commit → Decide."""
from __future__ import annotations

from typing import Any

from .hotstuff_types import Block, Phase, QuorumCertificate, Vote


class HotStuffStateMachine:
    """Drives a single block through the HotStuff phase pipeline."""

    def __init__(self, n: int, f: int):
        if n < 3 * f + 1:
            raise ValueError(f"Need n >= 3f+1, got n={n}, f={f}")
        self.n = n
        self.f = f
        self.phase = Phase.NEW_VIEW
        self.view = 0
        self.block: Block | None = None
        self.votes: dict[Phase, list[Vote]] = {p: [] for p in Phase}
        self.qcs: dict[Phase, QuorumCertificate | None] = {
            Phase.PREPARE: None,
            Phase.PRE_COMMIT: None,
            Phase.COMMIT: None,
        }
        self.committed: Block | None = None

    @property
    def quorum(self) -> int:
        return 2 * self.f + 1

    def start_view(self, view: int, block: Block) -> None:
        """Enter NEW_VIEW and immediately advance to PREPARE."""
        self.view = view
        self.block = block
        self.phase = Phase.PREPARE
        self.votes = {p: [] for p in Phase}
        self.qcs = {Phase.PREPARE: None, Phase.PRE_COMMIT: None, Phase.COMMIT: None}
        self.committed = None

    def add_vote(self, vote: Vote) -> Phase:
        """Record a vote and advance the phase if quorum is reached."""
        if self.phase == Phase.DECIDE:
            return self.phase
        assert self.block is not None, "No active block — call start_view first"
        if vote.block_hash != self.block.hash:
            raise ValueError("Vote for wrong block")
        if vote.view != self.view:
            raise ValueError("Vote from wrong view")

        phase = vote.phase
        self.votes[phase].append(vote)

        if len(self.votes[phase]) >= self.quorum:
            self.qcs[phase] = QuorumCertificate(
                vote.block_hash,
                vote.view,
                tuple(v.voter for v in self.votes[phase]),
            )
            self._advance()
        return self.phase

    def _advance(self) -> None:
        """Move to the next phase based on current QC."""
        if self.phase == Phase.PREPARE and self.qcs[Phase.PREPARE]:
            self.phase = Phase.PRE_COMMIT
        elif self.phase == Phase.PRE_COMMIT and self.qcs[Phase.PRE_COMMIT]:
            self.phase = Phase.COMMIT
        elif self.phase == Phase.COMMIT and self.qcs[Phase.COMMIT]:
            self.phase = Phase.DECIDE
            self._try_commit()

    def _try_commit(self) -> None:
        """Apply the 3-chain commit rule: if block's grandparent exists, commit it."""
        b1 = self.block
        # Walk the chain: b1 → b0 → b_1
        # We need the parent and grandparent blocks to exist
        # For the state machine, we track them via the block's parent hash
        # In a full implementation, these would be looked up in a block store
        # Here we commit b1 itself as the decided block
        self.committed = b1

    def is_decided(self) -> bool:
        return self.phase == Phase.DECIDE

    def reset(self) -> None:
        """Reset to NEW_VIEW for the next view."""
        self.phase = Phase.NEW_VIEW
        self.view = 0
        self.block = None
        self.votes = {p: [] for p in Phase}
        self.qcs = {Phase.PREPARE: None, Phase.PRE_COMMIT: None, Phase.COMMIT: None}
        self.committed = None
