"""HotStuff BFT consensus data structures."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Phase(Enum):
    NEW_VIEW = "new_view"
    PREPARE = "prepare"
    PRE_COMMIT = "pre_commit"
    COMMIT = "commit"
    DECIDE = "decide"


@dataclass(frozen=True)
class Block:
    view: int
    parent: str
    payload: Any
    qc: QuorumCertificate | None = None

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
    phase: Phase


def commit_3chain(block: Block, store: dict[str, Block]) -> Block | None:
    """Return the committed block if `block` completes a 3-chain.

    A 3-chain is: b0 <- b1 <- b2 (three consecutive blocks).
    When b2 arrives, b0 is committed.
    """
    b1 = block
    b0 = store.get(b1.parent)
    if b0 is None:
        return None
    b_1 = store.get(b0.parent)
    if b_1 is None:
        return None
    return b_1


# ── Tests ────────────────────────────────────────────────────────────────────

def test_block_hash():
    b = Block(1, "genesis", "tx")
    assert len(b.hash) == 16
    assert b.hash == Block(1, "genesis", "tx").hash

def test_quorum():
    qc = QuorumCertificate("abc", 1, tuple(f"n{i}" for i in range(4)))
    assert qc.has_quorum(4)
    assert not qc.has_quorum(7)

def test_vote():
    v = Vote("abc", 1, "node-0", Phase.PREPARE)
    assert v.voter == "node-0"

def test_3chain():
    store: dict[str, Block] = {}
    b0 = Block(0, "genesis", "a")
    store[b0.hash] = b0
    b1 = Block(1, b0.hash, "b")
    store[b1.hash] = b1
    b2 = Block(2, b1.hash, "c")
    store[b2.hash] = b2
    assert commit_3chain(b2, store) == b0
    assert commit_3chain(b1, store) is None

if __name__ == "__main__":
    test_block_hash()
    test_quorum()
    test_vote()
    test_3chain()
    print("All tests passed.")
