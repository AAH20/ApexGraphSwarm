"""Multi-decree Paxos consensus protocol.

Zero-dependency Python 3.10+ implementation with prepare/promise/accept/learn phases.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True, order=True)
class Ballot:
    round: int
    node_id: int


@dataclass
class Prepare:
    ballot: Ballot
    slot: int


@dataclass
class Promise:
    ballot: Ballot
    slot: int
    accepted: tuple[Ballot, Any] | None = None


@dataclass
class Accept:
    ballot: Ballot
    slot: int
    value: Any


@dataclass
class Accepted:
    ballot: Ballot
    slot: int


@dataclass
class Learn:
    slot: int
    value: Any


class Proposer:
    def __init__(self, node_id: int, acceptors: list[Callable], learners: list[Callable]):
        self.node_id = node_id
        self.acceptors = acceptors
        self.learners = learners
        self.round = 0
        self.promises: list[Promise] = []

    def propose(self, slot: int, value: Any) -> Any | None:
        self.round += 1
        ballot = Ballot(self.round, self.node_id)
        self.promises = [a(Prepare(ballot, slot)) for a in self.acceptors]
        self.promises = [p for p in self.promises if p is not None]
        majority = len(self.acceptors) // 2 + 1
        if len(self.promises) < majority:
            return None
        # If any acceptor already accepted a value, we must propose it
        highest = max((p.accepted for p in self.promises if p.accepted), default=None)
        if highest:
            value = highest[1]
        accepts = [a(Accept(ballot, slot, value)) for a in self.acceptors]
        if len(accepts) < majority:
            return None
        for l in self.learners:
            l(Learn(slot, value))
        return value


class Acceptor:
    def __init__(self):
        self.promised: Ballot | None = None
        self.accepted: dict[int, tuple[Ballot, Any]] = {}

    def handle(self, msg: Prepare | Accept) -> Promise | Accepted | None:
        if isinstance(msg, Prepare):
            if self.promised is None or msg.ballot > self.promised:
                self.promised = msg.ballot
                return Promise(msg.ballot, msg.slot, self.accepted.get(msg.slot))
            return None
        if isinstance(msg, Accept):
            if self.promised is None or msg.ballot >= self.promised:
                self.accepted[msg.slot] = (msg.ballot, msg.value)
                return Accepted(msg.ballot, msg.slot)
        return None


class Learner:
    def __init__(self):
        self.chosen: dict[int, Any] = {}

    def handle(self, msg: Learn) -> None:
        self.chosen[msg.slot] = msg.value


class PaxosNode:
    """Combined node: acts as proposer, acceptor, and learner."""

    def __init__(self, node_id: int):
        self.node_id = node_id
        self.acceptor = Acceptor()
        self.learner = Learner()
        self.proposer: Proposer | None = None

    def setup(self, acceptors: list[Callable], learners: list[Callable]) -> None:
        self.proposer = Proposer(self.node_id, acceptors, learners)

    def propose(self, slot: int, value: Any) -> Any | None:
        assert self.proposer is not None, "Call setup() first"
        return self.proposer.propose(slot, value)

    def handle(self, msg: Prepare | Accept | Learn) -> Promise | Accepted | None:
        if isinstance(msg, Learn):
            self.learner.handle(msg)
            return None
        return self.acceptor.handle(msg)


def create_cluster(n: int) -> tuple[list[PaxosNode], list[Callable], list[Callable]]:
    """Create a cluster of n nodes. Returns (nodes, acceptor_fns, learner_fns)."""
    nodes = [PaxosNode(i) for i in range(n)]
    acceptor_fns = [n.handle for n in nodes]
    learner_fns = [n.learner.handle for n in nodes]
    for node in nodes:
        node.setup(acceptor_fns, learner_fns)
    return nodes, acceptor_fns, learner_fns


# ── Tests ────────────────────────────────────────────────────────────────────

def test_basic_consensus():
    nodes, _, _ = create_cluster(3)
    result = nodes[0].propose(0, "value-A")
    assert result == "value-A"
    assert all(n.learner.chosen[0] == "value-A" for n in nodes)


def test_multiple_slots():
    nodes, _, _ = create_cluster(3)
    for slot in range(5):
        nodes[0].propose(slot, f"val-{slot}")
    for slot in range(5):
        assert all(n.learner.chosen[slot] == f"val-{slot}" for n in nodes)


def test_conflicting_proposals():
    nodes, _, _ = create_cluster(3)
    # Both propose to same slot; one must win
    r1 = nodes[0].propose(0, "X")
    r2 = nodes[1].propose(0, "Y")
    # At least one succeeds, and all learners agree
    assert r1 is not None or r2 is not None
    chosen = nodes[0].learner.chosen[0]
    assert all(n.learner.chosen[0] == chosen for n in nodes)


def test_majority_failure():
    nodes, _, _ = create_cluster(3)
    # Simulate 2 of 3 acceptors unreachable (return None)
    nodes[0].proposer.acceptors = [nodes[0].handle, lambda _: None, lambda _: None]  # type: ignore[union-attr]
    result = nodes[0].propose(0, "Z")
    assert result is None


def test_five_node_cluster():
    nodes, _, _ = create_cluster(5)
    for slot in range(3):
        nodes[2].propose(slot, f"five-{slot}")
    for slot in range(3):
        assert all(n.learner.chosen[slot] == f"five-{slot}" for n in nodes)


if __name__ == "__main__":
    test_basic_consensus()
    test_multiple_slots()
    test_conflicting_proposals()
    test_majority_failure()
    test_five_node_cluster()
    print("All tests passed.")
