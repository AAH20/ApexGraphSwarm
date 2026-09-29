"""Branch-and-cut for integer programming.

Solves: max c^T x s.t. Ax <= b, x >= 0, x integer
Using simplex for LP relaxation + Gomory cuts + branch-and-bound.
Zero dependencies, Python 3.10+.
"""
from math import floor


def _pivot(T, r, c):
    p = T[r][c]
    T[r] = [v / p for v in T[r]]
    for i in range(len(T)):
        if i != r and T[i][c] != 0:
            f = T[i][c]
            T[i] = [a - f * b for a, b in zip(T[i], T[r])]


def simplex(c, A, b):
    """Solve max c^T x s.t. Ax <= b, x >= 0 using big-M simplex."""
    m, n = len(A), len(c)
    M = 1e7
    A = [list(map(float, r)) for r in A]
    b = list(map(float, b))
    is_ge = [False] * m
    for i in range(m):
        if b[i] < 0:
            A[i] = [-a for a in A[i]]
            b[i] = -b[i]
            is_ge[i] = True
    nv = n + 2 * m
    T = [[0.0] * (nv + 1) for _ in range(m + 1)]
    basis = [0] * m
    for i in range(m):
        T[i][:n] = A[i]
        T[i][n + i] = 1.0
        basis[i] = n + i
        if is_ge[i]:
            T[i][n + i] = -1.0
            T[i][n + m + i] = 1.0
            basis[i] = n + m + i
        T[i][nv] = b[i]
    T[m][:n] = [-cj for cj in c]
    for i in range(m):
        if is_ge[i]:
            T[m][n + m + i] = M
            for j in range(nv + 1):
                T[m][j] += -M * T[i][j]
    while True:
        e = -1
        for j in range(nv):
            if T[m][j] < -1e-9:
                e = j
                break
        if e == -1:
            break
        l = -1
        mr = float('inf')
        for i in range(m):
            if T[i][e] > 1e-9:
                r = T[i][nv] / T[i][e]
                if r < mr:
                    mr = r
                    l = i
        if l == -1:
            return 'unbounded', None, None, None, None
        _pivot(T, l, e)
        basis[l] = e
    if any(is_ge[i] and basis[i] >= n + m for i in range(m)):
        return 'infeasible', None, None, None, None
    x = [0.0] * n
    for i in range(m):
        if basis[i] < n:
            x[basis[i]] = T[i][nv]
    obj = sum(c[j] * x[j] for j in range(n))
    return 'optimal', x, obj, T, basis


def gomory_cut(T, n, m, A, b, is_ge):
    """Extract Gomory fractional cut from optimal tableau."""
    bi = -1
    bf = 0
    for i in range(m):
        frac = T[i][-1] - floor(T[i][-1])
        if 1e-9 < frac < 1 - 1e-9 and frac > bf:
            bf = frac
            bi = i
    if bi == -1:
        return None
    cc = [0.0] * n
    cr = T[bi][-1] - floor(T[bi][-1])
    for j in range(n):
        cc[j] = T[bi][j] - floor(T[bi][j])
    for k in range(m):
        fc = T[bi][n + k] - floor(T[bi][n + k])
        if is_ge[k]:
            for j in range(n):
                cc[j] += fc * A[k][j]
            cr += fc * b[k]
        else:
            for j in range(n):
                cc[j] -= fc * A[k][j]
            cr -= fc * b[k]
    return ([-c for c in cc], -cr)


def branch_and_cut(c, A, b, max_nodes=1000):
    """Solve integer program using branch-and-cut."""
    best_obj = float('inf')
    best_x = None
    nodes = [(c, A, b, [False] * len(A))]
    while nodes and max_nodes > 0:
        max_nodes -= 1
        cn, An, bn, ign = nodes.pop()
        st, x, obj, T, basis = simplex(cn, An, bn)
        if st == 'infeasible':
            continue
        if st == 'unbounded':
            return 'unbounded', None, None
        if obj >= best_obj:
            continue
        if all(abs(xj - round(xj)) < 1e-6 for xj in x):
            if obj < best_obj:
                best_obj = obj
                best_x = x
            continue
        cut = gomory_cut(T, len(cn), len(An), An, bn, ign)
        if cut is not None:
            ca, cb = cut
            nodes.append((cn, An + [ca], bn + [cb], ign + [False]))
            continue
        fv = max(range(len(x)), key=lambda j: abs(x[j] - round(x[j])))
        fl = floor(x[fv])
        nodes.append((cn, An + [[1 if j == fv else 0 for j in range(len(x))]], bn + [fl], ign + [False]))
        nodes.append((cn, An + [[-1 if j == fv else 0 for j in range(len(x))]], bn + [-(fl + 1)], ign + [True]))
    if best_x is None:
        return 'infeasible', None, None
    return 'optimal', best_x, best_obj


# ── Tests ──────────────────────────────────────────────────────────────────

def test_simplex():
    st, x, obj, _, _ = simplex([3, 2], [[2, 1], [1, 2]], [4, 4])
    assert st == 'optimal' and abs(obj - 20 / 3) < 1e-6
    st, _, _, _, _ = simplex([1], [[-1]], [1])
    assert st == 'unbounded'
    st, _, _, _, _ = simplex([1], [[1]], [-2])
    assert st == 'infeasible'
    print("  simplex tests passed")


def test_branch_and_cut():
    st, x, obj = branch_and_cut([3, 2], [[2, 1], [1, 2]], [4, 4])
    assert st == 'optimal' and abs(obj - 6) < 1e-6
    assert abs(x[0] - 2) < 1e-6 and abs(x[1]) < 1e-6
    st, x, obj = branch_and_cut([1, 1], [[2, 2]], [3])
    assert st == 'optimal' and abs(obj - 1) < 1e-6
    st, _, _ = branch_and_cut([1], [[1]], [-2])
    assert st == 'infeasible'
    print("  branch_and_cut tests passed")


if __name__ == '__main__':
    test_simplex()
    test_branch_and_cut()
    print("All tests passed.")
