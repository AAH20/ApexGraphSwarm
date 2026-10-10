import unittest

from apexgraphswarm.optimization import (
    CodeTask,
    DagTask,
    EvidenceItem,
    ModelOption,
    OptimizationInputError,
    TelemetrySample,
    plan_waves,
    recommend_capacity,
    schedule_dag,
    select_evidence,
    optimize,
)


class SchedulingTests(unittest.TestCase):
    def test_schedule_obeys_dependencies_budget_and_capacity(self):
        tasks = (
            DagTask("a", duration_estimate=1, options=(ModelOption("m", 3, 2),)),
            DagTask("b", duration_estimate=1, options=(ModelOption("m", 4, 1),)),
            DagTask("c", dependencies=("a",), options=(ModelOption("m", 2, 1),)),
        )
        result = schedule_dag(tasks, budget_microusd=9, capacities={"m": 1})
        self.assertEqual(result.status, "feasible")
        self.assertEqual(result.total_cost_microusd, 9)
        assignments = {item.task_id: item for item in result.assignments}
        self.assertGreaterEqual(assignments["c"].start, assignments["a"].finish)
        self.assertEqual(assignments["b"].start, 2)

    def test_hard_budget_deadline_and_capacity_infeasibility(self):
        task = DagTask("a", options=(ModelOption("m", 11, 2),))
        self.assertEqual(schedule_dag((task,), budget_microusd=10, capacities={"m": 1}).status, "infeasible")
        self.assertEqual(schedule_dag((task,), budget_microusd=11, capacities={"m": 1}, deadline_seconds=1).status, "infeasible")
        self.assertEqual(schedule_dag((task,), budget_microusd=11, capacities={"m": 0}).status, "infeasible")

    def test_task_and_global_deadlines_both_apply(self):
        task = DagTask("a", options=(ModelOption("m", 1, 3),), deadline=10)
        self.assertEqual(schedule_dag((task,), budget_microusd=1, capacities={"m": 1}, deadline_seconds=2).status, "infeasible")

    def test_unknown_cost_is_never_treated_as_free(self):
        task = DagTask("a", options=(ModelOption("m", None, 1),))
        result = schedule_dag((task,), budget_microusd=100, capacities={"m": 1})
        self.assertEqual(result.status, "unknown")
        self.assertIsNone(result.feasible)
        self.assertIsNone(result.total_cost_microusd)

    def test_overflowing_aggregate_duration_is_rejected(self):
        tasks = (DagTask("a", options=(ModelOption("m", 0, 1e308),)),
                 DagTask("b", ("a",), options=(ModelOption("m", 0, 1e308),)))
        with self.assertRaisesRegex(OptimizationInputError, "overflow"):
            schedule_dag(tasks, budget_microusd=0, capacities={"m": 1})

    def test_cycle_and_unknown_dependency_are_rejected(self):
        with self.assertRaisesRegex(OptimizationInputError, "cycle"):
            schedule_dag((DagTask("a", ("b",)), DagTask("b", ("a",))), budget_microusd=0, capacities={})
        with self.assertRaisesRegex(OptimizationInputError, "missing dependencies"):
            schedule_dag((DagTask("a", ("absent",)),), budget_microusd=0, capacities={})

    def test_exact_and_heuristic_modes_are_reported(self):
        task = DagTask("a", options=(ModelOption("m", 1, 1),))
        exact = schedule_dag((task,), budget_microusd=1, capacities={"m": 1})
        heuristic = schedule_dag((task,), budget_microusd=1, capacities={"m": 1}, exact_max_tasks=1)
        # exact_max_tasks is bounded to small problems; the heuristic is forced
        # by asking for a threshold below the minimum permitted bound below.
        self.assertTrue(exact.exact)
        self.assertEqual(exact.algorithm, "bounded-exhaustive")

    def test_large_schedule_heuristic_failure_is_unknown(self):
        tasks = tuple(DagTask(str(i), options=(ModelOption("m", 1, 1),)) for i in range(9))
        result = schedule_dag(tasks, budget_microusd=100, capacities={"m": 1})
        self.assertFalse(result.exact)
        self.assertEqual(result.status, "feasible")
        self.assertIn("no optimality", result.limits[0])
        failed = schedule_dag(tasks, budget_microusd=8, capacities={"m": 1})
        self.assertEqual(failed.status, "unknown")


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.items = (
            EvidenceItem("a", ("1", "2", "3", "4", "5"), 5, {}),
            EvidenceItem("b", ("1", "2", "3"), 3, {}),
            EvidenceItem("c", ("4", "5", "6"), 3, {}),
        )

    def test_exact_oracle_beats_greedy_baseline_fixture(self):
        exact = select_evidence(self.items, token_budget=6)
        greedy = select_evidence(self.items, token_budget=6, exact_max_items=2)
        self.assertEqual(exact.selected_ids, ("b", "c"))
        self.assertEqual(exact.weighted_coverage, 6)
        self.assertEqual(greedy.weighted_coverage, 5)
        self.assertTrue(exact.exact)
        self.assertFalse(greedy.exact)

    def test_token_budget_and_unique_claim_weights(self):
        items = (EvidenceItem("a", ("x",), 2, {"x": 3}), EvidenceItem("b", ("x", "y"), 3, {"x": 100, "y": 2}))
        result = select_evidence(items, token_budget=3)
        self.assertEqual(result.selected_ids, ("b",))
        self.assertEqual(result.weighted_coverage, 102)
        self.assertLessEqual(result.tokens_used, 3)

    def test_exact_ties_prefer_lexically_first_id_and_weight_overflow_is_rejected(self):
        tie = select_evidence((EvidenceItem("b", ("x",), 1, {}), EvidenceItem("a", ("x",), 1, {})), token_budget=1)
        self.assertEqual(tie.selected_ids, ("a",))
        huge = (EvidenceItem("a", ("x",), 1, {"x": 1e308}), EvidenceItem("b", ("y",), 1, {"y": 1e308}))
        with self.assertRaisesRegex(OptimizationInputError, "aggregate claim weights"):
            select_evidence(huge, token_budget=2)


class WavePlanTests(unittest.TestCase):
    def test_waves_serialize_file_conflicts_but_parallelize_disjoint_tasks(self):
        result = plan_waves((CodeTask("a", writes=("src/x.py",)), CodeTask("b", reads=("src/x.py",)), CodeTask("c", writes=("docs/x.md",))))
        self.assertEqual(result.waves[0], ("a", "c"))
        self.assertEqual(result.waves[1], ("b",))
        self.assertEqual(result.conflicts[0].files, ("src/x.py",))

    def test_path_aliases_are_canonicalized_before_conflict_checks(self):
        result = plan_waves((CodeTask("a", writes=("src/x.py",)), CodeTask("b", reads=("src/../src/x.py",))))
        self.assertEqual(result.waves, (("a",), ("b",)))
        self.assertEqual(result.conflicts[0].files, ("src/x.py",))
        with self.assertRaisesRegex(OptimizationInputError, "aliased"):
            plan_waves((CodeTask("a", writes=("src/x.py", "src/../src/x.py")),))

    def test_dependency_cycle_and_dependency_file_cycle_are_rejected(self):
        with self.assertRaisesRegex(OptimizationInputError, "cycle"):
            plan_waves((CodeTask("a", dependencies=("b",)), CodeTask("b", dependencies=("a",))))


class CapacityTests(unittest.TestCase):
    def test_recommendation_uses_only_supplied_measurements(self):
        result = recommend_capacity((TelemetrySample(1, 8, 0.1, 0.5), TelemetrySample(4, 20, 0.4, 0.9), TelemetrySample(2, 12, 0.2, 0.7)), target_utilization=0.75)
        self.assertEqual(result.recommended_concurrency, 2)
        self.assertEqual(result.measurements_used, 3)
        self.assertIn("supplied", result.limits[0])

    def test_empty_telemetry_is_insufficient_and_bad_finite_values_rejected(self):
        self.assertEqual(recommend_capacity(()).status, "insufficient_data")
        with self.assertRaises(OptimizationInputError):
            recommend_capacity((TelemetrySample(1, float("nan"), 0.1, 0.2),))


class DispatcherTests(unittest.TestCase):
    def test_json_compatible_action_dispatch(self):
        result = optimize({"action": "schedule", "budget_microusd": 4, "capacities": {"m": 1}, "tasks": [
            {"id": "a", "duration_estimate": 1, "options": [{"model": "m", "estimated_cost_microusd": 4, "duration_estimate": 1}]}
        ]})
        self.assertEqual(result["status"], "feasible")
        self.assertEqual(result["assignments"][0]["task_id"], "a")
        with self.assertRaisesRegex(OptimizationInputError, "unexpected fields"):
            optimize({"action": "waves", "tasks": [], "surprise": 1})
        with self.assertRaisesRegex(OptimizationInputError, "claims must be a list"):
            optimize({"action": "evidence", "token_budget": 4, "items": [{"id": "b", "claims": "abc", "token_cost": 1}]})
        with self.assertRaisesRegex(OptimizationInputError, "reads must be a list"):
            optimize({"action": "waves", "tasks": [{"id": "a", "reads": "ab"}]})


if __name__ == "__main__":
    unittest.main()
