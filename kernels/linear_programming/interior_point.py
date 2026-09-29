"""Primal-dual interior point method for linear programming.

Solves: minimize c^T x subject to Ax = b, x >= 0
Pure Python 3.10+, no external dependencies.
"""


def _matvec(A, x):
    return [sum(aij * xj for aij, xj in zip(row, x)) for row in A]


def _dot(x, y):
    return sum(xi * yi for xi, yi in zip(x, y))


def _solve(M, b):
    """Solve Mx = b via Gaussian elimination with partial pivoting."""
    n = len(M)
    aug = [row[:] + [b[i]] for i, row in enumerate(M)]
    for col in range(n):
        max_row = max(range(col, n), key=lambda r: abs(aug[r][col]))
        aug[col], aug[max_row] = aug[max_row], aug[col]
        pivot = aug[col][col]
        if abs(pivot) < 1e-12:
            raise ValueError("Singular matrix")
        for row in range(col + 1, n):
            factor = aug[row][col] / pivot
            for j in range(col, n + 1):
                aug[row][j] -= factor * aug[col][j]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (aug[i][n] - sum(aug[i][j] * x[j] for j in range(i + 1, n))) / aug[i][i]
    return x


def interior_point_lp(A, b, c, max_iter=100, tol=1e-8):
    """
    Primal-dual interior point method for LP in standard form.

    Args:
        A: m×n constraint matrix (list of lists)
        b: m-vector (list)
        c: n-vector (list)
        max_iter: maximum iterations
        tol: convergence tolerance

    Returns:
        (x, y, s, obj) where x is primal solution, y is dual solution,
        s is dual slack, obj is optimal objective value.
    """
    m = len(A)
    n = len(c)
    x = [1.0] * n
    s = [1.0] * n
    y = [0.0] * m

    for _ in range(max_iter):
        Ax = _matvec(A, x)
        r_p = [bi - ai for bi, ai in zip(b, Ax)]
        Aty = [sum(A[i][j] * y[i] for i in range(m)) for j in range(n)]
        r_d = [c[j] - Aty[j] - s[j] for j in range(n)]
        mu = _dot(x, s) / n

        if _dot(r_p, r_p) < tol**2 and _dot(r_d, r_d) < tol**2 and mu < tol:
            break

        sigma = min(0.5, mu * 10) if mu > 1e-4 else 0.01

        # M = A D^{-1} A^T where D = diag(s/x)
        M = [[0.0] * m for _ in range(m)]
        for i in range(m):
            for j in range(i, m):
                M[i][j] = sum(A[i][k] * A[j][k] * x[k] / s[k] for k in range(n))
                M[j][i] = M[i][j]

        # rhs = r_p + A D^{-1} (r_d - sigma*mu/x)
        v = [r_d[k] - sigma * mu / x[k] for k in range(n)]
        ADinv_v = [sum(A[i][k] * v[k] * x[k] / s[k] for k in range(n)) for i in range(m)]
        rhs = [r_p[i] + ADinv_v[i] for i in range(m)]

        dy = _solve(M, rhs)

        Atdy = [sum(A[i][j] * dy[i] for i in range(m)) for j in range(n)]
        dx = [(Atdy[k] - r_d[k] + sigma * mu / x[k]) * x[k] / s[k] for k in range(n)]
        ds = [sigma * mu / x[k] - s[k] - (s[k] / x[k]) * dx[k] for k in range(n)]

        alpha_p = alpha_d = 1.0
        for k in range(n):
            if dx[k] < 0:
                alpha_p = min(alpha_p, -x[k] / dx[k])
            if ds[k] < 0:
                alpha_d = min(alpha_d, -s[k] / ds[k])
        alpha_p = min(1.0, 0.99 * alpha_p)
        alpha_d = min(1.0, 0.99 * alpha_d)

        x = [xk + alpha_p * dxk for xk, dxk in zip(x, dx)]
        s = [sk + alpha_d * dsk for sk, dsk in zip(s, ds)]
        y = [yk + alpha_d * dyk for yk, dyk in zip(y, dy)]

    return x, y, s, _dot(c, x)


def _test():
    """Test the interior point method."""
    # Test 1: minimize -x1 - x2
    # subject to x1 + 2*x2 + s1 = 4, 2*x1 + x2 + s2 = 4
    # Optimal: x1 = x2 = 4/3, obj = -8/3
    A = [[1, 2, 1, 0], [2, 1, 0, 1]]
    b = [4, 4]
    c = [-1, -1, 0, 0]
    x, y, s, obj = interior_point_lp(A, b, c)
    assert abs(obj - (-8 / 3)) < 1e-4, f"Test 1: expected -8/3, got {obj}"
    assert abs(x[0] - 4 / 3) < 1e-4, f"Test 1: expected x1=4/3, got {x[0]}"
    assert abs(x[1] - 4 / 3) < 1e-4, f"Test 1: expected x2=4/3, got {x[1]}"
    print("Test 1 passed")

    # Test 2: minimize x1 + 2*x2 subject to x1 + x2 = 3
    # Optimal: x1 = 3, x2 = 0, obj = 3
    A = [[1, 1]]
    b = [3]
    c = [1, 2]
    x, y, s, obj = interior_point_lp(A, b, c)
    assert abs(obj - 3) < 1e-4, f"Test 2: expected 3, got {obj}"
    assert abs(x[0] - 3) < 1e-4, f"Test 2: expected x1=3, got {x[0]}"
    assert abs(x[1]) < 1e-4, f"Test 2: expected x2=0, got {x[1]}"
    print("Test 2 passed")


if __name__ == "__main__":
    _test()
