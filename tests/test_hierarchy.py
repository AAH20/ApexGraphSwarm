import copy
import unittest

from apexgraphswarm.hierarchy import (
    HARD_GATES, METRIC_PROFILES, HierarchyError, get_metric_profile,
    plan_hierarchy, weighted_score,
)
from apexgraphswarm.lab import dispatch


def scores(values=None):
    keys = METRIC_PROFILES["coding"]["weights"]
    return {key: (values or {}).get(key, 0.8) for key in keys}


def payload():
    return {
        "profileId": "coding",
        "limits": {"budgetMicrousd": 500, "deadlineMs": 5000, "maxClusterTasks": 2, "maxClusters": 8},
        "tasks": [
            {"id": "inspect", "family": "repo", "dependencies": [], "requiredCapabilities": ["read_repo"],
             "requiredActions": ["read"], "resourceScope": "repo:fixture", "dataBoundary": "public",
             "estimatedCostMicrousd": 100, "estimatedLatencyMs": 1000},
            {"id": "verify", "family": "repo", "dependencies": ["inspect"], "requiredCapabilities": ["python", "tests"],
             "requiredActions": ["read", "run_tests"], "resourceScope": "repo:fixture", "dataBoundary": "public",
             "estimatedCostMicrousd": 200, "estimatedLatencyMs": 2500},
        ],
        "agents": [
            {"id": "leader", "role": "leader", "profileIds": ["coding"], "capabilities": ["coordination"],
             "authorizedActions": ["read", "run_tests"], "authorizationGrantId": "grant:leader",
             "resourceScopes": ["repo:fixture"], "dataBoundaries": ["public"], "maxAssignments": 1,
             "metricScores": scores({"coordination_efficiency": 0.95})},
            {"id": "worker", "role": "worker", "profileIds": ["coding"], "capabilities": ["read_repo", "python", "tests"],
             "authorizedActions": ["read", "run_tests"], "authorizationGrantId": "grant:worker",
             "resourceScopes": ["repo:fixture"], "dataBoundaries": ["public"], "maxAssignments": 2,
             "estimatedCostMicrousdPerTask": 150, "metricScores": scores({"correctness": 0.9})},
        ],
    }


class MetricProfileTests(unittest.TestCase):
    def test_all_builtin_weights_are_exactly_100_and_hard_gates_are_separate(self):
        for profile_id in METRIC_PROFILES:
            profile = get_metric_profile(profile_id)
            self.assertEqual(sum(profile["weights"].values()), 100)
            self.assertEqual(profile["weightTotal"], 100)
            self.assertEqual(profile["hardGates"], list(HARD_GATES))
        self.assertIn("A weighted score cannot override a failed hard gate.", weighted_score("coding", scores())["note"])

    def test_weighted_score_is_explicit_and_missing_metrics_are_not_renormalized(self):
        complete = weighted_score("coding", scores({"correctness": 1.0}))
        self.assertTrue(complete["complete"])
        self.assertAlmostEqual(complete["score"], 0.86)
        partial = weighted_score("coding", {"correctness": 1.0})
        self.assertFalse(partial["complete"])
        self.assertIsNone(partial["score"])
        self.assertEqual(len(partial["missingMetrics"]), 7)

    def test_rejects_unknown_and_out_of_range_metric_values(self):
        with self.assertRaisesRegex(HierarchyError, "unknown metrics"):
            weighted_score("coding", {**scores(), "invented": 1})
        with self.assertRaisesRegex(HierarchyError, "between"):
            weighted_score("coding", scores({"correctness": 2}))
        with self.assertRaisesRegex(HierarchyError, "profileId"):
            get_metric_profile("not-a-domain")

    def test_custom_weights_are_complete_sum_to_100_and_versioned(self):
        custom = {name: 0 for name in METRIC_PROFILES["coding"]["weights"]}
        custom["correctness"] = 100
        with self.assertRaisesRegex(HierarchyError, "requires metricWeightVersion"):
            weighted_score("coding", scores(), weights=custom)
        ranked = weighted_score("coding", scores({"correctness": 0.25}), weights=custom,
                                weight_version="team-policy-2")
        self.assertEqual(ranked["metricWeightVersion"], "team-policy-2")
        self.assertEqual(ranked["score"], 0.25)
        custom["correctness"] = 99
        with self.assertRaisesRegex(HierarchyError, "sum to exactly 100"):
            weighted_score("coding", scores(), weights=custom, weight_version="bad-v1")


class HierarchyPlanTests(unittest.TestCase):
    def test_plan_clusters_dependencies_and_ranks_workers_without_dispatch(self):
        result = plan_hierarchy(payload())
        self.assertEqual(result["status"], "plan_only")
        self.assertEqual(result["execution"], "plan_only")
        self.assertEqual(result["hierarchy"]["depth"], 4)
        self.assertEqual(result["clusterCount"], 1)
        self.assertEqual(result["estimatedCriticalPathMs"], 3500)
        self.assertEqual(result["estimatedTotalCostMicrousd"], 300)
        self.assertEqual(result["actualCostMicrousd"], None)
        self.assertEqual(result["unitEconomics"]["costPerAcceptedOutcomeMicrousd"], None)
        self.assertEqual(result["assignments"][1]["authorizationGrantId"], "grant:worker")
        self.assertEqual(result["assignments"][1]["workerId"], "worker")
        self.assertEqual(result["blockers"], [])

    def test_cost_unknown_budget_failure_and_deadline_failure_are_not_silently_accepted(self):
        unknown = payload()
        unknown["tasks"][0].pop("estimatedCostMicrousd")
        unknown["agents"][1].pop("estimatedCostMicrousdPerTask")
        result = plan_hierarchy(unknown)
        self.assertEqual(result["status"], "blocked_unknown_cost")
        self.assertIsNone(result["estimatedTotalCostMicrousd"])
        self.assertIn("inspect", result["unknownCostTaskIds"])
        too_expensive = payload()
        too_expensive["limits"]["budgetMicrousd"] = 299
        self.assertEqual(plan_hierarchy(too_expensive)["status"], "over_budget")
        too_slow = payload()
        too_slow["limits"]["deadlineMs"] = 100
        self.assertEqual(plan_hierarchy(too_slow)["status"], "deadline_exceeded")

    def test_scopes_actions_capabilities_and_boundaries_fail_closed(self):
        raw = payload()
        raw["agents"][1]["resourceScopes"] = ["repo:other"]
        result = plan_hierarchy(raw)
        self.assertEqual(result["status"], "not_plannable")
        self.assertIn("worker_unavailable", [item["code"] for item in result["blockers"]])
        raw = payload()
        raw["agents"][0]["authorizedActions"] = ["read"]
        result = plan_hierarchy(raw)
        self.assertIsNone(result["hierarchy"]["clusters"][0]["leaderId"])
        self.assertIn("leader_unavailable", [item["code"] for item in result["blockers"]])

    def test_cluster_boundaries_and_task_cycle_are_enforced(self):
        raw = payload()
        raw["tasks"][1]["dataBoundary"] = "restricted"
        result = plan_hierarchy(raw)
        self.assertEqual(result["clusterCount"], 2)
        raw = payload()
        raw["tasks"][0]["dependencies"] = ["verify"]
        with self.assertRaisesRegex(HierarchyError, "cycle"):
            plan_hierarchy(raw)

    def test_dispatch_accepts_only_bounded_hierarchy_schema(self):
        raw = {"action": "hierarchy", **payload()}
        result = dispatch(raw)
        self.assertEqual(result["schemaVersion"], "hierarchical-plan-v1")
        bad = copy.deepcopy(raw)
        bad["surprise"] = True
        with self.assertRaisesRegex(HierarchyError, "requires profileId"):
            dispatch(bad)

    def test_custom_weighted_hierarchy_requires_a_weight_set_version(self):
        raw = payload()
        weights = {name: 0 for name in METRIC_PROFILES["coding"]["weights"]}
        weights["correctness"] = 100
        raw["metricWeights"] = weights
        with self.assertRaisesRegex(HierarchyError, "requires metricWeightVersion"):
            plan_hierarchy(raw)
        raw["metricWeightVersion"] = "fixture-correctness-v2"
        result = plan_hierarchy(raw)
        self.assertEqual(result["profile"]["weightSetVersion"], "fixture-correctness-v2")
        self.assertEqual(result["assignments"][0]["workerProfileScore"], 0.9)

    def test_explicit_weight_version_is_preserved_even_when_weights_match_builtin(self):
        raw = payload()
        raw["metricWeights"] = dict(METRIC_PROFILES["coding"]["weights"])
        raw["metricWeightVersion"] = "team-approved-v1"
        result = plan_hierarchy(raw)
        self.assertEqual(result["profile"]["weightSetVersion"], "team-approved-v1")
        self.assertEqual(result["assignments"][0]["workerMetricWeightVersion"], "team-approved-v1")


if __name__ == "__main__":
    unittest.main()
