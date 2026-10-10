"""Example 60: Advanced - testing patterns.

Common testing patterns for ApexGraphSwarm components.
"""
import unittest
import tempfile
import time
from pathlib import Path
from apexgraphswarm.control import ControlStore, ControlError, ConflictError
from apexgraphswarm.analytics import build_analytics
from datetime import datetime, timezone

class TestControlStorePatterns(unittest.TestCase):
    """Reusable test patterns for ControlStore."""

    def setUp(self):
        self.store = ControlStore(":memory:")

    def tearDown(self):
        self.store.close()

    def create_simple_plan(self, **kwargs):
        """Helper to create a simple test plan."""
        return {
            "version": 1,
            "agents": [{"id": "test-agent"}],
            "tasks": [
                {
                    "id": "test-task",
                    "agentId": "test-agent",
                    "dependencies": [],
                    "payload": {"kind": "fixture"},
                    "reservedCostMicrousd": kwargs.get("cost", 0),
                    "maxAttempts": kwargs.get("max_attempts", 2),
                    "executionClass": "fixture",
                }
            ],
        }

    def test_create_and_complete_run(self):
        """Test basic run lifecycle."""
        plan = self.create_simple_plan()
        run = self.store.create_run(plan, idempotency_key="test-1", budget_microusd=0)
        run_id = run["run"]["id"]

        claim = self.store.claim(run_id, "worker-1")
        self.assertIsNotNone(claim)

        result = self.store.complete(claim["taskId"], claim["leaseToken"], {"ok": True}, 0)
        self.assertEqual(result["run"]["status"], "succeeded")

    def test_idempotency(self):
        """Test idempotent run creation."""
        plan = self.create_simple_plan()

        run1 = self.store.create_run(plan, idempotency_key="idem-1", budget_microusd=0)
        run2 = self.store.create_run(plan, idempotency_key="idem-1", budget_microusd=0)

        self.assertEqual(run1["run"]["id"], run2["run"]["id"])

    def test_budget_validation(self):
        """Test budget constraint enforcement."""
        plan = self.create_simple_plan(cost=1000)

        with self.assertRaises(ControlError):
            self.store.create_run(plan, idempotency_key="budget-1", budget_microusd=500)

    def test_dependency_ordering(self):
        """Test that dependencies are respected."""
        plan = {
            "version": 1,
            "agents": [{"id": "a"}],
            "tasks": [
                {"id": "first", "agentId": "a", "dependencies": [],
                 "payload": {}, "reservedCostMicrousd": 0, "maxAttempts": 1,
                 "executionClass": "fixture"},
                {"id": "second", "agentId": "a", "dependencies": ["first"],
                 "payload": {}, "reservedCostMicrousd": 0, "maxAttempts": 1,
                 "executionClass": "fixture"},
            ],
        }

        run = self.store.create_run(plan, idempotency_key="dep-1", budget_microusd=0)
        run_id = run["run"]["id"]

        # Should only get the first task
        claim = self.store.claim(run_id, "worker-1")
        self.assertEqual(claim["id"], "first")

        # Complete first, then second becomes available
        self.store.complete(claim["taskId"], claim["leaseToken"], {}, 0)
        claim2 = self.store.claim(run_id, "worker-1")
        self.assertEqual(claim2["id"], "second")

class TestAnalyticsPatterns(unittest.TestCase):
    """Reusable test patterns for analytics."""

    def test_demo_determinism(self):
        """Demo mode should produce identical results."""
        now = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)
        result1 = build_analytics({"source": "demo", "days": 30}, now=now)
        result2 = build_analytics({"source": "demo", "days": 30}, now=now)
        self.assertEqual(result1, result2)

    def test_import_validation(self):
        """Import should validate event structure."""
        now = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)
        with self.assertRaises(Exception):
            build_analytics({
                "source": "import",
                "days": 30,
                "rows": [{"invalid": "data"}],
            }, now=now)

if __name__ == "__main__":
    unittest.main()
