"""Tests for the JSSP disjunctive graph solver."""
import unittest

from kernels.scheduling.job_shop import DisjunctiveGraph, Op, solve


class DisjunctiveGraphTests(unittest.TestCase):
    def test_conjunctive_arcs_chain_within_job(self):
        jobs = [[(0, 3), (1, 2)], [(0, 2), (1, 4)]]
        g = DisjunctiveGraph(jobs)
        op_map = {(op.job, op.idx): op for op in g.ops}
        self.assertEqual(g.conj[op_map[(0, 0)]], [op_map[(0, 1)]])
        self.assertEqual(g.conj[op_map[(1, 0)]], [op_map[(1, 1)]])

    def test_disjunctive_arcs_pair_ops_on_same_machine(self):
        jobs = [[(0, 3), (1, 2)], [(0, 2), (1, 4)]]
        g = DisjunctiveGraph(jobs)
        op_map = {(op.job, op.idx): op for op in g.ops}
        expected = {
            (op_map[(0, 0)], op_map[(1, 0)]),
            (op_map[(0, 1)], op_map[(1, 1)]),
        }
        self.assertEqual(set(g.disj), expected)

    def test_makespan_serializes_when_no_shared_machines(self):
        jobs = [[(0, 3), (1, 2)], [(2, 4), (3, 1)]]
        g = DisjunctiveGraph(jobs)
        self.assertEqual(g.makespan([]), 5)

    def test_makespan_accounts_for_machine_conflict(self):
        jobs = [[(0, 3), (1, 2)], [(0, 2), (1, 4)]]
        g = DisjunctiveGraph(jobs)
        # Both disjunctive arcs oriented u→v: job0 before job1 on each machine
        self.assertEqual(g.makespan([True, True]), 9)


class SolveTests(unittest.TestCase):
    def test_single_job_no_conflicts(self):
        jobs = [[(0, 3), (1, 2), (2, 4)]]
        ms, orient = solve(jobs)
        self.assertEqual(ms, 9)
        self.assertEqual(orient, [])

    def test_two_jobs_two_machines_known_optimum(self):
        jobs = [[(0, 3), (1, 2)], [(0, 2), (1, 4)]]
        ms, orient = solve(jobs)
        self.assertEqual(ms, 8)
        self.assertEqual(len(orient), 2)

    def test_three_jobs_three_machines(self):
        jobs = [
            [(0, 3), (1, 2), (2, 4)],
            [(0, 2), (1, 4), (2, 3)],
            [(0, 4), (1, 3), (2, 2)],
        ]
        ms, orient = solve(jobs)
        self.assertGreater(ms, 0)
        # 3 machines × C(3,2) pairs = 9 disjunctive arcs
        self.assertEqual(len(orient), 9)

    def test_empty_job_list(self):
        ms, orient = solve([])
        self.assertEqual(ms, 0)
        self.assertEqual(orient, [])

    def test_single_operation(self):
        ms, orient = solve([[(0, 5)]])
        self.assertEqual(ms, 5)
        self.assertEqual(orient, [])


if __name__ == "__main__":
    unittest.main()
