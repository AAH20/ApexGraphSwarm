"""Flow Shop Scheduling Problem (FSSP) solver.

Permutation representation: a schedule is a tuple of job indices.
Zero-dependency, Python 3.10+.
"""
from __future__ import annotations


def makespan(proc: list[list[int]], perm: tuple[int, ...]) -> int:
    """Compute the makespan for a given job permutation."""
    m = len(proc[0])
    n = len(perm)
    completion = [[0] * m for _ in range(n)]
    for i, job in enumerate(perm):
        for j in range(m):
            prev_job = completion[i - 1][j] if i > 0 else 0
            prev_machine = completion[i][j - 1] if j > 0 else 0
            completion[i][j] = max(prev_job, prev_machine) + proc[job][j]
    return completion[-1][-1]


def johnson_rule(proc: list[list[int]]) -> tuple[int, ...]:
    """Optimal for 2-machine FSSP. Returns a permutation."""
    set1: list[int] = []  # p_i1 <= p_i2
    set2: list[int] = []  # p_i1 > p_i2
    for j in range(len(proc)):
        if proc[j][0] <= proc[j][1]:
            set1.append(j)
        else:
            set2.append(j)
    set1.sort(key=lambda j: proc[j][0])
    set2.sort(key=lambda j: -proc[j][1])
    return tuple(set1 + set2)


def neh_heuristic(proc: list[list[int]]) -> tuple[int, ...]:
    """NEH heuristic for n-machine FSSP. Returns a permutation."""
    n = len(proc)
    totals = [sum(proc[j]) for j in range(n)]
    order = sorted(range(n), key=lambda j: -totals[j])
    perm = [order[0]]
    for k in range(1, n):
        best_perm: list[int] = perm + [order[k]]
        best_ms = makespan(proc, tuple(best_perm))
        for pos in range(len(perm) + 1):
            candidate = perm[:pos] + [order[k]] + perm[pos:]
            ms = makespan(proc, tuple(candidate))
            if ms < best_ms:
                best_ms = ms
                best_perm = candidate
        perm = best_perm
    return tuple(perm)


def local_search(
    proc: list[list[int]], perm: tuple[int, ...], max_iter: int = 1000
) -> tuple[int, ...]:
    """First-improvement insertion local search."""
    n = len(perm)
    best = list(perm)
    best_ms = makespan(proc, tuple(best))
    improved = True
    it = 0
    while improved and it < max_iter:
        improved = False
        it += 1
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                candidate = best[:]
                job = candidate.pop(i)
                candidate.insert(j, job)
                ms = makespan(proc, tuple(candidate))
                if ms < best_ms:
                    best = candidate
                    best_ms = ms
                    improved = True
                    break
            if improved:
                break
    return tuple(best)


def solve(proc: list[list[int]], improve: bool = True) -> tuple[tuple[int, ...], int]:
    """Solve FSSP. Returns (permutation, makespan)."""
    if len(proc[0]) == 2:
        perm = johnson_rule(proc)
    else:
        perm = neh_heuristic(proc)
    if improve:
        perm = local_search(proc, perm)
    return perm, makespan(proc, perm)


# --- Tests ---
def _test() -> None:
    # 2-machine: Johnson's rule is optimal
    proc2 = [[3, 2], [1, 4], [5, 1], [2, 3]]
    perm, ms = solve(proc2, improve=False)
    assert ms == 12, f"Johnson 2-machine: expected 12, got {ms}"

    # 3-machine: NEH + local search
    proc3 = [[3, 3, 2], [1, 2, 4], [4, 1, 3], [2, 4, 1]]
    perm, ms = solve(proc3)
    assert len(perm) == 4
    assert set(perm) == {0, 1, 2, 3}
    assert ms == makespan(proc3, perm)

    # Single job
    proc1 = [[5, 3, 2]]
    perm, ms = solve(proc1)
    assert perm == (0,)
    assert ms == 10

    # Single machine
    proc_m = [[3], [1], [4], [2]]
    perm, ms = solve(proc_m)
    assert ms == 10

    # 5-job 3-machine instance
    proc_c = [[5, 9, 8], [9, 3, 10], [10, 7, 8], [9, 5, 1], [1, 3, 6]]
    perm, ms = solve(proc_c)
    assert ms <= 41, f"Expected makespan <= 41, got {ms}"

    print("All tests passed.")


if __name__ == "__main__":
    _test()
