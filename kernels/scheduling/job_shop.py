"""Job Shop Scheduling Problem (JSSP) solver using disjunctive graph representation.

A disjunctive graph models a JSSP instance:
- Nodes represent operations (job, position, machine, duration).
- Conjunctive arcs encode precedence within a job (fixed).
- Disjunctive arcs encode machine sharing (orientation = processing order).
A feasible schedule orients every disjunctive arc without creating a cycle.
The solver uses branch-and-bound over disjunctive arc orientations.
"""
from __future__ import annotations
from dataclasses import dataclass

INF = 10**9


@dataclass(frozen=True)
class Op:
    """A single operation in the job shop."""

    job: int
    idx: int
    machine: int
    duration: int


class DisjunctiveGraph:
    """Disjunctive graph for a job shop instance."""

    def __init__(self, jobs: list[list[tuple[int, int]]]):
        self.jobs = jobs
        self.ops = [
            Op(j, i, m, d)
            for j, job in enumerate(jobs)
            for i, (m, d) in enumerate(job)
        ]
        self.conj: dict[Op, list[Op]] = {op: [] for op in self.ops}
        self.disj: list[tuple[Op, Op]] = []
        op_map = {(op.job, op.idx): op for op in self.ops}
        for j, job in enumerate(jobs):
            for i in range(len(job) - 1):
                self.conj[op_map[(j, i)]].append(op_map[(j, i + 1)])
        by_machine: dict[int, list[Op]] = {}
        for op in self.ops:
            by_machine.setdefault(op.machine, []).append(op)
        for mops in by_machine.values():
            for i in range(len(mops)):
                for j in range(i + 1, len(mops)):
                    self.disj.append((mops[i], mops[j]))

    @property
    def n_machines(self) -> int:
        return max(op.machine for op in self.ops) + 1

    @property
    def n_jobs(self) -> int:
        return len(self.jobs)

    def makespan(self, orient: list[bool]) -> int:
        """Compute makespan for a complete disjunctive arc orientation.

        orient[i] = True means disjunctive arc i is u→v, False means v→u.
        """
        succ: dict[Op, list[Op]] = {op: [] for op in self.ops}
        for u, vs in self.conj.items():
            succ[u].extend(vs)
        for i, (u, v) in enumerate(self.disj):
            if orient[i]:
                succ[u].append(v)
            else:
                succ[v].append(u)
        memo: dict[Op, int] = {}
        visiting: set[Op] = set()

        def critical_path(u: Op) -> int:
            if u in memo:
                return memo[u]
            if u in visiting:
                return INF
            visiting.add(u)
            best = 0
            for v in succ[u]:
                best = max(best, critical_path(v) + v.duration)
            visiting.remove(u)
            memo[u] = best
            return best

        if not self.ops:
            return 0
        return max(critical_path(op) + op.duration for op in self.ops)


def solve(jobs: list[list[tuple[int, int]]]) -> tuple[int, list[bool]]:
    """Exact branch-and-bound solver. Returns (makespan, orientation)."""
    g = DisjunctiveGraph(jobs)
    n = len(g.disj)
    best = INF
    best_orient: list[bool] = []

    def bb(i: int, orient: list[bool]) -> None:
        nonlocal best, best_orient
        if i == n:
            ms = g.makespan(orient)
            if ms < best:
                best = ms
                best_orient = list(orient)
            return
        orient.append(True)
        bb(i + 1, orient)
        orient[-1] = False
        bb(i + 1, orient)
        orient.pop()

    bb(0, [])
    return best, best_orient
