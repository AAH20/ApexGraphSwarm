"""Branch-and-bound for MILP using simplex LP relaxation. Zero-dep Python 3.10+."""
from __future__ import annotations
import math
from dataclasses import dataclass
@dataclass
class LPResult:
    status: str
    objective: float | None
    solution: list[float] | None
def _pivot(T, m, n, r, c):
    piv = T[r][c]
    T[r] = [v / piv for v in T[r]]
    for i in range(m + 1):
        if i != r and T[i][c] != 0:
            f = T[i][c]
            T[i] = [a - f * b for a, b in zip(T[i], T[r])]
def _basic_cols(T, m, n):
    cols = []
    for i in range(m):
        col = -1
        for j in range(n):
            if abs(T[i][j] - 1.0) < 1e-9 and all(abs(T[k][j]) < 1e-9 for k in range(m) if k != i):
                col = j
                break
        cols.append(col)
    return cols
def _simplex(T, m, n):
    while True:
        col = -1
        for j in range(n):
            if T[m][j] < -1e-9:
                col = j
                break
        if col < 0:
            return True
        row = -1
        min_ratio = float('inf')
        for i in range(m):
            if T[i][col] > 1e-9:
                ratio = T[i][n] / T[i][col]
                if ratio < min_ratio:
                    min_ratio = ratio
                    row = i
        if row < 0:
            return False
        _pivot(T, m, n, row, col)
def simplex(c, A, b, senses=None):
    m, n = len(A), len(c)
    if senses is None:
        senses = ['<='] * m
    A = [row[:] for row in A]
    b = b[:]
    for i in range(m):
        if b[i] < 0:
            b[i] = -b[i]
            A[i] = [-a for a in A[i]]
            senses[i] = {'<=': '>=', '>=': '<=', '=': '='}[senses[i]]
    extra = []
    for i, s in enumerate(senses):
        if s == '<=':
            extra.append(('s', i))
        elif s == '>=':
            extra.append(('s', i))
            extra.append(('a', i))
        elif s == '=':
            extra.append(('a', i))
    ne = len(extra)
    total = n + ne
    T = [[0.0] * (total + 1) for _ in range(m + 1)]
    col = n
    art_rows = set()
    for i, s in enumerate(senses):
        for j in range(n):
            T[i][j] = A[i][j]
        T[i][total] = b[i]
        if s == '<=':
            T[i][col] = 1.0
            col += 1
        elif s == '>=':
            T[i][col] = -1.0
            col += 1
            T[i][col] = 1.0
            art_rows.add(i)
            col += 1
        elif s == '=':
            T[i][col] = 1.0
            art_rows.add(i)
            col += 1
    if art_rows:
        for j in range(total + 1):
            T[m][j] = 0.0
        for j in range(n):
            T[m][j] = sum(A[i][j] for i in art_rows)
        for idx, (typ, row) in enumerate(extra):
            if typ == 's' and senses[row] == '>=':
                T[m][n + idx] = -1.0
        T[m][total] = -sum(b[i] for i in art_rows)
        if not _simplex(T, m, total) or T[m][total] < -1e-9:
            return LPResult('infeasible', None, None)
        art_cols = {n + k for k, (t, r) in enumerate(extra) if t == 'a'}
        for i in range(m):
            if i in art_rows:
                for j in range(total):
                    if j not in art_cols and abs(T[i][j]) > 1e-9:
                        _pivot(T, m, total, i, j)
                        break
    for j in range(total + 1):
        T[m][j] = 0.0
    for j in range(n):
        T[m][j] = -c[j]
    for i, bc in enumerate(_basic_cols(T, m, total)):
        if bc >= 0 and abs(T[m][bc]) > 1e-9:
            f = T[m][bc]
            for j in range(total + 1):
                T[m][j] -= f * T[i][j]
    if not _simplex(T, m, total):
        return LPResult('unbounded', None, None)
    x = [0.0] * n
    for i, bc in enumerate(_basic_cols(T, m, total)):
        if 0 <= bc < n:
            x[bc] = T[i][total]
    return LPResult('optimal', T[m][total], x)
def branch_and_bound(c, A, b, integer_vars, senses=None):
    best_obj = -float('inf')
    best_x = None
    stack = [([], [], [])]
    while stack:
        eA, eb, es = stack.pop()
        result = simplex(c, A + eA, b + eb, (senses or ['<='] * len(A)) + es)
        if result.status == 'unbounded':
            return LPResult('unbounded', None, None)
        if result.status != 'optimal' or result.objective <= best_obj + 1e-9:
            continue
        frac_var = -1
        for i in integer_vars:
            if abs(result.solution[i] - round(result.solution[i])) > 1e-6:
                frac_var = i
                break
        if frac_var < 0:
            best_obj = result.objective
            best_x = result.solution
            continue
        val = result.solution[frac_var]
        row = [0.0] * len(c)
        row[frac_var] = 1.0
        stack.append((eA + [row], eb + [math.floor(val)], es + ['<=']))
        stack.append((eA + [row], eb + [math.ceil(val)], es + ['>=']))
    if best_x is None:
        return LPResult('infeasible', None, None)
    return LPResult('optimal', best_obj, best_x)
def _test():
    r = branch_and_bound([1, 1], [[2, 1], [1, 2]], [5, 5], [0, 1])
    assert r.status == 'optimal' and abs(r.objective - 3) < 1e-6
    r = branch_and_bound([1], [[1], [1]], [1, 2], [0], ['<=', '>='])
    assert r.status == 'infeasible'
    r = branch_and_bound([1, 1], [[1, 1]], [3], [0, 1], ['='])
    assert r.status == 'optimal' and abs(r.objective - 3) < 1e-6
    r = branch_and_bound([1, 1], [[1, 1]], [3], [])
    assert r.status == 'optimal' and abs(r.objective - 3) < 1e-6
    r = branch_and_bound([1], [], [], [])
    assert r.status == 'unbounded'
    print("All tests passed!")
if __name__ == '__main__':
    _test()
