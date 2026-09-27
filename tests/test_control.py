import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from apexgraphswarm.control import (
    BudgetError,
    ConflictError,
    ControlError,
    ControlStore,
    LeaseError,
)


class FakeClock:
    def __init__(self, value=1000.0):
        self.value = value

    def __call__(self):
        return self.value


def simple_plan(*, cost=0, attempts=1):
    return {
        "version": 1,
        "agents": [{"id": "planner", "name": "Planner"}],
        "tasks": [{"id": "inspect", "agentId": "planner", "dependencies": [],
                   "payload": {"kind": "fixture"}, "reservedCostMicrousd": cost,
                   "maxAttempts": attempts, "executionClass": "fixture"}],
    }


def create_run(store, plan, *, idempotency_key, budget_microusd):
    for task in plan["tasks"]:
        if task.get("executionClass", "external") != "fixture":
            task.setdefault("tool", "test-tool")
            task.setdefault("resource", "test-resource")
    return store.create_run(plan, idempotency_key=idempotency_key, budget_microusd=budget_microusd)


def claim(store, run_id, worker_id, **kwargs):
    status = store.status(run_id)
    pending = next((task for task in status["tasks"] if task["status"] == "pending"), None)
    if pending and pending["executionClass"] != "fixture":
        store.grant_access(principal_id=worker_id, tool_id=pending["tool"],
                           resource_id=pending["resource"], max_budget_microusd=100_000,
                           expires_at=store._now() + 1000)
        kwargs["principal_id"] = worker_id
    return store.claim(run_id, worker_id, **kwargs)


class ControlStoreTests(unittest.TestCase):
    def test_dag_dependencies_idempotency_and_fenced_completion(self):
        with ControlStore(":memory:") as store:
            plan = {"version": 1, "agents": [{"id": "a"}, {"id": "b"}], "tasks": [
                {"id": "first", "agentId": "a", "dependencies": [], "payload": {"v": 1}, "reservedCostMicrousd": 0},
                {"id": "second", "agentId": "b", "dependencies": ["first"], "payload": {}, "reservedCostMicrousd": 0},
            ]}
            run = create_run(store, plan, idempotency_key="request-1", budget_microusd=0)
            same = create_run(store, plan, idempotency_key="request-1", budget_microusd=0)
            run_id = run["run"]["id"]
            self.assertEqual(same["run"]["id"], run_id)
            with self.assertRaises(ConflictError):
                create_run(store, simple_plan(), idempotency_key="request-1", budget_microusd=0)

            first = claim(store, run_id, "worker-1")
            self.assertEqual(first["id"], "first")
            self.assertIsNone(claim(store, run_id, "worker-2"))
            result = store.complete(first["taskId"], first["leaseToken"], {"ok": True}, 0)
            self.assertEqual(result["run"]["status"], "queued")
            with self.assertRaises(LeaseError):
                store.complete(first["taskId"], first["leaseToken"], {"duplicate": True}, 0)
            second = claim(store, run_id, "worker-2")
            self.assertEqual(second["id"], "second")
            final = store.complete(second["taskId"], second["leaseToken"], {"done": True}, 0)
            self.assertEqual(final["run"]["status"], "succeeded")
            self.assertEqual([e["type"] for e in final["events"]].count("task.completed"), 2)
            self.assertEqual(final["run"]["spentMicrousd"], 0)

    def test_rejects_missing_dependencies_cycles_and_unknown_paid_cost(self):
        with ControlStore(":memory:") as store:
            missing = simple_plan()
            missing["tasks"][0]["dependencies"] = ["absent"]
            with self.assertRaisesRegex(ControlError, "missing dependencies"):
                create_run(store, missing, idempotency_key="missing", budget_microusd=0)
            cycle = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "x", "agentId": "a", "dependencies": ["y"], "reservedCostMicrousd": 0},
                {"id": "y", "agentId": "a", "dependencies": ["x"], "reservedCostMicrousd": 0},
            ]}
            with self.assertRaisesRegex(ControlError, "cycle"):
                create_run(store, cycle, idempotency_key="cycle", budget_microusd=0)
            with self.assertRaises(BudgetError):
                create_run(store, simple_plan(cost=1), idempotency_key="unknown", budget_microusd=None)
            with self.assertRaises(BudgetError):
                create_run(store, simple_plan(cost=2), idempotency_key="underfunded", budget_microusd=1)
            secret_payload = simple_plan()
            secret_payload["tasks"][0]["payload"] = {"api_key": "should-not-be-persisted"}
            with self.assertRaisesRegex(ControlError, "secret references"):
                create_run(store, secret_payload, idempotency_key="secret-field", budget_microusd=0)

    def test_budget_reservation_retry_and_exact_settlement(self):
        with ControlStore(":memory:") as store:
            plan = simple_plan(cost=10, attempts=2)
            plan["tasks"][0]["executionClass"] = "external_idempotent"
            run = create_run(store, plan, idempotency_key="budget", budget_microusd=10)
            run_id = run["run"]["id"]
            first = claim(store, run_id, "worker-a")
            retried = store.fail(first["taskId"], first["leaseToken"], "transient", retryable=True,
                                 actual_cost_microusd=3)
            self.assertEqual(retried["tasks"][0]["status"], "pending")
            self.assertEqual(retried["run"]["spentMicrousd"], 3)
            self.assertEqual(retried["run"]["reservedMicrousd"], 7)
            second = claim(store, run_id, "worker-b")
            done = store.complete(second["taskId"], second["leaseToken"], {"ok": 1}, 7)
            self.assertEqual(done["run"]["spentMicrousd"], 10)
            self.assertEqual(done["run"]["remainingMicrousd"], 0)
            self.assertEqual(done["run"]["status"], "succeeded")

    def test_budget_settlement_rejects_cost_above_task_reservation(self):
        with ControlStore(":memory:") as store:
            plan = simple_plan(cost=3)
            plan["tasks"][0]["executionClass"] = "external"
            run = create_run(store, plan, idempotency_key="cost-limit", budget_microusd=3)
            task = claim(store, run["run"]["id"], "worker")
            breached = store.complete(task["taskId"], task["leaseToken"], {}, 4)
            self.assertEqual(breached["tasks"][0]["status"], "succeeded")
            self.assertEqual(breached["run"]["spentMicrousd"], 4)
            self.assertEqual(breached["run"]["remainingMicrousd"], -1)
            self.assertTrue(breached["run"]["budgetExceeded"])
            self.assertEqual(breached["run"]["status"], "budget_exceeded")

    def test_unknown_external_lease_expiry_retains_reservation_until_reconciled(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = FakeClock()
            path = Path(directory) / "ambiguous.sqlite3"
            store = ControlStore(path, clock=clock)
            plan = {"version": 1, "agents": [{"id": "reviewer"}], "tasks": [
                {"id": "paid-review", "agentId": "reviewer", "dependencies": [],
                 "payload": {"provider": "configured"}, "reservedCostMicrousd": 50,
                 "maxAttempts": 3, "executionClass": "external"},
            ]}
            run = create_run(store, plan, idempotency_key="ambiguous", budget_microusd=50)
            task = claim(store, run["run"]["id"], "worker", lease_seconds=2)
            store.close()

            clock.value += 3
            reopened = ControlStore(path, clock=clock)
            self.assertEqual(reopened.recover_expired(), {"requeued": 0, "failed": 0})
            pending = reopened.status(run["run"]["id"])
            self.assertEqual(pending["run"]["status"], "needs_reconciliation")
            self.assertEqual(pending["tasks"][0]["status"], "needs_reconciliation")
            self.assertEqual(pending["run"]["reservedMicrousd"], 50)
            self.assertIsNone(reopened.claim(run["run"]["id"], "replacement"))
            reconciled = reopened.reconcile(task["taskId"], outcome="succeeded",
                                            actual_cost_microusd=20, result={"summary": "reconciled"})
            self.assertEqual(reconciled["run"]["status"], "succeeded")
            self.assertEqual(reconciled["run"]["spentMicrousd"], 20)
            self.assertEqual(reconciled["run"]["reservedMicrousd"], 0)
            reopened.close()

    def test_cancel_of_external_running_task_retains_unknown_cost_and_fences_worker(self):
        with ControlStore(":memory:") as store:
            plan = {"version": 1, "agents": [{"id": "external"}], "tasks": [
                {"id": "call", "agentId": "external", "dependencies": [], "payload": {},
                 "reservedCostMicrousd": 8, "executionClass": "external"},
            ]}
            run = create_run(store, plan, idempotency_key="cancel-paid", budget_microusd=8)
            task = claim(store, run["run"]["id"], "worker")
            cancelled = store.cancel(run["run"]["id"])
            self.assertEqual(cancelled["run"]["status"], "needs_reconciliation")
            self.assertEqual(cancelled["run"]["reservedMicrousd"], 8)
            self.assertEqual(cancelled["tasks"][0]["status"], "needs_reconciliation")
            with self.assertRaises(LeaseError):
                store.complete(task["taskId"], task["leaseToken"], {}, 0)
            resolved = store.reconcile(task["taskId"], outcome="not_started", actual_cost_microusd=0)
            self.assertEqual(resolved["run"]["status"], "cancelled")
            self.assertEqual(resolved["run"]["reservedMicrousd"], 0)

    def test_external_retry_flag_requires_explicit_idempotency_class(self):
        with ControlStore(":memory:") as store:
            plan = {"version": 1, "agents": [{"id": "remote"}], "tasks": [
                {"id": "call", "agentId": "remote", "dependencies": [], "payload": {},
                 "reservedCostMicrousd": 10, "maxAttempts": 2, "executionClass": "external"},
            ]}
            run = create_run(store, plan, idempotency_key="unsafe-retry", budget_microusd=10)
            task = claim(store, run["run"]["id"], "worker")
            with self.assertRaises(ConflictError):
                store.fail(task["taskId"], task["leaseToken"], "uncertain", retryable=True,
                           actual_cost_microusd=0)

    def test_restart_expiry_recovery_and_old_token_fencing(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "control.sqlite3"
            clock = FakeClock()
            first_store = ControlStore(db_path, clock=clock)
            run = create_run(first_store, simple_plan(attempts=2), idempotency_key="restart", budget_microusd=0)
            first = claim(first_store, run["run"]["id"], "worker-old", lease_seconds=2)
            old_token = first["leaseToken"]
            first_store.close()

            clock.value += 3
            reopened = ControlStore(db_path, clock=clock)
            self.assertEqual(reopened.status(run["run"]["id"])["tasks"][0]["status"], "running")
            self.assertEqual(reopened.recover_expired(), {"requeued": 1, "failed": 0})
            current = reopened.claim(run["run"]["id"], "worker-new")
            self.assertEqual(current["attempts"], 2)
            with self.assertRaises(LeaseError):
                reopened.complete(current["taskId"], old_token, {}, 0)
            events = reopened.status(run["run"]["id"])["events"]
            self.assertIn("task.lease_expired", [event["type"] for event in events])
            self.assertTrue(current["claimedAt"])
            reopened.close()

    def test_active_lease_cap_is_separate_from_300_logical_agents_and_survives_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capacity.sqlite3"
            agents = [{"id": f"agent-{i:03d}"} for i in range(300)]
            tasks = [{"id": f"task-{i:03d}", "agentId": f"agent-{i:03d}",
                      "dependencies": [], "payload": {"ordinal": i}, "reservedCostMicrousd": 0}
                     for i in range(300)]
            plan = {"version": 1, "agents": agents, "tasks": tasks}
            with ControlStore(path, max_active=4, max_registered_agents=300) as store:
                run = create_run(store, plan, idempotency_key="logical-300", budget_microusd=0)
                run_id = run["run"]["id"]
                with ThreadPoolExecutor(max_workers=16) as pool:
                    claims = list(pool.map(lambda index: claim(store, run_id, f"worker-{index}"), range(16)))
                active = [claim for claim in claims if claim is not None]
                self.assertEqual(len(active), 4)
                status = store.status(run_id)
                self.assertEqual(len(status["agents"]), 300)
                self.assertEqual(sum(task["status"] == "running" for task in status["tasks"]), 4)
            with ControlStore(path, max_active=4) as reopened:
                status = reopened.status(run_id)
                self.assertEqual(len(status["agents"]), 300)
                self.assertEqual(sum(task["status"] == "running" for task in status["tasks"]), 4)
                self.assertEqual(sum(event["type"] == "task.claimed" for event in status["events"]), 4)

    def test_cancellation_fences_running_workers_and_clears_reservations(self):
        with ControlStore(":memory:") as store:
            run = create_run(store, simple_plan(cost=0), idempotency_key="cancel", budget_microusd=0)
            task = claim(store, run["run"]["id"], "worker")
            cancelled = store.cancel(run["run"]["id"])
            self.assertEqual(cancelled["run"]["status"], "cancelled")
            self.assertEqual(cancelled["run"]["reservedMicrousd"], 0)
            self.assertEqual(cancelled["tasks"][0]["status"], "cancelled")
            with self.assertRaises(LeaseError):
                store.complete(task["taskId"], task["leaseToken"], {}, 0)

    def test_recovery_does_not_retry_after_attempt_limit(self):
        with ControlStore(":memory:") as store:
            run = create_run(store, simple_plan(attempts=1), idempotency_key="no-retry", budget_microusd=0)
            task = claim(store, run["run"]["id"], "worker", lease_seconds=1)
            self.assertEqual(store.recover_expired(now=task["leaseExpiresAt"] + 1), {"requeued": 0, "failed": 1})
            status = store.status(run["run"]["id"])
            self.assertEqual(status["run"]["status"], "failed")
            self.assertEqual(status["tasks"][0]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
