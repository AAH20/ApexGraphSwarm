import unittest

from kernels.scheduling.open_shop import (
    Operation,
    ScheduledOperation,
    decode,
    makespan,
    lower_bound,
    solve,
)


class TestOSSP(unittest.TestCase):
    def test_decode_simple(self):
        ops = [Operation(0, 0, 3), Operation(0, 1, 2), Operation(1, 0, 2), Operation(1, 1, 3)]
        schedule = decode(ops, 2)
        self.assertEqual(len(schedule), 4)
        for m in range(2):
            m_ops = sorted([s for s in schedule if s.machine == m], key=lambda s: s.start)
            for i in range(len(m_ops) - 1):
                self.assertGreaterEqual(m_ops[i + 1].start, m_ops[i].finish)
        for j in range(2):
            j_ops = sorted([s for s in schedule if s.job == j], key=lambda s: s.start)
            for i in range(len(j_ops) - 1):
                self.assertGreaterEqual(j_ops[i + 1].start, j_ops[i].finish)

    def test_makespan(self):
        schedule = [ScheduledOperation(0, 0, 0, 3), ScheduledOperation(0, 1, 3, 5)]
        self.assertEqual(makespan(schedule), 5)

    def test_makespan_empty(self):
        self.assertEqual(makespan([]), 0)

    def test_lower_bound(self):
        self.assertEqual(lower_bound([[3, 2], [2, 3]]), 5)

    def test_lower_bound_empty(self):
        self.assertEqual(lower_bound([]), 0)
        self.assertEqual(lower_bound([[]]), 0)

    def test_solve_empty(self):
        schedule, ms = solve([])
        self.assertEqual(schedule, [])
        self.assertEqual(ms, 0)

    def test_solve_single(self):
        schedule, ms = solve([[5]])
        self.assertEqual(ms, 5)
        self.assertEqual(len(schedule), 1)

    def test_solve_2x2_optimal(self):
        schedule, ms = solve([[3, 2], [2, 3]])
        self.assertEqual(ms, 5)
        self.assertEqual(len(schedule), 4)

    def test_solve_respects_constraints(self):
        pt = [[3, 2, 4], [2, 3, 1], [4, 1, 2]]
        schedule, ms = solve(pt)
        for m in range(3):
            m_ops = sorted([s for s in schedule if s.machine == m], key=lambda s: s.start)
            for i in range(len(m_ops) - 1):
                self.assertGreaterEqual(m_ops[i + 1].start, m_ops[i].finish)
        for j in range(3):
            j_ops = sorted([s for s in schedule if s.job == j], key=lambda s: s.start)
            for i in range(len(j_ops) - 1):
                self.assertGreaterEqual(j_ops[i + 1].start, j_ops[i].finish)
        self.assertEqual(ms, makespan(schedule))

    def test_solve_with_seed(self):
        schedule, ms = solve([[3, 2], [2, 3]], seed=42)
        self.assertEqual(len(schedule), 4)
        self.assertGreaterEqual(ms, lower_bound([[3, 2], [2, 3]]))

    def test_solve_zero_processing_times(self):
        schedule, ms = solve([[0, 0], [0, 0]])
        self.assertEqual(ms, 0)
        self.assertEqual(len(schedule), 4)

    def test_solve_single_job_multiple_machines(self):
        schedule, ms = solve([[3, 2, 4]])
        self.assertEqual(ms, 9)
        self.assertEqual(len(schedule), 3)

    def test_solve_single_machine_multiple_jobs(self):
        schedule, ms = solve([[3], [2], [4]])
        self.assertEqual(ms, 9)
        self.assertEqual(len(schedule), 3)


if __name__ == "__main__":
    unittest.main()
