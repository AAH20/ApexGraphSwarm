import json
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from apexgraphswarm.control import ControlStore
from apexgraphswarm.execution_graph import (
    main,
    project_execution_graph,
    read_only_execution_graph,
)


class ExecutionGraphTests(unittest.TestCase):
    def _run(self, store, *, unknown=False):
        plan = {
            "version": 1,
            "agents": [{"id": "planner", "name": "Planner"}],
            "tasks": [
                {"id": "first", "agentId": "planner", "dependencies": [],
                 "payload": {"prompt": "sensitive payload"}, "reservedCostMicrousd": 0,
                 "executionClass": "fixture"},
                {"id": "second", "agentId": "planner", "dependencies": ["first"],
                 "payload": {"resultSecret": "sensitive result"}, "reservedCostMicrousd": 0,
                 "executionClass": "fixture"},
            ],
        }
        created = store.create_run(plan, idempotency_key="graph-fixture", budget_microusd=140)
        run_id = created["run"]["id"]
        first = store.claim(run_id, "worker-1")
        if unknown:
            store._db.execute("UPDATE execution_attempts SET outcome='unknown',actual_cost_microusd=NULL "
                              "WHERE task_id=?", (first["taskId"],))
            store._db.execute("UPDATE tasks SET status='needs_reconciliation',worker_id=NULL,lease_token=NULL "
                              "WHERE task_id=?", (first["taskId"],))
        else:
            store.complete(first["taskId"], first["leaseToken"], {"hidden": "output"}, 0)
        if not unknown:
            second = store.claim(run_id, "worker-2")
            store.complete(second["taskId"], second["leaseToken"], {"ok": True}, 0)
        return run_id

    def test_actual_control_store_projects_dependency_attempt_attribution_and_redacts_bodies(self):
        with ControlStore(":memory:") as store:
            run_id = self._run(store)
            status = store.status(run_id)
            graph = project_execution_graph(status)
            self.assertEqual(graph["version"], 1)
            kinds = {node["kind"] for node in graph["nodes"]}
            self.assertTrue({"run", "task", "attempt", "agent", "worker"}.issubset(kinds))
            edge_kinds = {edge["kind"] for edge in graph["edges"]}
            self.assertTrue({"dependency", "assigned", "attempt_of", "executed"}.issubset(edge_kinds))
            task_nodes = {node["label"]: node for node in graph["nodes"] if node["kind"] == "task"}
            self.assertEqual(task_nodes["first"]["actualMicrousd"], 0)
            self.assertEqual(task_nodes["second"]["actualMicrousd"], 0)
            encoded = json.dumps(graph)
            self.assertNotIn("sensitive payload", encoded)
            self.assertNotIn("sensitive result", encoded)
            self.assertNotIn("hidden", encoded)
            self.assertNotIn("leaseToken", encoded)
            self.assertTrue(graph["summary"]["attemptCoverage"]["complete"])
            self.assertTrue(graph["summary"]["allCostsResolved"])

    def test_pending_resource_edges_explain_saturated_capacity_without_payloads(self):
        with ControlStore(":memory:", clock=lambda: 100) as store:
            store.configure_resource_capacity("model:shared", 1)
            store.grant_access(principal_id="principal", tool_id="review", resource_id="model:shared",
                               max_budget_microusd=20, expires_at=200)
            plan = {"version": 1, "agents": [{"id": "reviewer"}], "tasks": [
                {"id": name, "agentId": "reviewer", "payload": {"prompt": "private input"},
                 "executionClass": "external", "tool": "review", "resource": "model:shared",
                 "reservedCostMicrousd": 10, "requireResourceCapacity": True,
                 "resourceConcurrencyLimit": 1} for name in ("first", "second")]}
            run = store.create_run(plan, idempotency_key="capacity-graph", budget_microusd=20)["run"]["id"]
            store.claim(run, "worker", principal_id="principal")
            graph = project_execution_graph(store.status(run))
            pending = next(node for node in graph["nodes"] if node["kind"] == "task" and node["status"] == "pending")
            self.assertEqual(pending["details"]["resourceCapacity"]["availableCount"], 0)
            self.assertTrue(any("No resource slot" in text for text in pending["explanations"]))
            self.assertTrue(any(edge["source"] == pending["id"] and edge["kind"] == "requires_resource"
                                for edge in graph["edges"]))
            self.assertNotIn("private input", json.dumps(graph))

    def test_unknown_liability_remains_unknown_and_not_zero(self):
        with ControlStore(":memory:") as store:
            run_id = self._run(store, unknown=True)
            graph = project_execution_graph(store.status(run_id))
            first = next(node for node in graph["nodes"]
                         if node["kind"] == "task" and node["label"] == "first")
            attempt = next(node for node in graph["nodes"] if node["kind"] == "attempt")
            self.assertIsNone(first.get("actualMicrousd"))
            self.assertIsNone(attempt.get("actualMicrousd"))
            self.assertEqual(attempt["details"]["costState"], "unknown")
            self.assertFalse(graph["summary"]["allCostsResolved"])
            self.assertEqual(graph["summary"]["unknownCostAttempts"], 1)

    def test_missing_legacy_attempt_is_not_fabricated(self):
        with ControlStore(":memory:") as store:
            run_id = self._run(store)
            status = store.status(run_id)
            first_id = next(task["taskId"] for task in status["tasks"] if task["id"] == "first")
            store._db.execute("DELETE FROM execution_attempts WHERE task_id=?", (first_id,))
            status = store.status(run_id)
            graph = project_execution_graph(status)
            self.assertEqual(sum(node["kind"] == "attempt" for node in graph["nodes"]), 1)
            self.assertFalse(graph["summary"]["attemptCoverage"]["complete"])
            self.assertEqual(graph["summary"]["attemptCoverage"]["missing"], 1)
            first = next(node for node in graph["nodes"]
                         if node["kind"] == "task" and node["label"] == "first")
            self.assertIsNone(first.get("actualMicrousd"))

    def test_bounds_drop_dangling_edges_and_report_truncation(self):
        with ControlStore(":memory:") as store:
            run_id = self._run(store)
            graph = project_execution_graph(store.status(run_id), max_nodes=2, max_edges=1)
            self.assertEqual(len(graph["nodes"]), 2)
            self.assertTrue(graph["truncated"])
            kept = {node["id"] for node in graph["nodes"]}
            self.assertTrue(all(edge["source"] in kept and edge["target"] in kept
                                for edge in graph["edges"]))
            self.assertGreater(graph["summary"]["omittedNodes"], 0)

    def test_read_only_cli_projection_reads_existing_database(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "control.sqlite"
            with ControlStore(path) as store:
                run_id = self._run(store)
            graph = read_only_execution_graph(str(path), run_id)
            self.assertIsNotNone(graph)
            self.assertEqual(graph["runId"], run_id)
            self.assertIsNone(read_only_execution_graph(str(path), "missing"))

    def test_cli_accepts_bounded_server_supplied_stdin_request(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "control.sqlite"
            with ControlStore(path) as store:
                run_id = self._run(store)
            output = io.StringIO()
            with patch("sys.stdin", io.StringIO(json.dumps({"dbPath": str(path), "runId": run_id}))), \
                    patch("sys.stdout", output):
                self.assertEqual(main([]), 0)
            graph = json.loads(output.getvalue())
            self.assertEqual(graph["runId"], run_id)

    def test_strict_bounds_and_source_shapes(self):
        with self.assertRaises(ValueError):
            project_execution_graph({"run": {"id": "r"}, "tasks": "bad"})
        with self.assertRaises(ValueError):
            project_execution_graph({"run": {"id": "r"}}, max_nodes=True)
        with self.assertRaises(ValueError):
            project_execution_graph({"run": {"id": "r"}}, max_edges=-1)

    def test_specialist_contract_is_bound_provenance_without_reviewed_input(self):
        secret = "DO_NOT_EXPORT_REVIEWED_EXECUTION_INPUT"
        status = {"run": {"id": "run-1", "status": "running"}, "agents": [], "tasks": [{
            "taskId": "task-1", "id": "review", "status": "pending", "attempts": 0,
            "dependencies": [], "specialistContractId": "contract-7",
            "payload": {
                "goal": secret,
                "specialistAccess": {
                    "contractId": "contract-7", "designId": "design-1", "specialistId": "security",
                    "nodeId": "node-2", "action": "read", "audience": "internal", "purpose": "review",
                    "modelId": "model-a", "adapterId": "openrouter", "toolId": "review",
                    "resourceId": "model:review", "designSha256": "a" * 64,
                    "skillBindingsSha256": "b" * 64, "mcpBindingsSha256": "c" * 64,
                    "executionInputSha256": "d" * 64,
                    "unexpectedSecret": secret,
                },
                "reviewedDesign": {"secret": secret}, "executionInput": {"goal": secret},
            },
        }]}

        graph = project_execution_graph(status)
        contract = next(node for node in graph["nodes"] if node["kind"] == "specialist_contract")
        self.assertEqual(contract["id"], "specialist-contract:contract-7")
        self.assertEqual(contract["status"], "bound")
        self.assertIn("live authorization", contract["explanations"][0])
        self.assertEqual(contract["details"]["executionInputSha256"], "d" * 64)
        self.assertNotIn("unexpectedSecret", contract["details"])
        task_id = "task:task-1"
        self.assertTrue(any(edge["source"] == task_id and edge["target"] == contract["id"]
                            and edge["kind"] == "governed_by"
                            and edge.get("label") == "bound contract; not live authorization"
                            for edge in graph["edges"]))
        encoded = json.dumps(graph)
        self.assertNotIn(secret, encoded)
        self.assertNotIn("reviewedDesign", encoded)
        self.assertNotIn('"executionInput":', encoded)

    def test_specialist_contract_id_without_matching_binding_still_has_safe_bound_edge(self):
        status = {"run": {"id": "run-1"}, "tasks": [{
            "taskId": "task-1", "id": "review", "status": "pending", "attempts": 0,
            "specialistContractId": "contract-7", "payload": {"specialistAccess": {
                "contractId": "other-contract", "executionInput": "must not leak"}},
        }]}
        graph = project_execution_graph(status)
        contract = next(node for node in graph["nodes"] if node["kind"] == "specialist_contract")
        self.assertEqual(contract["status"], "bound")
        self.assertNotIn("details", contract)
        self.assertTrue(any(edge["kind"] == "governed_by" for edge in graph["edges"]))
        self.assertNotIn("must not leak", json.dumps(graph))

    def test_upstream_ledger_page_truncation_is_not_called_missing_or_unknown(self):
        status = {"run": {"id": "r", "status": "succeeded"},
                  "agents": [], "tasks": [{"taskId": "t", "id": "t", "status": "succeeded",
                                              "dependencies": [], "attempts": 300,
                                              "reservedCostMicrousd": 1000,
                                              "actualCostMicrousd": 200}],
                  "ledger": {"attempts": [{"attemptId": "a1", "taskId": "t", "attempt": 1,
                                             "actualCostMicrousd": 100},
                                            {"attemptId": "a2", "taskId": "t", "attempt": 2,
                                             "actualCostMicrousd": 100}],
                             "totalAttempts": 300, "returnedAttempts": 2,
                             "truncated": True, "coverageComplete": True,
                             "allCostsResolved": True, "knownActualMicrousd": 12345,
                             "unresolvedCostCount": 0}}
        graph = project_execution_graph(status)
        self.assertEqual(graph["summary"]["attemptCoverage"]["missing"], 0)
        self.assertEqual(graph["summary"]["omittedAttempts"], 298)
        self.assertEqual(graph["summary"]["unknownCostAttempts"], 0)
        self.assertEqual(graph["summary"]["knownActualMicrousd"], 12345)
        self.assertTrue(graph["truncated"])


if __name__ == "__main__":
    unittest.main()
