import tempfile
import unittest
from pathlib import Path

from apexgraphswarm.control import ControlStore


class FakeClock:
    def __init__(self, value=1000.0):
        self.value = value

    def __call__(self):
        return self.value


class LedgerTests(unittest.TestCase):
    def test_failure_retry_receipts_are_stable_and_costs_are_attributable(self):
        with ControlStore(":memory:") as store:
            plan = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "paid", "agentId": "a", "payload": {}, "reservedCostMicrousd": 10,
                 "maxAttempts": 2, "executionClass": "external_idempotent",
                 "tool": "provider.invoke", "resource": "model:alpha"}]}
            run = store.create_run(plan, idempotency_key="retry-ledger", budget_microusd=10)
            grant = store.grant_access(principal_id="alice", tool_id="provider.invoke",
                                       resource_id="model:alpha", max_budget_microusd=10, expires_at=store._now() + 3600)
            first = store.claim(run["run"]["id"], "worker-1", principal_id="alice")
            store.fail(first["taskId"], first["leaseToken"], "provider timeout", retryable=True,
                       actual_cost_microusd=2)
            second = store.claim(run["run"]["id"], "worker-2", principal_id="alice")
            store.complete(second["taskId"], second["leaseToken"], {"ok": True}, 4)
            ledger = store.ledger(run["run"]["id"])
            self.assertEqual(ledger["knownActualMicrousd"], 6)
            self.assertTrue(ledger["allCostsResolved"])
            self.assertEqual([a["outcome"] for a in ledger["attempts"]], ["failed", "succeeded"])
            self.assertEqual([a["actualCostMicrousd"] for a in ledger["attempts"]], [2, 4])
            self.assertEqual([a["grantId"] for a in ledger["attempts"]], [grant["grantId"]] * 2)
            self.assertEqual([a["tool"] for a in ledger["attempts"]], ["provider.invoke"] * 2)
            self.assertEqual([a["resource"] for a in ledger["attempts"]], ["model:alpha"] * 2)
            self.assertEqual(len({a["attemptId"] for a in ledger["attempts"]}), 2)

    def test_expired_external_lease_keeps_cost_null_until_reconciled(self):
        clock = FakeClock()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.sqlite3"
            store = ControlStore(path, clock=clock)
            plan = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "paid", "agentId": "a", "payload": {}, "reservedCostMicrousd": 10,
                 "executionClass": "external", "tool": "provider.invoke", "resource": "model:alpha"}]}
            run = store.create_run(plan, idempotency_key="unknown-ledger", budget_microusd=10)
            store.grant_access(principal_id="alice", tool_id="provider.invoke",
                               resource_id="model:alpha", max_budget_microusd=10, expires_at=store._now() + 3600)
            claim = store.claim(run["run"]["id"], "worker", principal_id="alice", lease_seconds=2)
            store.close()
            clock.value += 3
            with ControlStore(path, clock=clock) as reopened:
                reopened.recover_expired()
                pending = reopened.ledger(run["run"]["id"])
                self.assertEqual(pending["unresolvedCostCount"], 1)
                self.assertIsNone(pending["attempts"][0]["actualCostMicrousd"])
                self.assertFalse(pending["allCostsResolved"])
                reconciled = reopened.reconcile(claim["taskId"], outcome="succeeded",
                                                actual_cost_microusd=3, result={"ok": True})
                self.assertEqual(reconciled["run"]["spentMicrousd"], 3)
                final = reopened.ledger(run["run"]["id"])
                self.assertEqual(final["unresolvedCostCount"], 0)
                self.assertEqual(final["attempts"][0]["actualCostMicrousd"], 3)
                self.assertEqual(final["attempts"][0]["receipt"]["outcome"], "succeeded")

    def test_ledger_read_is_bounded_and_status_contains_summary(self):
        with ControlStore(":memory:") as store:
            plan = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "fixture", "agentId": "a", "payload": {}, "reservedCostMicrousd": 0,
                 "executionClass": "fixture"}]}
            run = store.create_run(plan, idempotency_key="summary", budget_microusd=0)
            task = store.claim(run["run"]["id"], "worker")
            store.complete(task["taskId"], task["leaseToken"], {}, 0)
            self.assertIn("ledger", store.status(run["run"]["id"]))
            self.assertEqual(store.ledger(run["run"]["id"], limit=1)["returnedAttempts"], 1)
            with self.assertRaises(ValueError):
                store.ledger(limit=0)


if __name__ == "__main__":
    unittest.main()
