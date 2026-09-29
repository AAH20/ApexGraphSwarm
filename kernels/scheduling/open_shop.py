"""Open Shop Scheduling Problem (OSSP) solver using permutation representation.

In OSSP, n jobs must be processed on m machines. Each job has one operation
per machine with a given processing time. Operations of the same job have no
precedence constraints. Each machine can processes at most one operation at a
time, and each job can be on at most one machine at a time. Objective: minimize
makespan (C_max).
"""
from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Sequence

__all__ = [
    "Operation",
    "ScheduledOperation",
    "decode",
    "makespan",
    "lower_bound",
    "solve",
]


@dataclass(frozen=True)
class Operation:
    job: int
    machine: int
    processing_time: int


@dataclass(frozen=True)
class ScheduledOperation:
    job: int
    machine: int
    start: int
    finish: int


def decode(permutation: Sequence[Operation], num_machines: int) -> list[ScheduledOperation]:
    """Greedy list-scheduling decoder: place each operation at the earliest
    feasible time in the order given by the permutation."""
    machine_free = [0] * num_machines
    job_free: dict[int, int] = {}
    schedule = []
    for op in permutation:
        j, k, p = op.job, op.machine, op.processing_time
        start = max(machine_free[k], job_free.get(j, 0))
        finish = start + p
        machine_free[k] = finish
        job_free[j] = finish
        schedule.append(ScheduledOperation(j, k, start, finish))
    return schedule


def makespan(schedule: Sequence[ScheduledOperation]) -> int:
    return max((op.finish for op in schedule), default=0)


def lower_bound(processing_times: Sequence[Sequence[int]]) -> int:
    """Lower bound: max of total processing time per job and per machine."""
    if not processing_times or not processing_times[0]:
        return 0
    num_jobs = len(processing_times)
    num_machines = len(processing_times[0])
    job_sums = [sum(row) for row in processing_times]
    machine_sums = [
        sum(processing_times[j][k] for j in range(num_jobs))
        for k in range(num_machines)
    ]
    return max(max(job_sums), max(machine_sums))


def _all_operations(processing_times: Sequence[Sequence[int]]) -> list[Operation]:
    return [
        Operation(j, k, processing_times[j][k])
        for j in range(len(processing_times))
        for k in range(len(processing_times[0]))
    ]


def _initial_permutation(operations: list[Operation]) -> list[Operation]:
    """Sort by descending processing time (longest operation first)."""
    return sorted(operations, key=lambda op: -op.processing_time)


def _local_search(
    permutation: list[Operation], num_machines: int, max_iterations: int = 1000
) -> list[Operation]:
    """First-improvement pairwise swap local search on the permutation."""
    best_perm = list(permutation)
    best_ms = makespan(decode(best_perm, num_machines))
    n = len(best_perm)
    for _ in range(max_iterations):
        improved = False
        for i in range(n):
            for j in range(i + 1, n):
                best_perm[i], best_perm[j] = best_perm[j], best_perm[i]
                ms = makespan(decode(best_perm, num_machines))
                if ms < best_ms:
                    best_ms = ms
                    improved = True
                    break
                best_perm[i], best_perm[j] = best_perm[j], best_perm[i]
            if improved:
                break
        if not improved:
            break
    return best_perm


def solve(
    processing_times: Sequence[Sequence[int]],
    max_iterations: int = 1000,
    seed: int | None = None,
) -> tuple[list[ScheduledOperation], int]:
    """Solve OSSP. Returns (schedule, makespan)."""
    if not processing_times or not processing_times[0]:
        return [], 0
    num_machines = len(processing_times[0])
    operations = _all_operations(processing_times)
    if seed is not None:
        rng = random.Random(seed)
        rng.shuffle(operations)
        perm = operations
    else:
        perm = _initial_permutation(operations)
    perm = _local_search(perm, num_machines, max_iterations)
    schedule = decode(perm, num_machines)
    return schedule, makespan(schedule)
