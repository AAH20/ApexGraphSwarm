import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

from apexgraphswarm.control import ControlError, ControlStore, ConflictError


class FakeClock:
    def __init__(self, value=1000.0):
        self.value = value

    def __call__(self):
        return self.value


def external_plan(tasks, *, opt_in=False):
    rows = []
    for task_id, resource, limit in tasks:
        row = {"id": task_id, "agentId": "worker", "dependencies": [],
               "payload": {"work": task_id}, "reservedCostMicrousd": 10,
               "executionClass": "external_idempotent", "tool": f"tool:{resource}",
               "resource": resource}
        if opt_in:
            row.update(requireResourceCapacity=True, resourceConcurrencyLimit=limit)
        rows.append(row)
    return {"version": 1, "agents": [{"id": "worker"}], "tasks": rows}


def start_run(store, plan, key):
    return store.create_run(plan, idempotency_key=key, budget_microusd=100)["run"]["id"]


def grant(store, worker, resource):
    store.grant_access(principal_id=worker, tool_id=f"tool:{resource}", resource_id=resource,
                       max_budget_microusd=100, expires_at=store._now() + 10_000)


class ResourceCapacityTests(unittest.TestCase):
    def test_opt_in_requires_admin_cap_and_plan_limit_is_enforced(self):
        with ControlStore(":memory:") as store:
            plan = external_plan([("a", "model-a", 1)], opt_in=True)
            with self.assertRaisesRegex(ControlError, "administrator-configured capacity"):
                start_run(store, plan, "needs-cap")
            store.configure_resource_capacity("model-a", 3)
            run_id = start_run(store, plan, "has-cap")
            grant(store, "alice", "model-a")
            first = store.claim(run_id, "alice", principal_id="alice")
            self.assertEqual(first["resourceConcurrencyLimit"], 1)
            # The run-level declaration is enforced even when the global cap is higher.
            next_task = external_plan([("first", "model-a", 1), ("second", "model-a", 1)], opt_in=True)
            # Use a fresh, separately admitted run so this checks the per-run
            # limit after the first task in that same run is claimed.
            run2 = start_run(store, next_task, "run-two")
            grant(store, "bob", "model-a")
            self.assertEqual(store.claim(run2, "bob", principal_id="bob")["id"], "first")
            self.assertIsNone(store.claim(run2, "bob", principal_id="bob"))

    def test_head_of_line_saturation_skips_to_another_resource(self):
        with ControlStore(":memory:") as store:
            store.configure_resource_capacity("hot", 1)
            blocker = start_run(store, external_plan([("block", "hot", None)]), "blocker")
            grant(store, "blocker", "hot")
            held = store.claim(blocker, "blocker", principal_id="blocker")
            self.assertEqual(held["resource"], "hot")

            eligible = start_run(store, external_plan([("first-hot", "hot", None),
                                                        ("second-cold", "cold", None)]), "eligible")
            grant(store, "next", "hot")
            grant(store, "next", "cold")
            claimed = store.claim(eligible, "next", principal_id="next")
            self.assertEqual(claimed["id"], "second-cold")

    def test_global_cap_is_atomic_across_store_connections(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "capacity.sqlite")
            stores = [ControlStore(path), ControlStore(path)]
            try:
                stores[0].configure_resource_capacity("shared", 1)
                runs = []
                for index, store in enumerate(stores):
                    run_id = start_run(store, external_plan([(f"t{index}", "shared", None)]), f"race-{index}")
                    worker = f"worker-{index}"
                    grant(store, worker, "shared")
                    runs.append((store, run_id, worker))
                barrier = Barrier(2)

                def compete(item):
                    store, run_id, worker = item
                    barrier.wait()
                    return store.claim(run_id, worker, principal_id=worker)

                with ThreadPoolExecutor(max_workers=2) as pool:
                    claims = list(pool.map(compete, runs))
                self.assertEqual(sum(claim is not None for claim in claims), 1)
            finally:
                for store in stores:
                    store.close()

    def test_expired_unknown_work_holds_capacity_until_reconciliation(self):
        clock = FakeClock()
        with ControlStore(":memory:", clock=clock) as store:
            store.configure_resource_capacity("remote", 2)
            runs = []
            for index in range(2):
                worker = f"worker-{index}"
                run_id = start_run(store, external_plan([(f"t{index}", "remote", None)]), f"expire-{index}")
                grant(store, worker, "remote")
                task = store.claim(run_id, worker, lease_seconds=1, principal_id=worker)
                runs.append((run_id, task, worker))
            clock.value += 2
            store.recover_expired()
            status = store.resource_capacity_status()
            self.assertEqual(status["resources"][0]["occupiedCount"], 2)
            with self.assertRaises(ConflictError):
                store.configure_resource_capacity("remote", 1)

            first_run, first, _worker = runs[0]
            store.reconcile(first["taskId"], outcome="failed", actual_cost_microusd=0)
            status = store.resource_capacity_status()
            self.assertEqual(status["resources"][0]["occupiedCount"], 1)
            store.configure_resource_capacity("remote", 1)
            blocked_run, _task, _worker = runs[1]
            self.assertIsNone(store.claim(blocked_run, "later", principal_id="worker-1"))

    def test_successful_unknown_cost_output_releases_active_slot(self):
        with ControlStore(":memory:") as store:
            store.configure_resource_capacity("remote", 1)
            run_id = start_run(store, external_plan([("t", "remote", None)]), "unknown-cost")
            grant(store, "worker", "remote")
            identity = store.enroll_worker(worker_id="worker", principal_id="worker",
                                           expires_at=store._now() + 1000)
            task = store.claim_authenticated(run_id, "worker", identity["credential"])
            store.complete_authenticated(task["taskId"], task["leaseToken"],
                                         identity["credential"], {"ok": True}, None)
            self.assertEqual(store.resource_capacity_status()["resources"][0]["occupiedCount"], 0)
            self.assertEqual(store.status(run_id)["tasks"][0]["status"], "needs_reconciliation")

    def test_task_id_filter_and_invalid_capacity_contract(self):
        with ControlStore(":memory:") as store:
            plan = {"version": 1, "agents": [{"id": "a"}], "tasks": [
                {"id": "one", "agentId": "a", "payload": {}, "reservedCostMicrousd": 0,
                 "executionClass": "fixture"},
                {"id": "two", "agentId": "a", "payload": {}, "reservedCostMicrousd": 0,
                 "executionClass": "fixture"},
            ]}
            run_id = start_run(store, plan, "task-filter")
            rows = store.status(run_id)["tasks"]
            second_id = next(row["taskId"] for row in rows if row["id"] == "two")
            claimed = store.claim(run_id, "worker", task_id=second_id)
            self.assertEqual(claimed["id"], "two")
            self.assertIsNone(store.claim(run_id, "worker", task_id="not-a-task"))
            for value in (True, 0, 10_001, "1"):
                with self.assertRaises(ControlError):
                    store.configure_resource_capacity("bad", value)
            bad = external_plan([("bad", "r", 1)], opt_in=True)
            bad["tasks"][0]["resourceConcurrencyLimit"] = True
            with self.assertRaises(ControlError):
                store.create_run(bad, idempotency_key="bad-limit", budget_microusd=100)
            bad = external_plan([("bad", "r", 1)], opt_in=True)
            bad["tasks"][0]["requireResourceCapacity"] = 1
            with self.assertRaises(ControlError):
                store.create_run(bad, idempotency_key="bad-flag", budget_microusd=100)


if __name__ == "__main__":
    unittest.main()
