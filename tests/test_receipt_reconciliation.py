from __future__ import annotations

import hashlib
import json
import tempfile
import unittest

from apexgraphswarm.control import ConflictError, ControlError, ControlStore
from apexgraphswarm.provider_receipts import normalize_openrouter_receipt
from apexgraphswarm.receipt_reconciliation import reconcile_openrouter_task


TOOL = "integration:openrouter:review"
RESOURCE = "model:openrouter/test-model"


class ReceiptReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_800_000_000.0
        self.store = ControlStore(":memory:", clock=lambda: self.now)
        self.worker = self.store.enroll_worker(
            worker_id="worker-a", principal_id="principal-a", expires_at=self.now + 3600)
        self.grant = self.store.grant_access(
            principal_id="principal-a", tool_id=TOOL, resource_id=RESOURCE,
            max_budget_microusd=10_000, expires_at=self.now + 3600)
        self.run = self.store.create_run(self._plan(), idempotency_key="test-run", budget_microusd=10_000)
        self.task_id = self.run["tasks"][0]["taskId"]

    def tearDown(self):
        self.store.close()

    @staticmethod
    def _plan(*, max_attempts=1):
        return {
            "version": 1,
            "agents": [{"id": "reviewer", "name": "Review"}],
            "tasks": [{"id": "review", "agentId": "reviewer", "tool": TOOL,
                       "resource": RESOURCE, "executionClass": "external_idempotent",
                       "reservedCostMicrousd": 1_000, "maxAttempts": max_attempts,
                       "payload": {"goal": "review bounded graph metadata"}}],
        }

    def _claim(self):
        return self.store.claim_authenticated(self.run["run"]["id"], "worker-a", self.worker["credential"],
                                              agent_id="reviewer")

    def _record_call(self, claim, call_id="call-a", generation_id="gen-a", model="test-model"):
        self.store.checkpoint_authenticated(
            self.task_id, claim["leaseToken"], self.worker["credential"], call_id + ":started",
            {"callId": call_id, "provider": "openrouter", "model": model, "phase": "started"})
        self.store.checkpoint_authenticated(
            self.task_id, claim["leaseToken"], self.worker["credential"], call_id + ":receipt",
            {"callId": call_id, "provider": "openrouter", "model": model,
             "generationId": generation_id, "costUsd": None, "costMicrousd": None})

    @staticmethod
    def _entry(attempt=1, call_id="call-a", generation_id="gen-a", model="test-model", cost="0.0000004"):
        return {"attempt": attempt, "callId": call_id,
                "payload": {"id": generation_id, "model": model,
                            "usage": {"cost": cost, "prompt_tokens": 3,
                                      "completion_tokens": 1, "total_tokens": 4}}}

    def _unknown_success(self, claim, result=None):
        return self.store.complete_authenticated(
            self.task_id, claim["leaseToken"], self.worker["credential"],
            result or {"summary": "preserved output", "findings": []}, None)

    def test_reconciliation_preserves_output_and_audits_operator_assertion(self):
        claim = self._claim()
        self._record_call(claim)
        self._unknown_success(claim)

        status = reconcile_openrouter_task(self.store, self.task_id,
                                           [self._entry()], operator_id="alice")
        task = status["tasks"][0]
        self.assertEqual(task["status"], "succeeded")
        self.assertEqual(task["result"], {"summary": "preserved output", "findings": []})
        self.assertEqual(task["actualCostMicrousd"], 1)
        audit = self.store.receipt_reconciliation(self.task_id)
        self.assertEqual(audit["provenance"], "trusted_local_operator_assertion")
        self.assertEqual(audit["operatorId"], "alice")
        self.assertEqual(audit["receipts"][0]["receipt"]["costUsd"], "0.0000004")

    def test_missing_call_and_mismatched_identity_leave_liability_unsettled(self):
        claim = self._claim()
        self._record_call(claim, "call-a", "gen-a")
        self._record_call(claim, "call-b", "gen-b")
        self._unknown_success(claim)

        with self.assertRaises(ControlError):
            reconcile_openrouter_task(self.store, self.task_id,
                                      [self._entry(call_id="call-a")], operator_id="alice")
        with self.assertRaises(ControlError):
            reconcile_openrouter_task(self.store, self.task_id,
                                      [self._entry(call_id="call-a"),
                                       self._entry(call_id="call-b", generation_id="wrong")],
                                      operator_id="alice")
        with self.assertRaises(ControlError):
            reconcile_openrouter_task(self.store, self.task_id,
                                      [self._entry(call_id="call-a"),
                                       self._entry(call_id="call-b", generation_id="gen-b",
                                                   model="different-model")],
                                      operator_id="alice")
        current = self.store.status(self.run["run"]["id"])
        self.assertEqual(current["tasks"][0]["status"], "needs_reconciliation")
        self.assertEqual(current["run"]["spentMicrousd"], 0)
        self.assertIsNone(self.store.receipt_reconciliation(self.task_id))

    def test_missing_saved_generation_id_is_never_inferred_from_supplied_receipt(self):
        claim = self._claim()
        self._record_call(claim, generation_id=None)
        self._unknown_success(claim)
        with self.assertRaises(ControlError):
            reconcile_openrouter_task(self.store, self.task_id,
                                      [self._entry(generation_id="gen-a")], operator_id="alice")
        self.assertEqual(self.store.status(self.run["run"]["id"])["tasks"][0]["status"],
                         "needs_reconciliation")

    def test_identical_replay_is_idempotent_and_changed_evidence_conflicts(self):
        claim = self._claim()
        self._record_call(claim)
        self._unknown_success(claim)
        entries = [self._entry()]
        first = reconcile_openrouter_task(self.store, self.task_id, entries, operator_id="alice")
        replay = reconcile_openrouter_task(self.store, self.task_id, entries, operator_id="alice")
        self.assertEqual(first, replay)
        self.assertEqual(self.store.status(self.run["run"]["id"])["run"]["spentMicrousd"], 1)
        with self.assertRaises(ConflictError):
            reconcile_openrouter_task(self.store, self.task_id,
                                      [self._entry(cost="0.0000005")], operator_id="alice")
        self.assertEqual(self.store.status(self.run["run"]["id"])["run"]["spentMicrousd"], 1)

    def test_known_failed_attempt_is_not_charged_twice_when_retry_is_unresolved(self):
        self.store.close()
        self.store = ControlStore(":memory:", clock=lambda: self.now)
        self.worker = self.store.enroll_worker(
            worker_id="worker-a", principal_id="principal-a", expires_at=self.now + 3600)
        self.grant = self.store.grant_access(
            principal_id="principal-a", tool_id=TOOL, resource_id=RESOURCE,
            max_budget_microusd=10_000, expires_at=self.now + 3600)
        self.run = self.store.create_run(self._plan(max_attempts=2), idempotency_key="retry-run",
                                         budget_microusd=10_000)
        self.task_id = self.run["tasks"][0]["taskId"]

        first = self._claim()
        self._record_call(first, "call-first", "gen-first")
        self.store.fail_authenticated(self.task_id, first["leaseToken"], self.worker["credential"],
                                      "provider request failed after usage was returned", retryable=True,
                                      actual_cost_microusd=1)
        second = self._claim()
        self._record_call(second, "call-second", "gen-second")
        self._unknown_success(second, {"summary": "retry output", "findings": []})

        result = reconcile_openrouter_task(
            self.store, self.task_id,
            [self._entry(1, "call-first", "gen-first", cost="0.0000004"),
             self._entry(2, "call-second", "gen-second", cost="0.0000012")],
            operator_id="alice")
        self.assertEqual(result["tasks"][0]["actualCostMicrousd"], 3)
        self.assertEqual(result["run"]["spentMicrousd"], 3)
        ledger = self.store.ledger(self.run["run"]["id"])
        settled = {row["attempt"]: row["actualCostMicrousd"] for row in ledger["attempts"]}
        self.assertEqual(settled, {1: 1, 2: 2})
        self.assertEqual(result["tasks"][0]["result"], {"summary": "retry output", "findings": []})

    def _second_task(self, suffix="second"):
        run = self.store.create_run(self._plan(), idempotency_key=f"{suffix}-run",
                                    budget_microusd=10_000)
        task_id = run["tasks"][0]["taskId"]
        claim = self.store.claim_authenticated(run["run"]["id"], "worker-a",
                                               self.worker["credential"], agent_id="reviewer")
        return run, task_id, claim

    def test_duplicate_generation_across_two_calls_in_one_task_is_rejected(self):
        claim = self._claim()
        self._record_call(claim, "call-a", "gen-shared")
        with self.assertRaises(ConflictError):
            self._record_call(claim, "call-b", "gen-shared")
        checkpoints = self.store.read_checkpoints(self.task_id, attempt=1)["checkpoints"]
        self.assertNotIn("call-b:receipt", [row["checkpointId"] for row in checkpoints])

    def test_duplicate_generation_across_tasks_is_rejected(self):
        first = self._claim()
        self._record_call(first, "call-first", "gen-shared")
        _, second_task_id, second = self._second_task("cross-task")
        with self.assertRaises(ConflictError):
            self._record_call_for(second_task_id, second, "call-second", "gen-shared")
        ids = [row["checkpointId"] for row in self.store.read_checkpoints(second_task_id, attempt=1)["checkpoints"]]
        self.assertIn("call-second:started", ids)
        self.assertNotIn("call-second:receipt", ids)

    def test_settled_checkpoint_generation_cannot_be_reused_by_later_reconciliation(self):
        first = self._claim()
        self._record_call(first, "call-settled", "gen-settled")
        self.store.complete_authenticated(self.task_id, first["leaseToken"],
                                          self.worker["credential"],
                                          {"summary": "known-cost result"}, 5)
        _, second_task_id, second = self._second_task("settled-owner")
        with self.assertRaises(ConflictError):
            self._record_call_for(second_task_id, second, "call-reconcile", "gen-settled")
        self.assertEqual(self.store.provider_receipt_context(second_task_id)["status"], "running")

    def _record_call_for(self, task_id, claim, call_id, generation_id, model="test-model"):
        self.store.checkpoint_authenticated(
            task_id, claim["leaseToken"], self.worker["credential"], call_id + ":started",
            {"callId": call_id, "provider": "openrouter", "model": model, "phase": "started"})
        self.store.checkpoint_authenticated(
            task_id, claim["leaseToken"], self.worker["credential"], call_id + ":receipt",
            {"callId": call_id, "provider": "openrouter", "model": model,
             "generationId": generation_id, "costUsd": None, "costMicrousd": None})

    def test_ambiguous_legacy_generation_history_fails_closed_on_every_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            path = f"{directory}/control.sqlite3"
            store = ControlStore(path, clock=lambda: self.now)
            worker = store.enroll_worker(worker_id="legacy-worker", principal_id="legacy-principal",
                                         expires_at=self.now + 3600)
            store.grant_access(principal_id="legacy-principal", tool_id=TOOL,
                               resource_id=RESOURCE, max_budget_microusd=10_000,
                               expires_at=self.now + 3600)
            plan = {"version": 1, "agents": [{"id": "reviewer"}], "tasks": [
                {"id": key, "agentId": "reviewer", "tool": TOOL, "resource": RESOURCE,
                 "executionClass": "external", "reservedCostMicrousd": 1_000,
                 "payload": {}} for key in ("legacy-a", "legacy-b")]}
            run = store.create_run(plan, idempotency_key="legacy-run", budget_microusd=2_000)
            first = store.claim_authenticated(run["run"]["id"], "legacy-worker", worker["credential"],
                                              agent_id="reviewer")
            first_id = first["taskId"]
            self._record_with(store, worker["credential"], first_id, first,
                              "legacy-call-a", "gen-legacy-duplicate")
            store.complete_authenticated(first_id, first["leaseToken"], worker["credential"],
                                         {"summary": "settled"}, 5)
            normalized = normalize_openrouter_receipt(
                {"id": "gen-legacy-duplicate", "model": "test-model",
                 "usage": {"cost": "0.000005", "prompt_tokens": 1,
                           "completion_tokens": 1, "total_tokens": 2}},
                expected_generation_id="gen-legacy-duplicate", expected_model="test-model")
            evidence = {"provenance": "trusted_local_operator_assertion",
                        "operatorId": "legacy-operator", "provider": "openrouter",
                        "receipts": [{"attempt": 1, "callId": "legacy-call-a",
                                      "receipt": normalized}]}
            evidence_json = json.dumps(evidence, sort_keys=True, separators=(",", ":"))
            store._db.execute(
                "INSERT INTO provider_receipt_reconciliations(task_id,run_id,evidence_sha256,evidence_json,created_at) VALUES(?,?,?,?,?)",
                (first_id, run["run"]["id"], hashlib.sha256(evidence_json.encode()).hexdigest(),
                 evidence_json, self.now))
            # Simulate old state with a valid settled audit but missing response
            # checkpoint. Its provider generation must still remain owned.
            store._db.execute("DELETE FROM worker_checkpoints WHERE task_id=? AND checkpoint_id=?",
                              (first_id, "legacy-call-a:receipt"))
            second = store.claim_authenticated(run["run"]["id"], "legacy-worker", worker["credential"],
                                               agent_id="reviewer")
            second_id = second["taskId"]
            store.checkpoint_authenticated(second_id, second["leaseToken"], worker["credential"],
                                           "legacy-call-b:started",
                                           {"callId": "legacy-call-b", "provider": "openrouter",
                                            "model": "test-model", "phase": "started"})
            # Construct an on-disk pre-migration duplicate, which the current
            # checkpoint API correctly refuses to create.
            legacy_value = {"callId": "legacy-call-b", "provider": "openrouter",
                            "model": "test-model", "generationId": "gen-legacy-duplicate",
                            "costUsd": None, "costMicrousd": None}
            encoded = json.dumps(legacy_value, sort_keys=True, separators=(",", ":"))
            digest = hashlib.sha256(encoded.encode()).hexdigest()
            store._db.execute("DELETE FROM provider_generation_ownership")
            store._db.execute("DELETE FROM control_meta WHERE key='provider_generation_ownership_migrated'")
            store._db.execute(
                "INSERT INTO worker_checkpoints(task_id,run_id,attempt_number,worker_id,checkpoint_id,value_json,value_sha256,byte_length,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (second_id, run["run"]["id"], 1, "legacy-worker", "legacy-call-b:receipt",
                 encoded, digest, len(encoded.encode()), self.now))
            store.close()
            for _ in range(2):
                with self.assertRaisesRegex(ControlError, "already bound|ambiguous"):
                    ControlStore(path, clock=lambda: self.now)

    def _record_with(self, store, credential, task_id, claim, call_id, generation_id):
        store.checkpoint_authenticated(
            task_id, claim["leaseToken"], credential, call_id + ":started",
            {"callId": call_id, "provider": "openrouter", "model": "test-model", "phase": "started"})
        store.checkpoint_authenticated(
            task_id, claim["leaseToken"], credential, call_id + ":receipt",
            {"callId": call_id, "provider": "openrouter", "model": "test-model",
             "generationId": generation_id, "costUsd": None, "costMicrousd": None})


if __name__ == "__main__":
    unittest.main()
