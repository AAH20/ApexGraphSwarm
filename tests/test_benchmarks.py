from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.benchmark_swarm import build_artifact, fixture_work, percentile, run_scenario


class BenchmarkFixtureTests(unittest.TestCase):
    def test_fixture_and_nearest_rank_percentiles_are_deterministic(self):
        payload = {"value": "seed:one", "rounds": 3}
        self.assertEqual(fixture_work(payload), fixture_work(payload))
        self.assertEqual(len(fixture_work(payload)["digest"]), 64)
        self.assertEqual(percentile([1, 2, 3, 4], 0.50), 2)
        self.assertEqual(percentile([1, 2, 3, 4], 0.95), 4)
        self.assertEqual(percentile([], 0.95), 0)

    def test_queue_benchmark_reopens_durable_store_and_recovers_expired_lease(self):
        with tempfile.TemporaryDirectory() as directory:
            row = run_scenario(10, workers_cap=4, tasks_per_agent=1,
                               task_delay_ms=0, db_dir=Path(directory), seed=11)
        self.assertEqual(row["completed"], row["taskCount"])
        self.assertEqual(row["failed"], 0)
        self.assertLessEqual(row["observedPeakActive"], row["activeWorkerLimit"])
        self.assertEqual(row["duplicateCompletions"], 0)
        self.assertTrue(row["restart"]["reopened"])
        self.assertGreater(row["restart"]["persistedCompleted"], 0)
        self.assertEqual(row["restart"]["leaseRecoveries"], 1)
        self.assertTrue(row["restart"]["staleLeaseFenced"])
        self.assertEqual(row["restart"]["recoveryTaskCompleted"], 1)
        self.assertTrue(row["cost"]["consistent"])
        self.assertEqual(row["cost"]["providerCalls"], 0)

    def test_all_logical_agent_tiers_fit_the_registry_and_remain_fixture_labeled(self):
        artifact = build_artifact(counts=(1, 10, 30, 100, 300), workers_cap=4,
                                  tasks_per_agent=1, task_delay_ms=0, seed=7)
        self.assertEqual([row["logicalAgents"] for row in artifact["scenarios"]], [1, 10, 30, 100, 300])
        self.assertTrue(all(row["completed"] == row["taskCount"] for row in artifact["scenarios"]))
        self.assertTrue(all(row["activeWorkerLimit"] <= 4 for row in artifact["scenarios"]))
        self.assertEqual(artifact["classification"], "deterministic_local_queue_fixture")
        self.assertTrue(all(target["status"] == "unmeasured" for target in artifact["proposedTargets"]))
        self.assertEqual(artifact["config"]["providerCalls"], 0)
        self.assertEqual(json.loads(json.dumps(artifact))["schemaVersion"], 1)

    def test_worker_cap_reflects_current_queue_limit(self):
        with self.assertRaisesRegex(ValueError, "maximum of 64"):
            build_artifact(counts=(1,), workers_cap=65)


if __name__ == "__main__":
    unittest.main()
