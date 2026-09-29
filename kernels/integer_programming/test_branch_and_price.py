"""Tests for branch_and_price."""
import sys
sys.path.insert(0, '/Users/ahmedhassan/Downloads/2000 workflows/projects/ApexGraphSwarm/kernels/integer_programming')
from branch_and_price import branch_and_price, _simplex, _cg


def test_simplex_basic():
    """min x+y s.t. x+2y>=4, x,y>=0 -> x=4,y=0, obj=4"""
    c = [1, 1]
    A = [[-1, -2]]  # -x-2y <= -4
    b = [-4]
    result = _simplex(c, A, b)
    assert result is not None
    x, obj, _ = result
    assert abs(obj - 4.0) < 1e-6, f"Expected 4, got {obj}"


def test_simplex_infeasible():
    """x <= -1 is infeasible"""
    c = [1]
    A = [[1]]
    b = [-1]
    result = _simplex(c, A, b)
    assert result is None


def test_branch_and_price_simple():
    """min 3x+2y s.t. x+y>=3, x,y>=0 integer -> x=3,y=0, obj=9"""
    c = [3, 2]
    A = [[-1, -1]]
    b = [-3]

    def pricing(duals, bounds):
        # Generate columns: each column is (cost, [coeffs])
        # For this simple problem, we can use unit columns
        # But we need to handle the pricing problem properly
        # min (c_j - duals^T A_j) for each possible column
        # For simplicity, generate all unit columns
        best_col = None
        best_reduced = 0
        for j in range(2):
            cost = c[j]
            coeffs = [0, 0]
            coeffs[j] = 1
            reduced = cost - sum(duals[i] * coeffs[i] for i in range(len(duals)))
            if reduced < best_reduced - 1e-9:
                best_reduced = reduced
                best_col = (cost, coeffs)
        return best_col

    x, obj = branch_and_price(c, A, b, pricing)
    assert x is not None, "Should find a solution"
    assert abs(obj - 9.0) < 1e-6, f"Expected 9, got {obj}"
    assert x[0] + x[1] >= 3, "Constraint violated"


def test_branch_and_price_infeasible():
    """x >= 5, x <= 2 -> infeasible"""
    c = [1]
    A = [[-1], [1]]
    b = [-5, 2]

    def pricing(duals, bounds):
        cost = 1
        coeffs = [1]
        reduced = cost - duals[0] * 1
        if reduced < -1e-9:
            return (cost, coeffs)
        return None

    x, obj = branch_and_price(c, A, b, pricing)
    assert x is None, "Should be infeasible"


def test_branch_and_price_fractional_root():
    """min x+y s.t. 2x+2y>=3, x,y>=0 integer -> x=1,y=1 or x=2,y=0, obj=2"""
    c = [1, 1]
    A = [[-2, -2]]
    b = [-3]

    def pricing(duals, bounds):
        best_col = None
        best_reduced = 0
        for j in range(2):
            cost = c[j]
            coeffs = [0, 0]
            coeffs[j] = 1
            reduced = cost - duals[0] * coeffs[0]
            if reduced < best_reduced - 1e-9:
                best_reduced = reduced
                best_col = (cost, coeffs)
        return best_col

    x, obj = branch_and_price(c, A, b, pricing)
    assert x is not None
    assert abs(obj - 2.0) < 1e-6, f"Expected 2, got {obj}"
    assert 2 * x[0] + 2 * x[1] >= 3


if __name__ == '__main__':
    test_simplex_basic()
    print("PASS: test_simplex_basic")
    test_simplex_infeasible()
    print("PASS: test_simplex_infeasible")
    test_branch_and_price_simple()
    print("PASS: test_branch_and_price_simple")
    test_branch_and_price_infeasible()
    print("PASS: test_branch_and_price_infeasible")
    test_branch_and_price_fractional_root()
    print("PASS: test_branch_and_price_fractional_root")
    print("\nAll tests passed!")
