"""Simplex method for linear programming with Bland's rule.

Solves: max c^T x subject to Ax <= b, x >= 0, b >= 0.
Zero-dependency Python 3.10+.
"""

from __future__ import annotations


def simplex(c, A, b):
    """Solve max c^T x s.t. Ax <= b, x >= 0 (requires b >= 0).

    Args:
        c: Objective coefficients (length n).
        A: Constraint matrix (m x n).
        b: Right-hand side (length m), must be non-negative.

    Returns:
        (status, x, value) where status is "optimal" or "unbounded".
    """
    m, n = len(A), len(c)
    if any(bi < -1e-12 for bi in b):
        raise ValueError("b must be non-negative")

    # Tableau: m constraint rows + 1 objective row
    # Columns: n original + m slack + 1 RHS
    T = [[0.0] * (n + m + 1) for _ in range(m + 1)]
    basis = [n + i for i in range(m)]

    for i in range(m):
        for j in range(n):
            T[i][j] = float(A[i][j])
        T[i][n + i] = 1.0
        T[i][-1] = float(b[i])

    for j in range(n):
        T[m][j] = -float(c[j])

    while True:
        # Bland's rule: entering = smallest index with negative reduced cost
        enter = -1
        for j in range(n + m):
            if T[m][j] < -1e-12:
                enter = j
                break
        if enter == -1:
            break

        # Leaving: min ratio, Bland's tie-break on basis index
        candidates = []
        for i in range(m):
            if T[i][enter] > 1e-12:
                candidates.append((T[i][-1] / T[i][enter], basis[i], i))
        if not candidates:
            return "unbounded", None, None
        candidates.sort()
        leave = candidates[0][2]

        # Pivot
        piv = T[leave][enter]
        T[leave] = [v / piv for v in T[leave]]
        for i in range(m + 1):
            if i != leave and abs(T[i][enter]) > 1e-12:
                factor = T[i][enter]
                T[i] = [a - factor * bv for a, bv in zip(T[i], T[leave])]
        basis[leave] = enter

    x = [0.0] * n
    for i in range(m):
        if basis[i] < n:
            x[basis[i]] = T[i][-1]
    return "optimal", x, T[m][-1]  # type: ignore[return-value]


def _test():
    # Test 1: max x + y s.t. x + y <= 4, x <= 2, y <= 3
    status, x, val = simplex([1, 1], [[1, 1], [1, 0], [0, 1]], [4, 2, 3])
    assert status == "optimal" and abs(val - 4.0) < 1e-9

    # Test 2: unbounded
    status, _, _ = simplex([1, 1], [[-1, -1]], [1])
    assert status == "unbounded"

    # Test 3: max 3x + 2y s.t. x + y <= 4, 2x + y <= 5
    status, x, val = simplex([3, 2], [[1, 1], [2, 1]], [4, 5])
    assert status == "optimal" and abs(val - 9.0) < 1e-9

    # Test 4: no constraints
    status, x, val = simplex([1, 2], [], [])
    assert status == "unbounded"

    # Test 5: no variables
    status, x, val = simplex([], [[], []], [1, 2])
    assert status == "optimal" and val == 0.0

    print("All tests passed")


if __name__ == "__main__":
    _test()
