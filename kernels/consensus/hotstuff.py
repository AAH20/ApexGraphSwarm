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

    def collect_qc(self, block_hash: str, view: int) -> QuorumCertificate | None:
        votes = self.votes.get(block_hash, [])
        if len(votes) >= self.quorum():
            return QuorumCertificate(
                block_hash, view, tuple(v.voter for v in votes)
            )
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

    @property
    def leader(self) -> HotStuffNode:
        return self.nodes[self.leader_idx]

    def rotate_leader(self) -> None:
        self.leader_idx = (self.leader_idx + 1) % self.n

    def run_view(self, payload: Any) -> Block | None:
        leader = self.leader
        block = leader.create_block(payload)

        # Share block with all nodes so commit_3chain can traverse the chain
        for node in self.nodes:
            node.blocks[block.hash] = block

        # Prepare phase — collect votes on the leader
        qc: QuorumCertificate | None = None
        for node in self.nodes:
            v = node.vote(block, "prepare")
            leader.votes.setdefault(block.hash, []).append(v)
            qc = leader.collect_qc(block.hash, block.view)
        if qc is None:
            return None
        leader.update_high_qc(qc)

        # Pre-commit phase
        qc2: QuorumCertificate | None = None
        for node in self.nodes:
            v = node.vote(block, "pre-commit")
            leader.votes.setdefault(block.hash, []).append(v)
            qc2 = leader.collect_qc(block.hash, block.view)
        if qc2 is None:
            return None

        # Commit phase
        qc3: QuorumCertificate | None = None
        for node in self.nodes:
            v = node.vote(block, "commit")
            leader.votes.setdefault(block.hash, []).append(v)
            qc3 = leader.collect_qc(block.hash, block.view)
        if qc3 is None:
            return None

        # Check 3-chain
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
