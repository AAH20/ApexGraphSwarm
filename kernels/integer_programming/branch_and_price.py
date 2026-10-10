"""Branch-and-price for integer programming with column generation."""
import heapq
import time
from typing import Callable, List, Optional, Tuple


def _pivot(T, basis, nv):
    """Run simplex pivots. Returns (T, basis) or (None, None) if unbounded."""
    m = len(T) - 1
    while True:
        e = -1
        for j in range(nv):
            if T[m][j] < -1e-9:
                e = j
                break
        if e == -1:
            break
        l, mr = -1, float('inf')
        for i in range(m):
            if T[i][e] > 1e-9:
                r = T[i][-1] / T[i][e]
                if r < mr:
                    mr, l = r, i
        if l == -1:
            return None, None
        p = T[l][e]
        T[l] = [v / p for v in T[l]]
        for i in range(m + 1):
            if i != l and abs(T[i][e]) > 1e-12:
                f = T[i][e]
                T[i] = [T[i][j] - f * T[l][j] for j in range(nv + 1)]
        basis[l] = e
    return T, basis


def _simplex(c, A, b):
    """Solve min c^T x s.t. A x <= b, x >= 0. Returns (x, obj, duals) or None."""
    m, n = len(A), len(c)
    neg = [i for i in range(m) if b[i] < -1e-9]
    na = len(neg)
    nv = n + m + na
    T = []
    for i in range(m):
        row = [0.0] * (nv + 1)
        if b[i] >= -1e-9:
            for j in range(n):
                row[j] = A[i][j]
            row[n + i] = 1.0
            row[-1] = b[i]
        else:
            for j in range(n):
                row[j] = -A[i][j]
            row[n + i] = -1.0
            row[n + m + neg.index(i)] = 1.0
            row[-1] = -b[i]
        T.append(row)
    obj = [0.0] * (nv + 1)
    for k in range(na):
        obj[n + m + k] = 1.0
    T.append(obj)
    basis = [n + i if b[i] >= -1e-9 else n + m + neg.index(i) for i in range(m)]
    for i in range(m):
        if basis[i] >= n + m:
            f = T[m][basis[i]]
            if abs(f) > 1e-12:
                T[m] = [T[m][j] - f * T[i][j] for j in range(nv + 1)]
    T, basis = _pivot(T, basis, nv)
    if T is None or T[m][-1] > 1e-6:
        return None
    nv2 = n + m
    T2 = [[T[i][j] for j in range(nv2)] + [T[i][-1]] for i in range(m)]
    obj2 = [c[j] for j in range(n)] + [0.0] * m + [0.0]
    T2.append(obj2)
    for i in range(m):
        if basis[i] < nv2:
            f = T2[m][basis[i]]
            if abs(f) > 1e-12:
                T2[m] = [T2[m][j] - f * T2[i][j] for j in range(nv2 + 1)]
    T2, basis = _pivot(T2, basis, nv2)
    if T2 is None:
        return None
    x = [0.0] * n
    for i in range(m):
        if basis[i] < n:
            x[basis[i]] = T2[i][-1]
    return x, T2[m][-1], [T2[m][n + i] for i in range(m)]


def _cg(c, A, b, pricing_fn, columns, bounds):
    """Solve LP relaxation via column generation."""
    while True:
        if not columns:
            return None
        cm = [col[0] for col in columns]
        Am = [[col[1][i] for col in columns] for i in range(len(b))]
        r = _simplex(cm, Am, b)
        if r is None:
            return None
        x, obj, duals = r
        nc = pricing_fn(duals, bounds)
        if nc is None:
            return x, obj, columns
        columns.append(nc)


def branch_and_price(c, A, b, pricing_fn, initial_columns=None, time_limit=60):
    """Solve min c^T x s.t. A x <= b, x >= 0, x integer via branch-and-price.

    pricing_fn(duals, bounds) -> (cost, coeffs) or None if no improving column.
    bounds: list of (var_idx, sense, value) branching constraints.
    Returns (x, obj) or (None, None) if infeasible.
    """
    start = time.time()
    columns = list(initial_columns) if initial_columns else []
    if not columns:
        col = pricing_fn([0.0] * len(b), [])
        if col is None:
            return None, None
        columns.append(col)
    root = _cg(c, A, b, pricing_fn, columns, [])
    if root is None:
        return None, None
    xr, oroot, columns = root
    if all(abs(xj - round(xj)) < 1e-6 for xj in xr):
        return [round(xj) for xj in xr], oroot
    best_x, best_obj = None, float('inf')
    cnt = 0
    pq = [(oroot, cnt, columns, [])]
    while pq and time.time() - start < time_limit:
        obj, _, cols, bounds = heapq.heappop(pq)
        if obj >= best_obj - 1e-9:
            continue
        Am = [row[:] for row in A]
        bm = list(b)
        for vi, se, val in bounds:
            row = [0.0] * len(A[0])
            row[vi] = 1.0
            if se == '>=':
                row = [-v for v in row]
                val = -val
            Am.append(row)
            bm.append(val)
        r = _cg(c, Am, bm, pricing_fn, cols, bounds)
        if r is None:
            continue
        x, lp, nc = r
        if lp >= best_obj - 1e-9:
            continue
        frac = [(j, x[j]) for j in range(len(x)) if abs(x[j] - round(x[j])) > 1e-6]
        if not frac:
            if lp < best_obj:
                best_obj = lp
                best_x = [round(xj) for xj in x]
            continue
        j, xj = max(frac, key=lambda t: abs(t[1] - round(t[1])))
        fv, cv = int(xj), int(xj) + 1
        cnt += 1
        heapq.heappush(pq, (lp, cnt, nc, bounds + [(j, '<=', fv)]))
        cnt += 1
        heapq.heappush(pq, (lp, cnt, nc, bounds + [(j, '>=', cv)]))
    return best_x, best_obj if best_x else (None, None)
