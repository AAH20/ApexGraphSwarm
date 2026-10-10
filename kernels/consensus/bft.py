"""PBFT consensus: tolerates f < n/3 Byzantine faults. Zero-dep Python 3.10+."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PrePrepare:
    view: int
    seq: int
    digest: str
    node_id: int


@dataclass(frozen=True)
class Prepare:
    view: int
    seq: int
    digest: str
    node_id: int


@dataclass(frozen=True)
class Commit:
    view: int
    seq: int
    digest: str
    node_id: int


@dataclass
class PBFTNode:
    node_id: int
    n: int
    f: int
    view: int = 0
    seq: int = 0
    prepare_votes: set[int] = field(default_factory=set)
    commit_votes: set[int] = field(default_factory=set)
    pre_prepare: PrePrepare | None = None
    executed: dict[int, str] = field(default_factory=dict)
    faulty: bool = False

    @property
    def primary(self) -> int:
        return self.view % self.n

    def handle_pre_prepare(self, msg: PrePrepare) -> Prepare | None:
        if msg.view != self.view or msg.node_id != self.primary:
            return None
        self.pre_prepare = msg
        self.prepare_votes = {self.node_id}
        self.commit_votes = set()
        return Prepare(msg.view, msg.seq, msg.digest, self.node_id)

    def handle_prepare(self, msg: Prepare) -> Commit | None:
        if msg.view != self.view or self.pre_prepare is None:
            return None
        if msg.seq != self.pre_prepare.seq or msg.digest != self.pre_prepare.digest:
            return None
        self.prepare_votes.add(msg.node_id)
        if len(self.prepare_votes) >= 2 * self.f + 1 and self.node_id not in self.commit_votes:
            self.commit_votes.add(self.node_id)
            return Commit(msg.view, msg.seq, msg.digest, self.node_id)
        return None

    def handle_commit(self, msg: Commit) -> str | None:
        if msg.view != self.view:
            return None
        if self.pre_prepare and msg.digest != self.pre_prepare.digest:
            return None
        self.commit_votes.add(msg.node_id)
        if len(self.commit_votes) >= 2 * self.f + 1 and msg.seq not in self.executed:
            self.executed[msg.seq] = msg.digest
            return msg.digest
        return None


def create_cluster(n: int) -> list[PBFTNode]:
    f = (n - 1) // 3
    return [PBFTNode(i, n, f) for i in range(n)]


def run_pbft(nodes: list[PBFTNode], request: Any) -> str | None:
    """Run one PBFT round. Returns the committed digest or None."""
    primary = nodes[0].primary
    if nodes[primary].faulty:
        return None
    digest = str(request)
    pp = PrePrepare(nodes[0].view, nodes[0].seq, digest, primary)
    prepares = [p for node in nodes if not node.faulty
                for p in [node.handle_pre_prepare(pp)] if p]
    commits = [c for p in prepares for node in nodes if not node.faulty
               for c in [node.handle_prepare(p)] if c]
    results = [r for c in commits for node in nodes if not node.faulty
               for r in [node.handle_commit(c)] if r is not None]
    if results:
        for node in nodes:
            node.seq += 1
    return results[0] if results else None


# ── Tests ────────────────────────────────────────────────────────────────────

def test_basic_consensus():
    nodes = create_cluster(4)
    result = run_pbft(nodes, "tx-1")
    assert result == "tx-1"
    assert all(n.executed[0] == "tx-1" for n in nodes)


def test_one_faulty_node():
    nodes = create_cluster(4)
    nodes[1].faulty = True
    result = run_pbft(nodes, "tx-2")
    assert result == "tx-2"
    assert all(n.executed[0] == "tx-2" for n in nodes if not n.faulty)


def test_two_faulty_nodes():
    nodes = create_cluster(7)
    nodes[2].faulty = True
    nodes[5].faulty = True
    result = run_pbft(nodes, "tx-3")
    assert result == "tx-3"
    assert all(n.executed[0] == "tx-3" for n in nodes if not n.faulty)


def test_primary_faulty():
    nodes = create_cluster(4)
    nodes[0].faulty = True
    result = run_pbft(nodes, "tx-4")
    assert result is None


def test_reject_non_primary_pre_prepare():
    nodes = create_cluster(4)
    pp = PrePrepare(0, 0, "fake", 1)
    assert nodes[0].handle_pre_prepare(pp) is None


def test_reject_conflicting_prepare():
    nodes = create_cluster(4)
    pp = PrePrepare(0, 0, "correct", 0)
    nodes[0].handle_pre_prepare(pp)
    bad = Prepare(0, 0, "wrong", 1)
    assert nodes[0].handle_prepare(bad) is None


def test_multiple_rounds():
    nodes = create_cluster(4)
    for i in range(3):
        result = run_pbft(nodes, f"tx-{i}")
        assert result == f"tx-{i}"
    assert all(len(n.executed) == 3 for n in nodes)


if __name__ == "__main__":
    test_basic_consensus()
    test_one_faulty_node()
    test_two_faulty_nodes()
    test_primary_faulty()
    test_reject_non_primary_pre_prepare()
    test_reject_conflicting_prepare()
    test_multiple_rounds()
    print("All tests passed.")
