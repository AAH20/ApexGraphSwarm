"""Tests for the four-dimension conformance evaluator."""
from __future__ import annotations

import json
import time
import unittest

from conformance_evaluator import (
    ComputerUseReport,
    ConformanceError,
    ConformanceResult,
    FormalInvariantReport,
    GraphEdge,
    GraphNode,
    LatencyCostReport,
    Scorecard,
    TaskExecution,
    ToolAction,
    ToolCall,
    ZeroTrustReport,
    build_scorecard,
    evaluate_computer_use_precision,
    evaluate_conformance,
    evaluate_formal_invariants,
    evaluate_latency_cost,
    evaluate_zero_trust_discipline,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_nodes() -> list[GraphNode]:
    return [
        GraphNode("f1", "file", {"path": "src/main.py"}),
        GraphNode("fn1", "function", {"name": "main", "file": "src/main.py"}),
        GraphNode("fn2", "function", {"name": "helper", "file": "src/main.py"}),
        GraphNode("cls1", "class", {"name": "App", "file": "src/app.py"}),
        GraphNode("f2", "file", {"path": "src/app.py"}),
    ]


def make_edges() -> list[GraphEdge]:
    return [
        GraphEdge("e1", "f1", "fn1", "contains"),
        GraphEdge("e2", "f1", "fn2", "contains"),
        GraphEdge("e3", "f2", "cls1", "contains"),
        GraphEdge("e4", "fn1", "fn2", "calls"),
        GraphEdge("e5", "cls1", "fn1", "references"),
    ]


def make_tool_calls() -> list[ToolCall]:
    return [
        ToolCall("tc1", "read_file", {"path": "src/main.py"}, "file_contents", "file_contents", True, 1.0, 1.0),
        ToolCall("tc2", "write_file", {"path": "src/app.py", "content": "..."}, "written", "written", True, 1.0, 1.0),
        ToolCall("tc3", "run_command", {"cmd": "pytest"}, "test_results", "test_results", True, 1.0, 1.0),
    ]


def make_tool_actions() -> list[ToolAction]:
    return [
        ToolAction("ta1", "worker-1", "read_file", "src/main.py", "read", True, True, False, True, False),
        ToolAction("ta2", "worker-1", "write_file", "src/app.py", "write", True, True, False, True, False),
        ToolAction("ta3", "worker-2", "run_command", "pytest", "execute", True, True, False, True, False),
        ToolAction("ta4", "worker-3", "read_file", "/etc/passwd", "read", False, True, False, True, True),
    ]


def make_task_executions() -> list[TaskExecution]:
    return [
        TaskExecution("task1", 120.0, 500, deadline_ms=5000, budget_microusd=2000),
        TaskExecution("task2", 250.0, 800, deadline_ms=5000, budget_microusd=2000),
        TaskExecution("task3", 180.0, 600, deadline_ms=5000, budget_microusd=2000),
        TaskExecution("task4", 300.0, 400, deadline_ms=5000, budget_microusd=2000),
        TaskExecution("task5", 150.0, 700, deadline_ms=5000, budget_microusd=2000),
    ]


# ---------------------------------------------------------------------------
# Dimension 1: Formal Invariants
# ---------------------------------------------------------------------------

class TestFormalInvariants(unittest.TestCase):
    def test_valid_graph_passes(self):
        report = evaluate_formal_invariants(make_nodes(), make_edges())
        self.assertTrue(report.passed)
        self.assertEqual(report.score, 1.0)
        self.assertEqual(report.total_nodes, 5)
        self.assertEqual(report.total_edges, 5)
        self.assertEqual(report.duplicate_node_ids, [])
        self.assertEqual(report.dangling_edge_references, [])
        self.assertEqual(report.detected_cycles, [])

    def test_duplicate_node_ids_detected(self):
        nodes = make_nodes() + [GraphNode("f1", "file", {})]
        report = evaluate_formal_invariants(nodes, make_edges())
        self.assertFalse(report.passed)
        self.assertIn("f1", report.duplicate_node_ids)
        self.assertLess(report.score, 1.0)

    def test_duplicate_edge_ids_detected(self):
        edges = make_edges() + [GraphEdge("e1", "f1", "fn1", "contains")]
        report = evaluate_formal_invariants(make_nodes(), edges)
        self.assertFalse(report.passed)
        self.assertIn("e1", report.duplicate_edge_ids)

    def test_dangling_references_detected(self):
        edges = make_edges() + [GraphEdge("e_bad", "nonexistent", "fn1", "calls")]
        report = evaluate_formal_invariants(make_nodes(), edges)
        self.assertFalse(report.passed)
        self.assertTrue(any("nonexistent" in ref for ref in report.dangling_edge_references))

    def test_invalid_node_type_detected(self):
        nodes = make_nodes() + [GraphNode("bad", "unsupported_type", {})]
        report = evaluate_formal_invariants(nodes, make_edges())
        self.assertFalse(report.passed)
        self.assertTrue(any("bad" in item for item in report.invalid_node_types))

    def test_invalid_edge_type_detected(self):
        edges = make_edges() + [GraphEdge("e_bad", "f1", "fn1", "unsupported_relation")]
        report = evaluate_formal_invariants(make_nodes(), edges)
        self.assertFalse(report.passed)
        self.assertTrue(any("e_bad" in item for item in report.invalid_edge_types))

    def test_self_loop_detected(self):
        edges = make_edges() + [GraphEdge("e_self", "fn1", "fn1", "calls")]
        report = evaluate_formal_invariants(make_nodes(), edges)
        self.assertFalse(report.passed)
        self.assertIn("e_self", report.self_loops)

    def test_cycle_detected(self):
        edges = make_edges() + [
            GraphEdge("e_c1", "fn2", "cls1", "calls"),
            GraphEdge("e_c2", "cls1", "fn1", "calls"),
        ]
        report = evaluate_formal_invariants(make_nodes(), edges)
        self.assertFalse(report.passed)
        self.assertTrue(len(report.detected_cycles) > 0)

    def test_dag_not_required_when_false(self):
        edges = make_edges() + [
            GraphEdge("e_c1", "fn2", "cls1", "calls"),
            GraphEdge("e_c2", "cls1", "fn1", "calls"),
        ]
        report = evaluate_formal_invariants(make_nodes(), edges, require_dag=False)
        self.assertEqual(report.detected_cycles, [])

    def test_custom_allowed_types(self):
        nodes = [GraphNode("n1", "custom_type", {}), GraphNode("n2", "custom_type", {})]
        edges = [GraphEdge("e1", "n1", "n2", "custom_relation")]
        report = evaluate_formal_invariants(
            nodes, edges,
            allowed_node_types=frozenset({"custom_type"}),
            allowed_edge_types=frozenset({"custom_relation"}),
            require_dag=False,
        )
        self.assertTrue(report.passed)

    def test_empty_graph_fails(self):
        with self.assertRaises(ConformanceError):
            evaluate_formal_invariants([], [])
        with self.assertRaises(ConformanceError):
            evaluate_formal_invariants(make_nodes(), [])


# ---------------------------------------------------------------------------
# Dimension 2: Computer-Use Precision
# ---------------------------------------------------------------------------

class TestComputerUsePrecision(unittest.TestCase):
    def test_perfect_calls_pass(self):
        report = evaluate_computer_use_precision(make_tool_calls())
        self.assertTrue(report.passed)
        self.assertEqual(report.score, 1.0)
        self.assertEqual(report.total_calls, 3)
        self.assertEqual(report.successful_calls, 3)
        self.assertEqual(report.failed_calls, 0)

    def test_failed_call_detected(self):
        calls = make_tool_calls() + [
            ToolCall("tc_fail", "delete_file", {"path": "/important"}, None, None, False, 0.5, 0.5),
        ]
        report = evaluate_computer_use_precision(calls)
        self.assertFalse(report.passed)
        self.assertEqual(report.failed_calls, 1)
        self.assertLess(report.score, 1.0)

    def test_imprecise_path_detected(self):
        calls = [
            ToolCall("tc1", "read_file", {"path": "src/main.py"}, "ok", "ok", True, 0.3, 1.0),
        ]
        report = evaluate_computer_use_precision(calls)
        self.assertFalse(report.passed)
        self.assertIn("tc1", report.calls_with_imprecise_paths)

    def test_imprecise_command_detected(self):
        calls = [
            ToolCall("tc1", "run_command", {"cmd": "pytest"}, "ok", "ok", True, 1.0, 0.4),
        ]
        report = evaluate_computer_use_precision(calls)
        self.assertFalse(report.passed)
        self.assertIn("tc1", report.calls_with_imprecise_commands)

    def test_outcome_mismatch_detected(self):
        calls = [
            ToolCall("tc1", "read_file", {"path": "f"}, "expected_content", "different_content", True, 1.0, 1.0),
        ]
        report = evaluate_computer_use_precision(calls)
        self.assertFalse(report.passed)
        self.assertIn("tc1", report.outcome_mismatches)

    def test_custom_thresholds(self):
        calls = [
            ToolCall("tc1", "read_file", {"path": "f"}, "ok", "ok", True, 0.7, 0.7),
        ]
        report = evaluate_computer_use_precision(calls, path_threshold=0.6, command_threshold=0.6)
        self.assertTrue(report.passed)

    def test_empty_calls_fail(self):
        with self.assertRaises(ConformanceError):
            evaluate_computer_use_precision([])


# ---------------------------------------------------------------------------
# Dimension 3: Zero-Trust Tool Discipline
# ---------------------------------------------------------------------------

class TestZeroTrustDiscipline(unittest.TestCase):
    def test_compliant_actions_pass(self):
        actions = [
            ToolAction("ta1", "w1", "read_file", "f.py", "read", True, True, False, True, False),
            ToolAction("ta2", "w2", "write_file", "g.py", "write", True, True, False, True, False),
        ]
        report = evaluate_zero_trust_discipline(actions)
        self.assertTrue(report.passed)
        self.assertEqual(report.score, 1.0)
        self.assertEqual(report.policy_violations, 0)
        self.assertEqual(report.audit_coverage, 1.0)

    def test_policy_violation_detected(self):
        actions = [
            ToolAction("ta1", "w1", "read_file", "f.py", "read", True, True, True, True, False),
        ]
        report = evaluate_zero_trust_discipline(actions)
        self.assertFalse(report.passed)
        self.assertEqual(report.policy_violations, 1)
        self.assertLess(report.score, 1.0)

    def test_ungranted_attempt_detected(self):
        actions = [
            ToolAction("ta1", "w1", "read_file", "f.py", "read", False, True, False, True, False),
        ]
        report = evaluate_zero_trust_discipline(actions)
        self.assertFalse(report.passed)
        self.assertIn("ta1", report.ungranted_attempts)

    def test_unchecked_capability_detected(self):
        actions = [
            ToolAction("ta1", "w1", "read_file", "f.py", "read", True, False, False, True, False),
        ]
        report = evaluate_zero_trust_discipline(actions)
        self.assertFalse(report.passed)
        self.assertIn("ta1", report.unchecked_capability_attempts)

    def test_unaudited_action_detected(self):
        actions = [
            ToolAction("ta1", "w1", "read_file", "f.py", "read", True, True, False, False, False),
        ]
        report = evaluate_zero_trust_discipline(actions)
        self.assertFalse(report.passed)
        self.assertIn("ta1", report.unaudited_actions)
        self.assertEqual(report.audit_coverage, 0.0)

    def test_denied_action_is_ok(self):
        actions = [
            ToolAction("ta1", "w1", "read_file", "f.py", "read", False, True, False, True, True),
        ]
        report = evaluate_zero_trust_discipline(actions)
        self.assertTrue(report.passed)
        self.assertEqual(report.denied_actions, 1)
        self.assertEqual(report.granted_actions, 0)

    def test_audit_not_required(self):
        actions = [
            ToolAction("ta1", "w1", "read_file", "f.py", "read", True, True, False, False, False),
        ]
        report = evaluate_zero_trust_discipline(actions, require_audit=False)
        self.assertTrue(report.passed)

    def test_empty_actions_fail(self):
        with self.assertRaises(ConformanceError):
            evaluate_zero_trust_discipline([])


# ---------------------------------------------------------------------------
# Dimension 4: Latency/Cost Conformance
# ---------------------------------------------------------------------------

class TestLatencyCost(unittest.TestCase):
    def test_within_slo_passes(self):
        report = evaluate_latency_cost(make_task_executions(), latency_slo_ms=5000)
        self.assertTrue(report.passed)
        self.assertEqual(report.score, 1.0)
        self.assertEqual(report.deadline_violations, [])
        self.assertEqual(report.budget_violations, [])

    def test_p95_latency_computed(self):
        report = evaluate_latency_cost(make_task_executions())
        self.assertIsNotNone(report.p95_latency_ms)
        self.assertIsNotNone(report.p50_latency_ms)
        self.assertIsNotNone(report.mean_latency_ms)
        self.assertIsNotNone(report.max_latency_ms)
        self.assertIsNotNone(report.p95_latency_ms)
        self.assertIsNotNone(report.p50_latency_ms)
        self.assertGreaterEqual(report.p95_latency_ms, report.p50_latency_ms)

    def test_deadline_violation_detected(self):
        tasks = make_task_executions() + [
            TaskExecution("task_late", 6000.0, 500, deadline_ms=5000),
        ]
        report = evaluate_latency_cost(tasks)
        self.assertFalse(report.passed)
        self.assertIn("task_late", report.deadline_violations)

    def test_budget_violation_detected(self):
        tasks = make_task_executions() + [
            TaskExecution("task_over", 100.0, 3000, budget_microusd=2000),
        ]
        report = evaluate_latency_cost(tasks)
        self.assertFalse(report.passed)
        self.assertIn("task_over", report.budget_violations)

    def test_unknown_cost_detected(self):
        tasks = make_task_executions() + [
            TaskExecution("task_unknown", 100.0, None),
        ]
        report = evaluate_latency_cost(tasks)
        self.assertFalse(report.passed)
        self.assertIn("task_unknown", report.unknown_cost_tasks)
        self.assertEqual(report.total_cost_microusd, 3000)  # sum of known costs only

    def test_cost_cap_enforced(self):
        tasks = make_task_executions()
        report = evaluate_latency_cost(tasks, cost_cap_microusd=1000)
        self.assertTrue(report.passed)

    def test_cost_cap_violated(self):
        tasks = make_task_executions()
        report = evaluate_latency_cost(tasks, cost_cap_microusd=400)
        self.assertFalse(report.passed)
        self.assertLess(report.score, 1.0)

    def test_latency_slo_violated(self):
        tasks = [
            TaskExecution("t1", 100.0, 100),
            TaskExecution("t2", 200.0, 100),
            TaskExecution("t3", 300.0, 100),
        ]
        report = evaluate_latency_cost(tasks, latency_slo_ms=150)
        self.assertFalse(report.passed)
        self.assertLess(report.score, 1.0)

    def test_empty_tasks_fail(self):
        with self.assertRaises(ConformanceError):
            evaluate_latency_cost([])


# ---------------------------------------------------------------------------
# Scorecard Tests
# ---------------------------------------------------------------------------

class TestScorecard(unittest.TestCase):
    def test_scorecard_hash_verification(self):
        formal = evaluate_formal_invariants(make_nodes(), make_edges())
        cu = evaluate_computer_use_precision(make_tool_calls())
        zt = evaluate_zero_trust_discipline(make_tool_actions())
        lc = evaluate_latency_cost(make_task_executions())

        sc = build_scorecard(
            run_id="test-run-1",
            timestamp_unix=1700000000.0,
            formal_report=formal,
            computer_use_report=cu,
            zero_trust_report=zt,
            latency_cost_report=lc,
            hmac_key="test-secret",
        )
        self.assertTrue(sc.verify(hmac_key="test-secret"))
        self.assertFalse(sc.verify(hmac_key="wrong-key"))
        self.assertIsNotNone(sc.scorecard_hash)
        self.assertIsNotNone(sc.hmac_signature)

    def test_scorecard_tamper_detection(self):
        formal = evaluate_formal_invariants(make_nodes(), make_edges())
        cu = evaluate_computer_use_precision(make_tool_calls())
        zt = evaluate_zero_trust_discipline(make_tool_actions())
        lc = evaluate_latency_cost(make_task_executions())

        sc = build_scorecard(
            run_id="test-run-2",
            timestamp_unix=1700000000.0,
            formal_report=formal,
            computer_use_report=cu,
            zero_trust_report=zt,
            latency_cost_report=lc,
        )
        # Tamper with the scorecard
        sc_dict = sc.to_dict()
        sc_dict["overallScore"] = 0.0
        tampered = Scorecard.from_dict(sc_dict)
        self.assertFalse(tampered.verify())

    def test_scorecard_without_hmac(self):
        formal = evaluate_formal_invariants(make_nodes(), make_edges())
        cu = evaluate_computer_use_precision(make_tool_calls())
        zt = evaluate_zero_trust_discipline(make_tool_actions())
        lc = evaluate_latency_cost(make_task_executions())

        sc = build_scorecard(
            run_id="test-run-3",
            timestamp_unix=1700000000.0,
            formal_report=formal,
            computer_use_report=cu,
            zero_trust_report=zt,
            latency_cost_report=lc,
        )
        self.assertIsNone(sc.hmac_signature)
        self.assertTrue(sc.verify())
        self.assertTrue(sc.verify(hmac_key="any-key"))  # HMAC not required

    def test_scorecard_chain(self):
        formal = evaluate_formal_invariants(make_nodes(), make_edges())
        cu = evaluate_computer_use_precision(make_tool_calls())
        zt = evaluate_zero_trust_discipline(make_tool_actions())
        lc = evaluate_latency_cost(make_task_executions())

        sc1 = build_scorecard(
            run_id="chain-run",
            timestamp_unix=1700000000.0,
            formal_report=formal,
            computer_use_report=cu,
            zero_trust_report=zt,
            latency_cost_report=lc,
        )
        sc2 = build_scorecard(
            run_id="chain-run",
            timestamp_unix=1700000001.0,
            formal_report=formal,
            computer_use_report=cu,
            zero_trust_report=zt,
            latency_cost_report=lc,
            previous_scorecard_hash=sc1.scorecard_hash,
        )
        self.assertEqual(sc2.previous_scorecard_hash, sc1.scorecard_hash)

    def test_scorecard_serialization(self):
        formal = evaluate_formal_invariants(make_nodes(), make_edges())
        cu = evaluate_computer_use_precision(make_tool_calls())
        zt = evaluate_zero_trust_discipline(make_tool_actions())
        lc = evaluate_latency_cost(make_task_executions())

        sc = build_scorecard(
            run_id="ser-run",
            timestamp_unix=1700000000.0,
            formal_report=formal,
            computer_use_report=cu,
            zero_trust_report=zt,
            latency_cost_report=lc,
        )
        sc_dict = sc.to_dict()
        restored = Scorecard.from_dict(sc_dict)
        self.assertEqual(restored.scorecard_hash, sc.scorecard_hash)
        self.assertEqual(restored.overall_score, sc.overall_score)
        self.assertTrue(restored.verify())


# ---------------------------------------------------------------------------
# Integration: Full Conformance Evaluation
# ---------------------------------------------------------------------------

class TestFullConformance(unittest.TestCase):
    def test_full_evaluation_passes(self):
        result = evaluate_conformance(
            run_id="full-test-1",
            timestamp_unix=time.time(),
            nodes=make_nodes(),
            edges=make_edges(),
            tool_calls=make_tool_calls(),
            tool_actions=make_tool_actions(),
            task_executions=make_task_executions(),
            hmac_key="integration-secret",
        )
        self.assertIsInstance(result, ConformanceResult)
        self.assertTrue(result.formal.passed)
        self.assertTrue(result.computer_use.passed)
        self.assertTrue(result.zero_trust.passed)
        self.assertTrue(result.latency_cost.passed)
        self.assertTrue(result.scorecard.overall_passed)
        self.assertTrue(result.scorecard.verify(hmac_key="integration-secret"))

    def test_full_evaluation_with_violations(self):
        bad_nodes = make_nodes() + [GraphNode("f1", "file", {})]  # duplicate
        result = evaluate_conformance(
            run_id="full-test-2",
            timestamp_unix=time.time(),
            nodes=bad_nodes,
            edges=make_edges(),
            tool_calls=make_tool_calls(),
            tool_actions=make_tool_actions(),
            task_executions=make_task_executions(),
        )
        self.assertFalse(result.formal.passed)
        self.assertFalse(result.scorecard.overall_passed)

    def test_to_dict_serializable(self):
        result = evaluate_conformance(
            run_id="full-test-3",
            timestamp_unix=time.time(),
            nodes=make_nodes(),
            edges=make_edges(),
            tool_calls=make_tool_calls(),
            tool_actions=make_tool_actions(),
            task_executions=make_task_executions(),
        )
        d = result.to_dict()
        # Must be JSON-serializable
        json_str = json.dumps(d)
        self.assertIsInstance(json_str, str)
        restored = json.loads(json_str)
        self.assertEqual(restored["runId"], "full-test-3")
        self.assertIn("scorecard", restored)
        self.assertIn("formalInvariants", restored)

    def test_overall_score_is_average(self):
        result = evaluate_conformance(
            run_id="full-test-4",
            timestamp_unix=time.time(),
            nodes=make_nodes(),
            edges=make_edges(),
            tool_calls=make_tool_calls(),
            tool_actions=make_tool_actions(),
            task_executions=make_task_executions(),
        )
        expected_avg = (
            result.formal.score
            + result.computer_use.score
            + result.zero_trust.score
            + result.latency_cost.score
        ) / 4
        self.assertAlmostEqual(result.scorecard.overall_score, expected_avg, places=5)


if __name__ == "__main__":
    unittest.main()
