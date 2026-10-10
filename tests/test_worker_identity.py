import hashlib
import json
import tempfile
import time
import unittest
from pathlib import Path

from apexgraphswarm.access import AccessDenied
from apexgraphswarm.control import ConflictError, ControlError, ControlStore, LeaseError


class FakeClock:
    def __init__(self, value=10_000.0):
        self.value = value

    def __call__(self):
        return self.value


def paid_plan(*, tasks=1, cost=10):
    return {"version": 1, "agents": [{"id": "agent"}], "tasks": [
        {"id": f"call-{index}", "agentId": "agent", "dependencies": [],
         "payload": {"jobId": f"job-{index}"}, "reservedCostMicrousd": cost,
         "executionClass": "external", "tool": "integration:forge:run",
         "resource": "repository:17"}
        for index in range(tasks)]}


def prepare(store, *, worker_id="worker-a", principal_id="principal-a", expiry=None):
    expiry = expiry if expiry is not None else store._now() + 10_000
    enrollment = store.enroll_worker(worker_id=worker_id, principal_id=principal_id,
                                     expires_at=expiry)
    store.grant_access(principal_id=principal_id, tool_id="integration:forge:run",
                       resource_id="repository:17", max_budget_microusd=100,
                       expires_at=expiry)
    run = store.create_run(paid_plan(), idempotency_key=f"run-{worker_id}", budget_microusd=10)
    return enrollment, run


class WorkerIdentityTests(unittest.TestCase):
    def test_enrollment_persists_only_hash_and_auth_claim_binds_principal(self):
        with ControlStore(":memory:") as store:
            enrollment, run = prepare(store)
            credential = enrollment["credential"]
            row = store._db.execute("SELECT * FROM workers WHERE worker_id='worker-a'").fetchone()
            self.assertNotIn(credential, tuple(row))
            self.assertEqual(row["token_hash"], hashlib.sha256(credential.encode()).hexdigest())
            claim = store.claim_authenticated(run["run"]["id"], "worker-a", credential)
            self.assertEqual(claim["workerId"], "worker-a")
            attempt = store.ledger(run["run"]["id"])["attempts"][0]
            self.assertEqual(attempt["principalId"], "principal-a")
            self.assertEqual(attempt["workerId"], "worker-a")
            self.assertNotIn(credential, json.dumps(store.status(run["run"]["id"])))


    def test_enrollment_and_grant_survive_database_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workers.sqlite3"
            store = ControlStore(path)
            enrollment = store.enroll_worker(worker_id="durable-worker", principal_id="durable-principal",
                                             expires_at=store._now() + 10_000)
            store.grant_access(principal_id="durable-principal", tool_id="integration:forge:run",
                               resource_id="repository:17", max_budget_microusd=10,
                               expires_at=store._now() + 10_000)
            run = store.create_run(paid_plan(), idempotency_key="durable-worker-run", budget_microusd=10)
            store.close()
            with ControlStore(path) as reopened:
                task = reopened.claim_authenticated(run["run"]["id"], "durable-worker",
                                                    enrollment["credential"])
                self.assertEqual(task["workerId"], "durable-worker")
                self.assertEqual(reopened.ledger(run["run"]["id"])["attempts"][0]["principalId"],
                                 "durable-principal")

    def test_missing_wrong_and_mismatched_credentials_fail_closed(self):
        with ControlStore(":memory:") as store:
            enrollment, run = prepare(store)
            run_id = run["run"]["id"]
            with self.assertRaises(AccessDenied):
                store.claim_authenticated(run_id, "worker-a", None)
            with self.assertRaises(AccessDenied):
                store.claim_authenticated(run_id, "worker-a", "z" * 43)
            with self.assertRaises(AccessDenied):
                store.claim_authenticated(run_id, "other-worker", enrollment["credential"])
            task = store.claim_authenticated(run_id, "worker-a", enrollment["credential"])
            with self.assertRaises(AccessDenied):
                store.heartbeat_authenticated(task["taskId"], task["leaseToken"], "z" * 43)
            with self.assertRaises(LeaseError):
                store.heartbeat_authenticated(task["taskId"], "wrong-lease-token", enrollment["credential"])
            store.complete_authenticated(task["taskId"], task["leaseToken"], enrollment["credential"], {}, 0)

    def test_lifecycle_is_bound_to_worker_and_lease(self):
        with ControlStore(":memory:") as store:
            worker_a, run = prepare(store)
            worker_b = store.enroll_worker(worker_id="worker-b", principal_id="principal-a",
                                           expires_at=store._now() + 10_000)
            task = store.claim_authenticated(run["run"]["id"], "worker-a", worker_a["credential"])
            with self.assertRaises(AccessDenied):
                store.complete_authenticated(task["taskId"], task["leaseToken"],
                                             worker_b["credential"], {"forged": True}, 0)
            with self.assertRaises(AccessDenied):
                store.fail_authenticated(task["taskId"], task["leaseToken"],
                                         worker_b["credential"], "forged", actual_cost_microusd=0)
            with self.assertRaises(AccessDenied):
                store.heartbeat_authenticated(task["taskId"], task["leaseToken"],
                                              worker_b["credential"])
            store.complete_authenticated(task["taskId"], task["leaseToken"],
                                         worker_a["credential"], {"ok": True}, 1)

    def test_revocation_and_expiry_block_dispatch_and_lease_updates(self):
        clock = FakeClock()
        with ControlStore(":memory:", clock=clock) as store:
            enrollment, run = prepare(store, expiry=clock.value + 100)
            task = store.claim_authenticated(run["run"]["id"], "worker-a", enrollment["credential"])
            self.assertTrue(store.revoke_worker("worker-a"))
            with self.assertRaises(AccessDenied):
                store.heartbeat_authenticated(task["taskId"], task["leaseToken"], enrollment["credential"])
            with self.assertRaises(AccessDenied):
                store.complete_authenticated(task["taskId"], task["leaseToken"], enrollment["credential"], {}, 0)
            self.assertFalse(store.revoke_worker("worker-a"))

        clock = FakeClock()
        with ControlStore(":memory:", clock=clock) as store:
            enrollment = store.enroll_worker(worker_id="expiring", principal_id="p",
                                             expires_at=clock.value + 5)
            run = store.create_run(paid_plan(), idempotency_key="expiring-run", budget_microusd=10)
            store.grant_access(principal_id="p", tool_id="integration:forge:run",
                               resource_id="repository:17", max_budget_microusd=10,
                               expires_at=clock.value + 100)
            task = store.claim_authenticated(run["run"]["id"], "expiring", enrollment["credential"],
                                             lease_seconds=30)
            self.assertEqual(task["leaseExpiresAt"], clock.value + 5)
            clock.value += 4
            renewed = store.heartbeat_authenticated(task["taskId"], task["leaseToken"],
                                                   enrollment["credential"], lease_seconds=30)
            self.assertEqual(renewed["leaseExpiresAt"], clock.value + 1)
            clock.value += 1
            with self.assertRaises(LeaseError):
                store.heartbeat_authenticated(task["taskId"], task["leaseToken"], enrollment["credential"])

    def test_unknown_cost_success_persists_output_until_admin_reconciliation(self):
        with ControlStore(":memory:") as store:
            enrollment, run = prepare(store)
            task = store.claim_authenticated(run["run"]["id"], "worker-a", enrollment["credential"])
            started = {"jobId": "job", "phase": "started"}
            checkpoint = store.checkpoint_authenticated(task["taskId"], task["leaseToken"],
                                                        enrollment["credential"], "call-1:started", started)
            same = store.checkpoint_authenticated(task["taskId"], task["leaseToken"],
                                                  enrollment["credential"], "call-1:started", started)
            self.assertFalse(checkpoint["duplicate"])
            self.assertTrue(same["duplicate"])
            with self.assertRaises(ConflictError):
                store.checkpoint_authenticated(task["taskId"], task["leaseToken"],
                                               enrollment["credential"], "call-1:started", {"changed": True})
            with self.assertRaises(ControlError):
                store.checkpoint_authenticated(task["taskId"], task["leaseToken"],
                                               enrollment["credential"], "bad", {"workerToken": "secret"})
            # Provider receipts may include a bounded token-usage summary,
            # but the exception does not permit arbitrary token metadata.
            usage = {"prompt": 12, "completion": 8, "total": 20,
                     "reasoning": None, "cachedPrompt": 3}
            store.checkpoint_authenticated(task["taskId"], task["leaseToken"],
                                           enrollment["credential"], "usage:receipt",
                                           {"receipt": {"tokenUsage": usage}})
            for bad_usage in ({"prompt": True}, {"prompt": -1},
                              {"prompt": 1, "accessToken": "secret"},
                              [{"prompt": 1}], {"unknown": 1}):
                with self.subTest(bad_usage=bad_usage), self.assertRaises(ControlError):
                    store.checkpoint_authenticated(task["taskId"], task["leaseToken"],
                                                   enrollment["credential"],
                                                   "usage:bad:" + str(len(str(bad_usage))),
                                                   {"tokenUsage": bad_usage})
            with self.assertRaises(ControlError):
                store.complete_authenticated(task["taskId"], task["leaseToken"],
                                             enrollment["credential"], {"body": enrollment["credential"]}, 0)
            receipt = {"jobId": "job", "phase": "receipt", "generated": {"answer": 42}}
            store.checkpoint_authenticated(task["taskId"], task["leaseToken"],
                                           enrollment["credential"], "call-1:receipt", receipt)
            unknown = store.complete_authenticated(task["taskId"], task["leaseToken"],
                                                   enrollment["credential"], receipt, None)
            stored_task = unknown["tasks"][0]
            self.assertEqual(stored_task["status"], "needs_reconciliation")
            self.assertEqual(stored_task["result"], receipt)
            self.assertEqual(unknown["run"]["reservedMicrousd"], 10)
            ledger = unknown["ledger"]
            self.assertEqual(ledger["unresolvedCostCount"], 1)
            self.assertIsNone(ledger["attempts"][0]["actualCostMicrousd"])
            checkpoints = store.read_checkpoints(task["taskId"], attempt=1)
            self.assertEqual(len(checkpoints["checkpoints"]), 3)
            with self.assertRaises(ConflictError):
                store.reconcile(task["taskId"], outcome="not_started", actual_cost_microusd=0)
            reconciled = store.reconcile(task["taskId"], outcome="succeeded",
                                         actual_cost_microusd=3)
            self.assertEqual(reconciled["tasks"][0]["result"], receipt)
            self.assertEqual(reconciled["run"]["spentMicrousd"], 3)
            self.assertEqual(reconciled["run"]["reservedMicrousd"], 0)

    def test_unknown_cost_authenticated_failure_clears_lease_and_replay_is_idempotent(self):
        with ControlStore(":memory:") as store:
            enrollment, run = prepare(store)
            task = store.claim_authenticated(run["run"]["id"], "worker-a", enrollment["credential"])
            first = store.fail_authenticated(task["taskId"], task["leaseToken"],
                                             enrollment["credential"], "provider cancelled",
                                             actual_cost_microusd=None)
            failed = first["tasks"][0]
            self.assertEqual(failed["status"], "needs_reconciliation")
            self.assertIsNone(failed["leaseExpiresAt"])
            self.assertEqual(first["run"]["reservedMicrousd"], 10)
            self.assertEqual(first["ledger"]["unresolvedCostCount"], 1)
            attempt = first["ledger"]["attempts"][0]
            self.assertEqual(attempt["outcome"], "unknown")
            self.assertIsNone(attempt["actualCostMicrousd"])

            replay = store.fail_authenticated(task["taskId"], task["leaseToken"],
                                              enrollment["credential"], "provider cancelled",
                                              actual_cost_microusd=None)
            self.assertEqual(replay["ledger"]["totalAttempts"], 1)
            self.assertEqual(replay["run"]["reservedMicrousd"], 10)
            with self.assertRaises(ConflictError):
                store.fail_authenticated(task["taskId"], "different-lease",
                                         enrollment["credential"], "provider cancelled",
                                         actual_cost_microusd=None)
            with self.assertRaises(ConflictError):
                store.fail_authenticated(task["taskId"], task["leaseToken"],
                                         enrollment["credential"], "different failure",
                                         actual_cost_microusd=None)
            with self.assertRaises(ConflictError):
                store.fail_authenticated(task["taskId"], task["leaseToken"],
                                         enrollment["credential"], "retry me", retryable=True,
                                         actual_cost_microusd=None)

            reconciled = store.reconcile(task["taskId"], outcome="failed",
                                         actual_cost_microusd=4)
            self.assertEqual(reconciled["tasks"][0]["status"], "failed")
            self.assertEqual(reconciled["run"]["spentMicrousd"], 4)
            self.assertEqual(reconciled["run"]["reservedMicrousd"], 0)

    def test_audit_checkpoint_remains_available_after_grant_revocation(self):
        with ControlStore(":memory:") as store:
            enrollment, run = prepare(store)
            task = store.claim_authenticated(run["run"]["id"], "worker-a", enrollment["credential"])
            grant_id = store.ledger(run["run"]["id"])["attempts"][0]["grantId"]
            self.assertTrue(store.revoke_access(grant_id))
            with self.assertRaises(AccessDenied):
                store.heartbeat_authenticated(task["taskId"], task["leaseToken"],
                                              enrollment["credential"])
            checkpoint = store.checkpoint_authenticated(task["taskId"], task["leaseToken"],
                                                        enrollment["credential"], "late:receipt",
                                                        {"phase": "receipt"})
            self.assertEqual(checkpoint["checkpointId"], "late:receipt")

    def test_checkpoint_id_count_and_total_byte_limits(self):
        with ControlStore(":memory:") as store:
            enrollment, run = prepare(store)
            task = store.claim_authenticated(run["run"]["id"], "worker-a", enrollment["credential"])
            for i in range(12):
                store.checkpoint_authenticated(task["taskId"], task["leaseToken"],
                                               enrollment["credential"], f"phase-{i}", {"value": "x"})
            with self.assertRaises(ControlError):
                store.checkpoint_authenticated(task["taskId"], task["leaseToken"],
                                               enrollment["credential"], "phase-13", {})

    def test_cli_requires_authenticated_transition_actions(self):
        from apexgraphswarm.control import _cli_request
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "control.sqlite3")
            with self.assertRaises(ControlError):
                _cli_request({"dbPath": path, "action": "claim", "runId": "r", "workerId": "w"})
            data = _cli_request({"dbPath": path, "action": "enrollWorker", "workerId": "w",
                                 "principalId": "p", "expiresAt": time.time() + 10_000})
            self.assertEqual(data["workerId"], "w")
            self.assertIn("credential", data)


if __name__ == "__main__":
    unittest.main()
