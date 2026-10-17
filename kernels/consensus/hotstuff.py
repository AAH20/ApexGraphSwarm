"""HotStuff BFT consensus: linear communication, 3-chain commit rule."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Sequence


@dataclass(frozen=True)
class Block:
    view: int
    parent: str
    payload: Any
    qc: "QuorumCertificate | None" = None

    @property
    def hash(self) -> str:
        return hashlib.sha256(
            f"{self.view}:{self.parent}:{self.payload}".encode()
        ).hexdigest()[:16]


@dataclass(frozen=True)
class QuorumCertificate:
    block_hash: str
    view: int
    signers: tuple[str, ...] = field(default_factory=tuple)

    def has_quorum(self, n: int) -> bool:
        return len(self.signers) >= 2 * ((n - 1) // 3) + 1


@dataclass
class Vote:
    block_hash: str
    view: int
    voter: str
    phase: str  # "prepare", "pre-commit", "commit"


class HotStuffNode:
    def __init__(self, node_id: str, n: int, f: int):
        self.node_id = node_id
        self.n = n
        self.f = f
        self.view = 0
        self.blocks: dict[str, Block] = {}
        self.votes: dict[str, list[Vote]] = {}
        self.high_qc: QuorumCertificate | None = None
        self.committed: list[Block] = []

    def quorum(self) -> int:
        return 2 * self.f + 1

    def create_block(self, payload: Any) -> Block:
        parent = self.high_qc.block_hash if self.high_qc else "genesis"
        block = Block(self.view, parent, payload, self.high_qc)
        self.blocks[block.hash] = block
        return block

    def vote(self, block: Block, phase: str) -> Vote:
        v = Vote(block.hash, block.view, self.node_id, phase)
        self.votes.setdefault(block.hash, []).append(v)
        return v

    def collect_qc(self, block_hash: str, view: int, phase: str = "prepare") -> QuorumCertificate | None:
        """Form a quorum certificate for one phase.

        A node records its own vote in `vote()`, so the leader aggregates across the
        cluster for the phase being certified. The previous signature took no phase and
        read only the leader's own table, which both double-counted the leader's vote
        and conflated the three phases.
        """
        signers = [v.voter for v in self.votes.get(block_hash, []) if v.phase == phase]
        if len(signers) >= self.quorum():
            return QuorumCertificate(block_hash, view, tuple(signers))
        return None

    def update_high_qc(self, qc: QuorumCertificate) -> None:
        if self.high_qc is None or qc.view > self.high_qc.view:
            self.high_qc = qc

    def commit_3chain(self, block: Block) -> Block | None:
        """Return the committed block if block completes a 3-chain."""
        b1 = block
        b0 = self.blocks.get(b1.parent)
        if b0 is None:
            return None
        b_1 = self.blocks.get(b0.parent)
        if b_1 is None:
            return None
        return b_1  # b_1 is committed


class HotStuffCluster:
    def __init__(self, n: int = 4, f: int = 1):
        if n < 3 * f + 1:
            raise ValueError(f"Need n >= 3f+1, got n={n}, f={f}")
        self.n = n
        self.f = f
        self.nodes = [HotStuffNode(f"node-{i}", n, f) for i in range(n)]
        self.leader_idx = 0
        self.view = 0
        self.high_qc: QuorumCertificate | None = None

    @property
    def leader(self) -> HotStuffNode:
        return self.nodes[self.leader_idx]

    def rotate_leader(self) -> None:
        self.leader_idx = (self.leader_idx + 1) % self.n

    def _quorum_for(self, block: Block, phase: str) -> QuorumCertificate | None:
        """Gather one vote per replica for `phase` and certify a quorum.

        Each replica records its own vote in `vote()`; the leader aggregates across the
        cluster. Reading only the leader's own table (the previous behaviour) certified
        a quorum from a single node's tally.
        """
        signers = [
            v.voter
            for node in self.nodes
            for v in node.votes.get(block.hash, [])
            if v.phase == phase
        ]
        if len(signers) >= self.leader.quorum():
            return QuorumCertificate(block.hash, block.view, tuple(signers))
        return None

    def run_view(self, payload: Any) -> Block | None:
        """Run one HotStuff view: propose, then prepare / pre-commit / commit.

        The view counter advances and the resulting QC is broadcast to every replica,
        so the next block's parent is the block just certified. Without both, every
        block was proposed against `genesis` and `commit_3chain` could never find the
        two ancestors it needs.
        """
        self.view += 1
        leader = self.leader

        for node in self.nodes:
            node.view = self.view
            if self.high_qc is not None:
                node.high_qc = self.high_qc

        block = leader.create_block(payload)
        for node in self.nodes:
            node.blocks[block.hash] = block

        qc: QuorumCertificate | None = None
        for phase in ("prepare", "pre-commit", "commit"):
            for node in self.nodes:
                node.vote(block, phase)
            qc = self._quorum_for(block, phase)
            if qc is None:
                return None

        # Broadcast the QC so the next proposal links to this block.
        self.high_qc = qc
        for node in self.nodes:
            node.high_qc = qc

        committed = leader.commit_3chain(block)
        if committed:
            leader.committed.append(committed)

        self.rotate_leader()
        return committed

    def run_views(self, payloads: Sequence[Any]) -> list[Block]:
        committed = []
        for payload in payloads:
            result = self.run_view(payload)
            if result:
                committed.append(result)
        return committed
