import unittest

from apexgraphswarm.access import AccessDenied
from apexgraphswarm.control import ControlStore


class FakeClock:
    def __init__(self, value=1000.0):
        self.value = value

    def __call__(self):
        return self.value


def paid_plan(*, tasks=1, cost=10):
    return {"version": 1, "agents": [{"id": "agent"}], "tasks": [
        {"id": f"task-{i}", "agentId": "agent", "dependencies": [],
         "payload": {}, "reservedCostMicrousd": cost,
         "executionClass": "external", "tool": "provider.invoke", "resource": "model:alpha"}
        for i in range(tasks)]}


class AccessTests(unittest.TestCase):
    def test_external_dispatch_fails_closed_for_missing_or_nonexact_grant(self):
        with ControlStore(":memory:") as store:
            run = store.create_run(paid_plan(), idempotency_key="scope", budget_microusd=10)
            run_id = run["run"]["id"]
            for kwargs in ({}, {"principal_id": "alice"}):
                with self.assertRaises(AccessDenied):
                    store.claim(run_id, "worker", **kwargs)
            store.grant_access(principal_id="alice", tool_id="provider.invoke",
                               resource_id="model:alpha", max_budget_microusd=9, expires_at=store._now() + 3600)
            with self.assertRaises(AccessDenied):
                store.claim(run_id, "worker", principal_id="alice")
            store.grant_access(principal_id="alice", tool_id="provider.invoke",
                               resource_id="model:beta", max_budget_microusd=10, expires_at=store._now() + 3600)
            with self.assertRaises(AccessDenied):
                store.claim(run_id, "worker", principal_id="alice")
            store.grant_access(principal_id="alice", tool_id="provider.invoke",
                               resource_id="model:alpha", max_budget_microusd=10, expires_at=store._now() + 3600)
            task = store.claim(run_id, "worker", principal_id="alice")
            self.assertEqual(task["tool"], "provider.invoke")
            self.assertEqual(task["resource"], "model:alpha")

    def test_expiry_and_revocation_are_checked_at_claim(self):
        clock = FakeClock()
        with ControlStore(":memory:", clock=clock) as store:
            run = store.create_run(paid_plan(), idempotency_key="expiry", budget_microusd=10)
            grant = store.grant_access(principal_id="alice", tool_id="provider.invoke",
                                       resource_id="model:alpha", max_budget_microusd=10,
                                       expires_at=1001)
            clock.value = 1001
            with self.assertRaises(AccessDenied):
                store.claim(run["run"]["id"], "worker", principal_id="alice")
            clock.value = 1000
            self.assertTrue(store.revoke_access(grant["grantId"]))
            self.assertFalse(store.revoke_access(grant["grantId"]))
            with self.assertRaises(AccessDenied):
                store.claim(run["run"]["id"], "worker", principal_id="alice")

    def test_cumulative_spend_cannot_reuse_grant_budget(self):
        with ControlStore(":memory:") as store:
            run = store.create_run(paid_plan(tasks=2, cost=5), idempotency_key="cumulative", budget_microusd=10)
            grant = store.grant_access(principal_id="alice", tool_id="provider.invoke",
                                       resource_id="model:alpha", max_budget_microusd=9, expires_at=store._now() + 3600)
            first = store.claim(run["run"]["id"], "worker", principal_id="alice")
            store.complete(first["taskId"], first["leaseToken"], {"ok": True}, 5)
            with store._transaction() as db:
                self.assertEqual(db.execute("SELECT spent_microusd FROM access_grants WHERE grant_id=?",
                                            (grant["grantId"],)).fetchone()[0], 5)
                db.execute("DELETE FROM execution_attempts WHERE task_id=?", (first["taskId"],))
            with self.assertRaises(AccessDenied):
                store.claim(run["run"]["id"], "worker", principal_id="alice")
            self.assertEqual(store.ledger(run["run"]["id"])["attempts"], [])
            with store._lock:
                self.assertEqual(store._db.execute("SELECT spent_microusd FROM access_grants WHERE grant_id=?",
                                                   (grant["grantId"],)).fetchone()[0], 5)



    def test_unresolved_expiry_reservation_survives_missing_receipt_row(self):
        clock = FakeClock()
        with ControlStore(":memory:", clock=clock) as store:
            run = store.create_run(paid_plan(tasks=2, cost=5), idempotency_key="unknown-budget", budget_microusd=10)
            grant = store.grant_access(principal_id="alice", tool_id="provider.invoke",
                                       resource_id="model:alpha", max_budget_microusd=9,
                                       expires_at=clock.value + 3600)
            first = store.claim(run["run"]["id"], "worker", principal_id="alice", lease_seconds=2)
            clock.value += 3
            store.recover_expired()
            with store._transaction() as db:
                self.assertEqual(db.execute("SELECT reserved_microusd FROM access_grants WHERE grant_id=?",
                                            (grant["grantId"],)).fetchone()[0], 5)
                db.execute("DELETE FROM execution_attempts WHERE task_id=?", (first["taskId"],))
            another = store.create_run(paid_plan(cost=5), idempotency_key="unknown-budget-2", budget_microusd=5)
            with self.assertRaises(AccessDenied):
                store.claim(another["run"]["id"], "worker-2", principal_id="alice")

    def test_claim_lease_is_capped_by_grant_expiry_and_heartbeat_rechecks_revocation(self):
        clock = FakeClock()
        with ControlStore(":memory:", clock=clock) as store:
            run = store.create_run(paid_plan(), idempotency_key="lease-bound", budget_microusd=10)
            grant = store.grant_access(principal_id="alice", tool_id="provider.invoke",
                                       resource_id="model:alpha", max_budget_microusd=10,
                                       expires_at=clock.value + 5)
            task = store.claim(run["run"]["id"], "worker", principal_id="alice", lease_seconds=30)
            self.assertEqual(task["leaseExpiresAt"], clock.value + 5)
            store.revoke_access(grant["grantId"])
            with self.assertRaises(AccessDenied):
                store.heartbeat(task["taskId"], task["leaseToken"], lease_seconds=30)

    def test_fixture_claim_needs_no_grant_but_external_missing_scope_cannot_claim(self):
        with ControlStore(":memory:") as store:
            fixture = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "fixture", "agentId": "a", "payload": {}, "reservedCostMicrousd": 0,
                 "executionClass": "fixture"}]}
            run = store.create_run(fixture, idempotency_key="fixture", budget_microusd=0)
            self.assertIsNotNone(store.claim(run["run"]["id"], "worker"))
            unscoped = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "external", "agentId": "a", "payload": {}, "reservedCostMicrousd": 0,
                 "executionClass": "external"}]}
            run = store.create_run(unscoped, idempotency_key="unscoped", budget_microusd=0)
            with self.assertRaises(AccessDenied):
                store.claim(run["run"]["id"], "worker", principal_id="alice")


if __name__ == "__main__":
    unittest.main()
