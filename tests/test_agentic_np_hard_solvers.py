"""
Comprehensive unit tests for Agentic NP-Hard Kernel solvers.
Covers: Tool Routing, Workflow DAG, Prefix-KV Cache, Speculative Tree Search,
        Fault-Tolerant DAG, Submodular Memory, Pareto Model Routing,
        Sandbox Resource Scheduler, Least-Privilege RBAC, Byzantine Consensus.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.integration-sources', 'agentic-np-hard-kernel'))

from agentic_np_hard_kernel.core.models import (
    ToolDefinition, SubTask, ContextPromptBlock, SpeculativeActionNode,
    TaskFailureEvent, AgentMemoryRecord, ModelOption, AgentResourceRequest,
    CapabilityRule, AgentExecutionReceipt
)
from agentic_np_hard_kernel.core.tool_routing import CombinatorialToolRouter
from agentic_np_hard_kernel.core.workflow_dag import WorkflowDAGSynthesizer
from agentic_np_hard_kernel.core.prefix_kv_cache import PrefixKVCacheOptimizer
from agentic_np_hard_kernel.core.speculative_tree import SpeculativeTreeSearchSolver
from agentic_np_hard_kernel.core.fault_tolerant_dag import SelfHealingDAGReconfigurator
from agentic_np_hard_kernel.core.submodular_memory import SubmodularMemoryRetriever
from agentic_np_hard_kernel.core.pareto_model_router import ParetoModelRouter
from agentic_np_hard_kernel.core.sandbox_resource_scheduler import SandboxResourceScheduler
from agentic_np_hard_kernel.core.least_privilege_rbac import LeastPrivilegeRBACSolver
from agentic_np_hard_kernel.core.byzantine_consensus import ByzantineAgentConsensus


class TestCombinatorialToolRouter(unittest.TestCase):
    """Tests for Combinatorial Tool Routing & Selection solver."""

    def test_basic_routing(self):
        tools = [
            ToolDefinition("t1", "Tool 1", 0.9, 10.0, 100),
            ToolDefinition("t2", "Tool 2", 0.8, 15.0, 150),
            ToolDefinition("t3", "Tool 3", 0.95, 20.0, 200, ["t1"]),
            ToolDefinition("t4", "Tool 4", 0.5, 50.0, 500),
        ]
        router = CombinatorialToolRouter(tools)
        res = router.solve(max_latency_ms=35.0, max_token_budget=350)
        selected_ids = {t.tool_id for t in res.selected_tools}
        self.assertIn("t1", selected_ids)
        self.assertIn("t3", selected_ids)
        self.assertNotIn("t4", selected_ids)
        self.assertLessEqual(res.total_latency_ms, 35.0)
        self.assertLessEqual(res.total_token_cost, 350)

    def test_empty_tools(self):
        router = CombinatorialToolRouter([])
        res = router.solve(max_latency_ms=100.0, max_token_budget=1000)
        self.assertEqual(res.selected_tools, [])

    def test_dependency_closure(self):
        tools = [
            ToolDefinition("base", "Base", 0.5, 5.0, 50),
            ToolDefinition("dep", "Dep", 0.9, 5.0, 50, ["base"]),
        ]
        router = CombinatorialToolRouter(tools)
        res = router.solve(max_latency_ms=20.0, max_token_budget=200)
        selected_ids = {t.tool_id for t in res.selected_tools}
        if "dep" in selected_ids:
            self.assertIn("base", selected_ids)

    def test_utility_calculation(self):
        tools = [
            ToolDefinition("t1", "T1", 0.9, 5.0, 50),
        ]
        router = CombinatorialToolRouter(tools)
        res = router.solve(max_latency_ms=10.0, max_token_budget=100)
        self.assertAlmostEqual(res.total_utility, 0.9, places=5)

    def test_latency_constraint(self):
        tools = [
            ToolDefinition("t1", "T1", 0.9, 100.0, 50),
            ToolDefinition("t2", "T2", 0.5, 5.0, 50),
        ]
        router = CombinatorialToolRouter(tools)
        res = router.solve(max_latency_ms=10.0, max_token_budget=100)
        selected_ids = {t.tool_id for t in res.selected_tools}
        self.assertNotIn("t1", selected_ids)

    def test_token_constraint(self):
        tools = [
            ToolDefinition("t1", "T1", 0.9, 5.0, 1000),
            ToolDefinition("t2", "T2", 0.5, 5.0, 50),
        ]
        router = CombinatorialToolRouter(tools)
        res = router.solve(max_latency_ms=10.0, max_token_budget=100)
        selected_ids = {t.tool_id for t in res.selected_tools}
        self.assertNotIn("t1", selected_ids)

    def test_algorithm_name(self):
        tools = [ToolDefinition("t1", "T1", 0.5, 5.0, 50)]
        router = CombinatorialToolRouter(tools)
        res = router.solve(max_latency_ms=10.0, max_token_budget=100)
        self.assertEqual(res.algorithm, "BRANCH_AND_BOUND_MKP_PC")

    def test_execution_time(self):
        tools = [ToolDefinition("t1", "T1", 0.5, 5.0, 50)]
        router = CombinatorialToolRouter(tools)
        res = router.solve(max_latency_ms=10.0, max_token_budget=100)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_greedy_baseline(self):
        tools = [
            ToolDefinition("t1", "T1", 0.9, 5.0, 50),
            ToolDefinition("t2", "T2", 0.8, 10.0, 100),
        ]
        router = CombinatorialToolRouter(tools)
        res = router.solve_greedy_baseline(max_latency_ms=20.0, max_token_budget=200)
        self.assertGreater(res.total_utility, 0.0)

    def test_greedy_baseline_algorithm(self):
        tools = [ToolDefinition("t1", "T1", 0.5, 5.0, 50)]
        router = CombinatorialToolRouter(tools)
        res = router.solve_greedy_baseline(max_latency_ms=10.0, max_token_budget=100)
        self.assertEqual(res.algorithm, "GREEDY_HEURISTIC")

    def test_transitive_dependencies(self):
        tools = [
            ToolDefinition("a", "A", 0.3, 1.0, 10),
            ToolDefinition("b", "B", 0.3, 1.0, 10, ["a"]),
            ToolDefinition("c", "C", 0.9, 1.0, 10, ["b"]),
        ]
        router = CombinatorialToolRouter(tools)
        res = router.solve(max_latency_ms=10.0, max_token_budget=100)
        selected_ids = {t.tool_id for t in res.selected_tools}
        if "c" in selected_ids:
            self.assertIn("a", selected_ids)
            self.assertIn("b", selected_ids)

    def test_no_valid_selection(self):
        tools = [
            ToolDefinition("t1", "T1", 0.9, 100.0, 1000),
        ]
        router = CombinatorialToolRouter(tools)
        res = router.solve(max_latency_ms=10.0, max_token_budget=100)
        self.assertEqual(res.total_utility, 0.0)

    def test_many_tools(self):
        tools = [
            ToolDefinition(f"t{i}", f"Tool {i}", 0.5 + i * 0.05, float(i + 1), (i + 1) * 10)
            for i in range(10)
        ]
        router = CombinatorialToolRouter(tools)
        res = router.solve(max_latency_ms=50.0, max_token_budget=500)
        self.assertGreaterEqual(res.total_utility, 0.0)


class TestWorkflowDAGSynthesizer(unittest.TestCase):
    """Tests for Optimal Hierarchical Goal Decomposition & Workflow DAG Synthesis solver."""

    def test_basic_dag(self):
        tasks = [
            SubTask("A", "Task A", 10.0, [], "ROLE_1"),
            SubTask("B", "Task B", 20.0, ["A"], "ROLE_2"),
            SubTask("C", "Task C", 15.0, ["A"], "ROLE_3"),
            SubTask("D", "Task D", 25.0, ["B", "C"], "ROLE_4"),
        ]
        synth = WorkflowDAGSynthesizer(tasks)
        res = synth.solve()
        self.assertEqual(res.total_makespan_ms, 55.0)
        self.assertEqual(res.critical_path, ["A", "B", "D"])
        self.assertEqual(res.task_schedule["A"], 0.0)
        self.assertEqual(res.task_schedule["B"], 10.0)
        self.assertEqual(res.task_schedule["D"], 30.0)

    def test_empty_tasks(self):
        synth = WorkflowDAGSynthesizer([])
        res = synth.solve()
        self.assertEqual(res.total_makespan_ms, 0.0)

    def test_single_task(self):
        tasks = [SubTask("A", "Task A", 10.0, [], "ROLE_1")]
        synth = WorkflowDAGSynthesizer(tasks)
        res = synth.solve()
        self.assertEqual(res.total_makespan_ms, 10.0)
        self.assertEqual(res.critical_path, ["A"])

    def test_parallel_tasks(self):
        tasks = [
            SubTask("A", "Task A", 10.0, [], "ROLE_1"),
            SubTask("B", "Task B", 10.0, [], "ROLE_2"),
        ]
        synth = WorkflowDAGSynthesizer(tasks)
        res = synth.solve()
        self.assertEqual(res.total_makespan_ms, 10.0)

    def test_chain_dependencies(self):
        tasks = [
            SubTask("A", "A", 5.0, [], "R1"),
            SubTask("B", "B", 10.0, ["A"], "R2"),
            SubTask("C", "C", 15.0, ["B"], "R3"),
        ]
        synth = WorkflowDAGSynthesizer(tasks)
        res = synth.solve()
        self.assertEqual(res.total_makespan_ms, 30.0)

    def test_parallelism_factor(self):
        tasks = [
            SubTask("A", "A", 10.0, [], "R1"),
            SubTask("B", "B", 10.0, [], "R2"),
        ]
        synth = WorkflowDAGSynthesizer(tasks)
        res = synth.solve()
        self.assertGreater(res.parallelism_factor, 1.0)

    def test_algorithm_name(self):
        tasks = [SubTask("A", "A", 10.0, [], "R1")]
        synth = WorkflowDAGSynthesizer(tasks)
        res = synth.solve()
        self.assertEqual(res.algorithm, "EXACT_CPM_DAG")

    def test_execution_time(self):
        tasks = [SubTask("A", "A", 10.0, [], "R1")]
        synth = WorkflowDAGSynthesizer(tasks)
        res = synth.solve()
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_diamond_dependencies(self):
        tasks = [
            SubTask("A", "A", 10.0, [], "R1"),
            SubTask("B", "B", 20.0, ["A"], "R2"),
            SubTask("C", "C", 15.0, ["A"], "R3"),
            SubTask("D", "D", 25.0, ["B", "C"], "R4"),
        ]
        synth = WorkflowDAGSynthesizer(tasks)
        res = synth.solve()
        self.assertEqual(res.total_makespan_ms, 55.0)

    def test_multiple_roots(self):
        tasks = [
            SubTask("A", "A", 10.0, [], "R1"),
            SubTask("B", "B", 20.0, [], "R2"),
            SubTask("C", "C", 5.0, ["A", "B"], "R3"),
        ]
        synth = WorkflowDAGSynthesizer(tasks)
        res = synth.solve()
        self.assertEqual(res.total_makespan_ms, 25.0)

    def test_critical_path_identification(self):
        tasks = [
            SubTask("A", "A", 5.0, [], "R1"),
            SubTask("B", "B", 100.0, ["A"], "R2"),
            SubTask("C", "C", 5.0, ["A"], "R3"),
        ]
        synth = WorkflowDAGSynthesizer(tasks)
        res = synth.solve()
        self.assertIn("B", res.critical_path)

    def test_schedule_start_times(self):
        tasks = [
            SubTask("A", "A", 10.0, [], "R1"),
            SubTask("B", "B", 20.0, ["A"], "R2"),
        ]
        synth = WorkflowDAGSynthesizer(tasks)
        res = synth.solve()
        self.assertEqual(res.task_schedule["A"], 0.0)
        self.assertEqual(res.task_schedule["B"], 10.0)

    def test_cycle_fallback(self):
        tasks = [
            SubTask("A", "A", 10.0, ["B"], "R1"),
            SubTask("B", "B", 10.0, ["A"], "R2"),
        ]
        synth = WorkflowDAGSynthesizer(tasks)
        res = synth.solve()
        # Should still produce a result
        self.assertGreaterEqual(res.total_makespan_ms, 0.0)


class TestPrefixKVCacheOptimizer(unittest.TestCase):
    """Tests for Shared Prefix-KV Cache & Context Memory Packing solver."""

    def test_basic_packing(self):
        blocks = [
            ContextPromptBlock("P1", [1, 2, 3, 4], 100, 1.0, "A1"),
            ContextPromptBlock("P2", [1, 2, 3, 4, 5, 6], 150, 0.9, "A2"),
            ContextPromptBlock("P3", [1, 2, 8, 9], 120, 0.8, "A3"),
        ]
        opt = PrefixKVCacheOptimizer(blocks)
        res = opt.solve()
        self.assertEqual(len(res.packed_execution_order), 3)
        self.assertGreater(res.saved_prefill_tokens, 0)
        self.assertGreater(res.cache_hit_ratio, 0.0)

    def test_empty_blocks(self):
        opt = PrefixKVCacheOptimizer([])
        res = opt.solve()
        self.assertEqual(res.packed_execution_order, [])

    def test_single_block(self):
        blocks = [ContextPromptBlock("P1", [1, 2, 3], 100, 1.0, "A1")]
        opt = PrefixKVCacheOptimizer(blocks)
        res = opt.solve()
        self.assertEqual(len(res.packed_execution_order), 1)
        self.assertEqual(res.saved_prefill_tokens, 0)

    def test_identical_prefixes(self):
        blocks = [
            ContextPromptBlock("P1", [1, 2, 3, 4, 5], 100, 1.0, "A1"),
            ContextPromptBlock("P2", [1, 2, 3, 4, 5], 100, 1.0, "A2"),
        ]
        opt = PrefixKVCacheOptimizer(blocks)
        res = opt.solve()
        self.assertGreater(res.saved_prefill_tokens, 0)

    def test_vram_peak(self):
        blocks = [
            ContextPromptBlock("P1", [1, 2], 500, 1.0, "A1"),
            ContextPromptBlock("P2", [3, 4], 300, 0.9, "A2"),
        ]
        opt = PrefixKVCacheOptimizer(blocks, max_vram_tokens=1000)
        res = opt.solve()
        self.assertLessEqual(res.vram_peak_tokens, 1000)

    def test_algorithm_name(self):
        blocks = [ContextPromptBlock("P1", [1, 2], 100, 1.0, "A1")]
        opt = PrefixKVCacheOptimizer(blocks)
        res = opt.solve()
        self.assertEqual(res.algorithm, "RADIX_PREFIX_PACKER")

    def test_execution_time(self):
        blocks = [ContextPromptBlock("P1", [1, 2], 100, 1.0, "A1")]
        opt = PrefixKVCacheOptimizer(blocks)
        res = opt.solve()
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_priority_weight(self):
        blocks = [
            ContextPromptBlock("P1", [1, 2], 100, 0.5, "A1"),
            ContextPromptBlock("P2", [3, 4], 100, 1.0, "A2"),
        ]
        opt = PrefixKVCacheOptimizer(blocks)
        res = opt.solve()
        # Higher priority should be first
        self.assertEqual(res.packed_execution_order[0], "P2")

    def test_no_common_prefix(self):
        blocks = [
            ContextPromptBlock("P1", [1, 2, 3], 100, 1.0, "A1"),
            ContextPromptBlock("P2", [4, 5, 6], 100, 1.0, "A2"),
        ]
        opt = PrefixKVCacheOptimizer(blocks)
        res = opt.solve()
        self.assertEqual(res.saved_prefill_tokens, 0)

    def test_many_blocks(self):
        blocks = [
            ContextPromptBlock(f"P{i}", [i, i+1, i+2], 100, 1.0 - i * 0.1, f"A{i}")
            for i in range(10)
        ]
        opt = PrefixKVCacheOptimizer(blocks)
        res = opt.solve()
        self.assertEqual(len(res.packed_execution_order), 10)

    def test_cache_hit_ratio_range(self):
        blocks = [
            ContextPromptBlock("P1", [1, 2, 3], 100, 1.0, "A1"),
            ContextPromptBlock("P2", [1, 2, 3], 100, 1.0, "A2"),
        ]
        opt = PrefixKVCacheOptimizer(blocks)
        res = opt.solve()
        self.assertGreaterEqual(res.cache_hit_ratio, 0.0)


class TestSpeculativeTreeSearchSolver(unittest.TestCase):
    """Tests for Speculative Multi-Branch Agent Rollout & Verification Tree Search solver."""

    def test_basic_search(self):
        nodes = [
            SpeculativeActionNode("N0", None, "Root", 0, 0.5, False, 0),
            SpeculativeActionNode("N1", "N0", "Child1", 100, 0.8, True, 1),
            SpeculativeActionNode("N2", "N0", "Child2", 200, 0.6, True, 1),
        ]
        solver = SpeculativeTreeSearchSolver(nodes, token_budget=1000)
        res = solver.solve()
        self.assertGreater(len(res.optimal_path), 0)
        self.assertGreater(res.highest_verification_score, 0.0)

    def test_empty_nodes(self):
        solver = SpeculativeTreeSearchSolver([], token_budget=1000)
        res = solver.solve()
        self.assertEqual(res.optimal_path, [])

    def test_single_node(self):
        nodes = [SpeculativeActionNode("N0", None, "Root", 0, 0.5, True, 0)]
        solver = SpeculativeTreeSearchSolver(nodes, token_budget=1000)
        res = solver.solve()
        self.assertEqual(res.optimal_path, ["N0"])

    def test_budget_pruning(self):
        nodes = [
            SpeculativeActionNode("N0", None, "Root", 0, 0.5, False, 0),
            SpeculativeActionNode("N1", "N0", "Expensive", 2000, 0.9, True, 1),
            SpeculativeActionNode("N2", "N0", "Cheap", 100, 0.7, True, 1),
        ]
        solver = SpeculativeTreeSearchSolver(nodes, token_budget=500)
        res = solver.solve()
        self.assertGreater(res.nodes_pruned, 0)

    def test_deep_tree(self):
        nodes = [
            SpeculativeActionNode("N0", None, "Root", 0, 0.3, False, 0),
            SpeculativeActionNode("N1", "N0", "L1", 50, 0.5, False, 1),
            SpeculativeActionNode("N2", "N1", "L2", 50, 0.9, True, 2),
        ]
        solver = SpeculativeTreeSearchSolver(nodes, token_budget=200)
        res = solver.solve()
        self.assertIn("N2", res.optimal_path)

    def test_total_tokens_spent(self):
        nodes = [
            SpeculativeActionNode("N0", None, "Root", 10, 0.5, True, 0),
        ]
        solver = SpeculativeTreeSearchSolver(nodes, token_budget=100)
        res = solver.solve()
        self.assertEqual(res.total_tokens_spent, 10)

    def test_algorithm_name(self):
        nodes = [SpeculativeActionNode("N0", None, "Root", 0, 0.5, True, 0)]
        solver = SpeculativeTreeSearchSolver(nodes, token_budget=100)
        res = solver.solve()
        self.assertEqual(res.algorithm, "BEST_FIRST_SPECULATIVE_BNB")

    def test_execution_time(self):
        nodes = [SpeculativeActionNode("N0", None, "Root", 0, 0.5, True, 0)]
        solver = SpeculativeTreeSearchSolver(nodes, token_budget=100)
        res = solver.solve()
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_multiple_roots(self):
        nodes = [
            SpeculativeActionNode("R1", None, "Root1", 0, 0.8, True, 0),
            SpeculativeActionNode("R2", None, "Root2", 0, 0.6, True, 0),
        ]
        solver = SpeculativeTreeSearchSolver(nodes, token_budget=100)
        res = solver.solve()
        self.assertEqual(res.highest_verification_score, 0.8)

    def test_best_path_selection(self):
        nodes = [
            SpeculativeActionNode("N0", None, "Root", 0, 0.3, False, 0),
            SpeculativeActionNode("N1", "N0", "Low", 50, 0.4, True, 1),
            SpeculativeActionNode("N2", "N0", "High", 50, 0.95, True, 1),
        ]
        solver = SpeculativeTreeSearchSolver(nodes, token_budget=100)
        res = solver.solve()
        self.assertEqual(res.highest_verification_score, 0.95)

    def test_disconnected_node(self):
        nodes = [
            SpeculativeActionNode("N0", None, "Root", 0, 0.5, True, 0),
            SpeculativeActionNode("NX", "NY", "Orphan", 50, 0.99, True, 1),
        ]
        solver = SpeculativeTreeSearchSolver(nodes, token_budget=100)
        res = solver.solve()
        # Orphan node has invalid parent, so it becomes a root itself
        self.assertIn("NX", res.optimal_path)


class TestSelfHealingDAGReconfigurator(unittest.TestCase):
    """Tests for Dynamic Fault-Tolerant Workflow Reconfiguration solver."""

    def test_basic_reconfiguration(self):
        tasks = [
            SubTask("A", "Task A", 10.0, [], "R1"),
            SubTask("B", "Task B", 20.0, ["A"], "R2"),
        ]
        healer = SelfHealingDAGReconfigurator(tasks)
        failure = TaskFailureEvent("A", "ERR", ["C"])
        fallbacks = {"C": SubTask("C", "Fallback C", 15.0, [], "R1")}
        res = healer.reconfigure(failure, fallbacks)
        self.assertEqual(res.tasks_rerouted, 1)
        self.assertGreaterEqual(res.makespan_increase_ms, 0.0)

    def test_unknown_failed_task(self):
        tasks = [SubTask("A", "Task A", 10.0, [], "R1")]
        healer = SelfHealingDAGReconfigurator(tasks)
        failure = TaskFailureEvent("Z", "ERR", ["C"])
        fallbacks = {"C": SubTask("C", "Fallback C", 15.0, [], "R1")}
        res = healer.reconfigure(failure, fallbacks)
        self.assertEqual(res.tasks_rerouted, 0)
        self.assertEqual(res.makespan_increase_ms, 0.0)

    def test_no_fallback_candidates(self):
        tasks = [SubTask("A", "Task A", 10.0, [], "R1")]
        healer = SelfHealingDAGReconfigurator(tasks)
        failure = TaskFailureEvent("A", "ERR", [])
        res = healer.reconfigure(failure, {})
        self.assertEqual(res.tasks_rerouted, 0)

    def test_stability_score(self):
        tasks = [
            SubTask("A", "Task A", 10.0, [], "R1"),
            SubTask("B", "Task B", 20.0, [], "R2"),
        ]
        healer = SelfHealingDAGReconfigurator(tasks)
        failure = TaskFailureEvent("A", "ERR", ["C"])
        fallbacks = {"C": SubTask("C", "Fallback C", 10.0, [], "R1")}
        res = healer.reconfigure(failure, fallbacks)
        self.assertGreaterEqual(res.stability_score, 0.0)
        self.assertLessEqual(res.stability_score, 1.0)

    def test_algorithm_name(self):
        tasks = [SubTask("A", "Task A", 10.0, [], "R1")]
        healer = SelfHealingDAGReconfigurator(tasks)
        failure = TaskFailureEvent("A", "ERR", ["C"])
        fallbacks = {"C": SubTask("C", "Fallback C", 15.0, [], "R1")}
        res = healer.reconfigure(failure, fallbacks)
        self.assertEqual(res.algorithm, "INCREMENTAL_DAG_RECONFIG")

    def test_execution_time(self):
        tasks = [SubTask("A", "Task A", 10.0, [], "R1")]
        healer = SelfHealingDAGReconfigurator(tasks)
        failure = TaskFailureEvent("A", "ERR", ["C"])
        fallbacks = {"C": SubTask("C", "Fallback C", 15.0, [], "R1")}
        res = healer.reconfigure(failure, fallbacks)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_successor_dependencies_updated(self):
        tasks = [
            SubTask("A", "Task A", 10.0, [], "R1"),
            SubTask("B", "Task B", 20.0, ["A"], "R2"),
        ]
        healer = SelfHealingDAGReconfigurator(tasks)
        failure = TaskFailureEvent("A", "ERR", ["C"])
        fallbacks = {"C": SubTask("C", "Fallback C", 15.0, [], "R1")}
        res = healer.reconfigure(failure, fallbacks)
        # B should now depend on C instead of A
        self.assertIn("C", res.repaired_schedule)

    def test_faster_fallback(self):
        tasks = [
            SubTask("A", "Task A", 100.0, [], "R1"),
            SubTask("B", "Task B", 20.0, ["A"], "R2"),
        ]
        healer = SelfHealingDAGReconfigurator(tasks)
        failure = TaskFailureEvent("A", "ERR", ["C"])
        fallbacks = {"C": SubTask("C", "Fallback C", 10.0, [], "R1")}
        res = healer.reconfigure(failure, fallbacks)
        self.assertLess(res.makespan_increase_ms, 100.0)

    def test_repaired_schedule_valid(self):
        tasks = [
            SubTask("A", "Task A", 10.0, [], "R1"),
            SubTask("B", "Task B", 20.0, ["A"], "R2"),
        ]
        healer = SelfHealingDAGReconfigurator(tasks)
        failure = TaskFailureEvent("A", "ERR", ["C"])
        fallbacks = {"C": SubTask("C", "Fallback C", 15.0, [], "R1")}
        res = healer.reconfigure(failure, fallbacks)
        self.assertIsInstance(res.repaired_schedule, dict)


class TestSubmodularMemoryRetriever(unittest.TestCase):
    """Tests for Submodular Multi-Agent Episodic & Semantic Memory Retrieval solver."""

    def test_basic_retrieval(self):
        pool = [
            AgentMemoryRecord(f"m{i}", f"topic_{i%3}", f"content_{i}", 0.5 + i * 0.1, float(i), [1.0 if i%2==0 else 0.0, 0.0])
            for i in range(10)
        ]
        retriever = SubmodularMemoryRetriever(pool)
        res = retriever.solve(k_records=3)
        self.assertEqual(len(res.retrieved_records), 3)

    def test_empty_pool(self):
        retriever = SubmodularMemoryRetriever([])
        res = retriever.solve(k_records=3)
        self.assertEqual(res.retrieved_records, [])

    def test_k_larger_than_pool(self):
        pool = [AgentMemoryRecord("m1", "t", "c", 0.5, 1.0, [1.0])]
        retriever = SubmodularMemoryRetriever(pool)
        res = retriever.solve(k_records=5)
        self.assertEqual(len(res.retrieved_records), 1)

    def test_k_zero(self):
        pool = [AgentMemoryRecord("m1", "t", "c", 0.5, 1.0, [1.0])]
        retriever = SubmodularMemoryRetriever(pool)
        res = retriever.solve(k_records=0)
        self.assertEqual(res.retrieved_records, [])

    def test_coverage_score(self):
        pool = [
            AgentMemoryRecord(f"m{i}", f"topic_{i}", f"c{i}", 0.8, float(i), [1.0, 0.0])
            for i in range(5)
        ]
        retriever = SubmodularMemoryRetriever(pool)
        res = retriever.solve(k_records=3)
        self.assertGreater(res.coverage_score, 0.0)

    def test_semantic_diversity(self):
        pool = [
            AgentMemoryRecord(f"m{i}", "t", f"c{i}", 0.5, float(i), [float(i), 1.0])
            for i in range(5)
        ]
        retriever = SubmodularMemoryRetriever(pool)
        res = retriever.solve(k_records=3)
        self.assertGreaterEqual(res.semantic_diversity, 0.0)

    def test_compression_ratio(self):
        pool = [
            AgentMemoryRecord(f"m{i}", "t", f"c{i}", 0.5, float(i), [1.0])
            for i in range(10)
        ]
        retriever = SubmodularMemoryRetriever(pool)
        res = retriever.solve(k_records=3)
        self.assertGreater(res.compression_ratio_pct, 0.0)

    def test_algorithm_name(self):
        pool = [AgentMemoryRecord("m1", "t", "c", 0.5, 1.0, [1.0])]
        retriever = SubmodularMemoryRetriever(pool)
        res = retriever.solve(k_records=1)
        self.assertEqual(res.algorithm, "ACCELERATED_LAZY_GREEDY_MEMORY")

    def test_execution_time(self):
        pool = [AgentMemoryRecord("m1", "t", "c", 0.5, 1.0, [1.0])]
        retriever = SubmodularMemoryRetriever(pool)
        res = retriever.solve(k_records=1)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_diversity_penalty(self):
        pool = [
            AgentMemoryRecord(f"m{i}", "t", f"c{i}", 0.5, float(i), [float(i), 0.0])
            for i in range(5)
        ]
        retriever = SubmodularMemoryRetriever(pool, diversity_penalty=1.0)
        res = retriever.solve(k_records=3)
        self.assertGreaterEqual(res.semantic_diversity, 0.0)

    def test_unique_records(self):
        pool = [
            AgentMemoryRecord(f"m{i}", "t", f"c{i}", 0.5, float(i), [1.0])
            for i in range(5)
        ]
        retriever = SubmodularMemoryRetriever(pool)
        res = retriever.solve(k_records=3)
        ids = [r.memory_id for r in res.retrieved_records]
        self.assertEqual(len(ids), len(set(ids)))

    def test_single_record(self):
        pool = [AgentMemoryRecord("m1", "t", "c", 0.5, 1.0, [1.0])]
        retriever = SubmodularMemoryRetriever(pool)
        res = retriever.solve(k_records=1)
        self.assertEqual(len(res.retrieved_records), 1)

    def test_many_records(self):
        pool = [
            AgentMemoryRecord(f"m{i}", f"t{i%5}", f"c{i}", 0.5, float(i), [float(i%3), 1.0])
            for i in range(20)
        ]
        retriever = SubmodularMemoryRetriever(pool)
        res = retriever.solve(k_records=5)
        self.assertEqual(len(res.retrieved_records), 5)


class TestParetoModelRouter(unittest.TestCase):
    """Tests for Multi-Objective Model Routing solver."""

    def test_basic_routing(self):
        catalog = [
            ModelOption("m1", "Cheap", 0.01, 100.0, 0.7),
            ModelOption("m2", "Balanced", 0.05, 50.0, 0.9),
            ModelOption("m3", "Premium", 0.10, 20.0, 0.95),
        ]
        router = ParetoModelRouter(catalog)
        res = router.solve()
        self.assertIsNotNone(res.selected_model)
        self.assertTrue(res.is_pareto_optimal)

    def test_empty_catalog(self):
        router = ParetoModelRouter([])
        with self.assertRaises(ValueError):
            router.solve()

    def test_cost_budget(self):
        catalog = [
            ModelOption("m1", "Cheap", 0.01, 100.0, 0.7),
            ModelOption("m2", "Expensive", 0.10, 50.0, 0.9),
        ]
        router = ParetoModelRouter(catalog)
        res = router.solve(max_cost_budget=0.05)
        self.assertLessEqual(res.selected_model.cost_per_k_tokens, 0.05)

    def test_latency_constraint(self):
        catalog = [
            ModelOption("m1", "Fast", 0.01, 10.0, 0.7),
            ModelOption("m2", "Slow", 0.05, 500.0, 0.9),
        ]
        router = ParetoModelRouter(catalog)
        res = router.solve(max_latency_ms=100.0)
        self.assertLessEqual(res.selected_model.latency_per_step_ms, 100.0)

    def test_fidelity_constraint(self):
        catalog = [
            ModelOption("m1", "Low", 0.01, 10.0, 0.5),
            ModelOption("m2", "High", 0.05, 50.0, 0.95),
        ]
        router = ParetoModelRouter(catalog)
        res = router.solve(min_fidelity=0.8)
        self.assertGreaterEqual(res.selected_model.benchmark_fidelity, 0.8)

    def test_hypervolume(self):
        catalog = [
            ModelOption("m1", "A", 0.01, 100.0, 0.7),
            ModelOption("m2", "B", 0.05, 50.0, 0.9),
        ]
        router = ParetoModelRouter(catalog)
        res = router.solve()
        self.assertGreaterEqual(res.hypervolume_delta, 0.0)

    def test_algorithm_name(self):
        catalog = [ModelOption("m1", "A", 0.01, 100.0, 0.7)]
        router = ParetoModelRouter(catalog)
        res = router.solve()
        self.assertEqual(res.algorithm, "EXACT_PARETO_ROUTER")

    def test_execution_time(self):
        catalog = [ModelOption("m1", "A", 0.01, 100.0, 0.7)]
        router = ParetoModelRouter(catalog)
        res = router.solve()
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_single_model(self):
        catalog = [ModelOption("m1", "Only", 0.05, 50.0, 0.8)]
        router = ParetoModelRouter(catalog)
        res = router.solve()
        self.assertEqual(res.selected_model.model_id, "m1")

    def test_dominated_model_excluded(self):
        catalog = [
            ModelOption("m1", "Good", 0.01, 10.0, 0.9),
            ModelOption("m2", "Bad", 0.10, 100.0, 0.5),
        ]
        router = ParetoModelRouter(catalog)
        res = router.solve()
        # m2 is dominated by m1
        self.assertEqual(res.selected_model.model_id, "m1")

    def test_no_constraints(self):
        catalog = [
            ModelOption("m1", "A", 0.01, 100.0, 0.7),
            ModelOption("m2", "B", 0.05, 50.0, 0.9),
            ModelOption("m3", "C", 0.10, 20.0, 0.95),
        ]
        router = ParetoModelRouter(catalog)
        res = router.solve()
        self.assertIsNotNone(res.selected_model)

    def test_impossible_constraints(self):
        catalog = [
            ModelOption("m1", "A", 0.01, 100.0, 0.7),
        ]
        router = ParetoModelRouter(catalog)
        res = router.solve(max_cost_budget=0.001, max_latency_ms=1.0, min_fidelity=0.99)
        # Should relax constraints
        self.assertIsNotNone(res.selected_model)

    def test_many_models(self):
        catalog = [
            ModelOption(f"m{i}", f"Model {i}", 0.01 * (i + 1), 100.0 - i * 10, 0.5 + i * 0.05)
            for i in range(10)
        ]
        router = ParetoModelRouter(catalog)
        res = router.solve()
        self.assertIsNotNone(res.selected_model)


class TestSandboxResourceScheduler(unittest.TestCase):
    """Tests for Deadlock-Free Concurrency & Sandbox Resource Allocation solver."""

    def test_basic_scheduling(self):
        requests = [
            AgentResourceRequest("ag1", "t1", ["res1"], 100.0),
            AgentResourceRequest("ag2", "t2", ["res2"], 200.0),
        ]
        scheduler = SandboxResourceScheduler(requests)
        res = scheduler.solve()
        self.assertTrue(res.zero_deadlock_certified)
        self.assertEqual(len(res.execution_sequence), 2)

    def test_empty_requests(self):
        scheduler = SandboxResourceScheduler([])
        res = scheduler.solve()
        self.assertEqual(res.execution_sequence, [])

    def test_resource_contention(self):
        requests = [
            AgentResourceRequest("ag1", "t1", ["res1"], 100.0),
            AgentResourceRequest("ag2", "t2", ["res1"], 200.0),
        ]
        scheduler = SandboxResourceScheduler(requests)
        res = scheduler.solve()
        # One must wait for the other
        self.assertGreater(res.total_wait_time_ms, 0.0)

    def test_no_contention(self):
        requests = [
            AgentResourceRequest("ag1", "t1", ["res1"], 100.0),
            AgentResourceRequest("ag2", "t2", ["res2"], 200.0),
        ]
        scheduler = SandboxResourceScheduler(requests)
        res = scheduler.solve()
        self.assertEqual(res.total_wait_time_ms, 0.0)

    def test_max_concurrent_workers(self):
        requests = [
            AgentResourceRequest("ag1", "t1", ["res1"], 100.0),
            AgentResourceRequest("ag2", "t2", ["res2"], 200.0),
            AgentResourceRequest("ag3", "t3", ["res3"], 300.0),
        ]
        scheduler = SandboxResourceScheduler(requests)
        res = scheduler.solve()
        self.assertGreaterEqual(res.max_concurrent_workers, 1)

    def test_multiple_locks(self):
        requests = [
            AgentResourceRequest("ag1", "t1", ["res1", "res2"], 100.0),
            AgentResourceRequest("ag2", "t2", ["res2", "res3"], 200.0),
        ]
        scheduler = SandboxResourceScheduler(requests)
        res = scheduler.solve()
        self.assertTrue(res.zero_deadlock_certified)

    def test_algorithm_name(self):
        requests = [AgentResourceRequest("ag1", "t1", ["res1"], 100.0)]
        scheduler = SandboxResourceScheduler(requests)
        res = scheduler.solve()
        self.assertEqual(res.algorithm, "BANKER_DISJUNCTIVE_LOCK")

    def test_execution_time(self):
        requests = [AgentResourceRequest("ag1", "t1", ["res1"], 100.0)]
        scheduler = SandboxResourceScheduler(requests)
        res = scheduler.solve()
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_single_request(self):
        requests = [AgentResourceRequest("ag1", "t1", ["res1"], 100.0)]
        scheduler = SandboxResourceScheduler(requests)
        res = scheduler.solve()
        self.assertEqual(res.execution_sequence, ["t1"])

    def test_total_wait_time(self):
        requests = [
            AgentResourceRequest("ag1", "t1", ["res1"], 100.0),
            AgentResourceRequest("ag2", "t2", ["res1"], 200.0),
        ]
        scheduler = SandboxResourceScheduler(requests)
        res = scheduler.solve()
        self.assertGreaterEqual(res.total_wait_time_ms, 0.0)

    def test_many_requests(self):
        requests = [
            AgentResourceRequest(f"ag{i}", f"t{i}", [f"res{i%3}"], float(i + 1) * 50)
            for i in range(10)
        ]
        scheduler = SandboxResourceScheduler(requests)
        res = scheduler.solve()
        self.assertEqual(len(res.execution_sequence), 10)

    def test_no_locks(self):
        requests = [AgentResourceRequest("ag1", "t1", [], 100.0)]
        scheduler = SandboxResourceScheduler(requests)
        res = scheduler.solve()
        self.assertTrue(res.zero_deadlock_certified)

    def test_shared_lock_ordering(self):
        requests = [
            AgentResourceRequest("ag1", "t1", ["res1"], 100.0),
            AgentResourceRequest("ag2", "t2", ["res1"], 50.0),
            AgentResourceRequest("ag3", "t3", ["res1"], 200.0),
        ]
        scheduler = SandboxResourceScheduler(requests)
        res = scheduler.solve()
        self.assertTrue(res.zero_deadlock_certified)


class TestLeastPrivilegeRBACSolver(unittest.TestCase):
    """Tests for Least-Privilege Dynamic Capability / Safety RBAC solver."""

    def test_basic_rbac(self):
        capabilities = [
            CapabilityRule("c1", "EXECUTE_SHELL", "repo_A", 0.5),
            CapabilityRule("c2", "WRITE_FILE", "repo_A", 0.3),
        ]
        required = [("EXECUTE_SHELL", "repo_A")]
        solver = LeastPrivilegeRBACSolver(capabilities)
        res = solver.solve(required)
        self.assertEqual(len(res.granted_capabilities), 1)
        self.assertAlmostEqual(res.total_risk_score, 0.5, places=5)

    def test_empty_capabilities(self):
        solver = LeastPrivilegeRBACSolver([])
        res = solver.solve([("EXECUTE_SHELL", "repo_A")])
        self.assertEqual(res.granted_capabilities, [])

    def test_empty_requirements(self):
        capabilities = [CapabilityRule("c1", "EXECUTE_SHELL", "repo_A", 0.5)]
        solver = LeastPrivilegeRBACSolver(capabilities)
        res = solver.solve([])
        self.assertEqual(res.granted_capabilities, [])

    def test_wildcard_action(self):
        capabilities = [
            CapabilityRule("c1", "*", "repo_A", 0.8),
            CapabilityRule("c2", "EXECUTE_SHELL", "repo_A", 0.3),
        ]
        required = [("EXECUTE_SHELL", "repo_A")]
        solver = LeastPrivilegeRBACSolver(capabilities)
        res = solver.solve(required)
        # Should prefer lower risk specific capability
        self.assertEqual(res.total_risk_score, 0.3)

    def test_wildcard_scope(self):
        capabilities = [
            CapabilityRule("c1", "EXECUTE_SHELL", "*", 0.8),
            CapabilityRule("c2", "EXECUTE_SHELL", "repo_A", 0.3),
        ]
        required = [("EXECUTE_SHELL", "repo_A")]
        solver = LeastPrivilegeRBACSolver(capabilities)
        res = solver.solve(required)
        self.assertEqual(res.total_risk_score, 0.3)

    def test_blast_radius_reduction(self):
        capabilities = [
            CapabilityRule("c1", "EXECUTE_SHELL", "repo_A", 0.5),
            CapabilityRule("c2", "WRITE_FILE", "repo_B", 0.3),
        ]
        required = [("EXECUTE_SHELL", "repo_A")]
        solver = LeastPrivilegeRBACSolver(capabilities)
        res = solver.solve(required)
        self.assertGreater(res.blast_radius_reduction_pct, 0.0)

    def test_algorithm_name(self):
        capabilities = [CapabilityRule("c1", "EXECUTE_SHELL", "repo_A", 0.5)]
        solver = LeastPrivilegeRBACSolver(capabilities)
        res = solver.solve([("EXECUTE_SHELL", "repo_A")])
        self.assertEqual(res.algorithm, "MIN_RISK_SET_COVER_RBAC")

    def test_execution_time(self):
        capabilities = [CapabilityRule("c1", "EXECUTE_SHELL", "repo_A", 0.5)]
        solver = LeastPrivilegeRBACSolver(capabilities)
        res = solver.solve([("EXECUTE_SHELL", "repo_A")])
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_multiple_requirements(self):
        capabilities = [
            CapabilityRule("c1", "EXECUTE_SHELL", "repo_A", 0.5),
            CapabilityRule("c2", "WRITE_FILE", "repo_A", 0.3),
            CapabilityRule("c3", "READ_FILE", "repo_A", 0.1),
        ]
        required = [
            ("EXECUTE_SHELL", "repo_A"),
            ("WRITE_FILE", "repo_A"),
        ]
        solver = LeastPrivilegeRBACSolver(capabilities)
        res = solver.solve(required)
        self.assertEqual(len(res.granted_capabilities), 2)

    def test_unable_to_cover(self):
        capabilities = [
            CapabilityRule("c1", "EXECUTE_SHELL", "repo_A", 0.5),
        ]
        required = [("NETWORK_EGRESS", "repo_A")]
        solver = LeastPrivilegeRBACSolver(capabilities)
        res = solver.solve(required)
        self.assertEqual(res.granted_capabilities, [])

    def test_zero_risk(self):
        capabilities = [
            CapabilityRule("c1", "READ_FILE", "repo_A", 0.0),
        ]
        required = [("READ_FILE", "repo_A")]
        solver = LeastPrivilegeRBACSolver(capabilities)
        res = solver.solve(required)
        self.assertEqual(res.total_risk_score, 0.0)

    def test_many_capabilities(self):
        capabilities = [
            CapabilityRule(f"c{i}", f"ACTION_{i}", f"repo_{i%3}", 0.1 * (i + 1))
            for i in range(10)
        ]
        required = [(f"ACTION_{i}", f"repo_{i%3}") for i in range(5)]
        solver = LeastPrivilegeRBACSolver(capabilities)
        res = solver.solve(required)
        self.assertGreater(len(res.granted_capabilities), 0)

    def test_scope_prefix_match(self):
        capabilities = [
            CapabilityRule("c1", "EXECUTE_SHELL", "repo_*", 0.5),
        ]
        required = [("EXECUTE_SHELL", "repo_A")]
        solver = LeastPrivilegeRBACSolver(capabilities)
        res = solver.solve(required)
        self.assertEqual(len(res.granted_capabilities), 1)


class TestByzantineAgentConsensus(unittest.TestCase):
    """Tests for Byzantine Agent Verification & Equivocation Consensus solver."""

    def test_basic_consensus(self):
        nodes = ["a1", "a2", "a3", "a4", "a5", "a6", "a7"]
        receipts = [
            AgentExecutionReceipt(f"a{i}", "task1", f"root_{i%2}", f"hash_{i}", f"sig_{i}")
            for i in range(1, 8)
        ]
        consensus = ByzantineAgentConsensus(nodes)
        res = consensus.verify_and_agree(receipts)
        self.assertIsInstance(res.bft_agreement_reached, bool)

    def test_empty_receipts(self):
        nodes = ["a1", "a2", "a3"]
        consensus = ByzantineAgentConsensus(nodes)
        res = consensus.verify_and_agree([])
        self.assertFalse(res.bft_agreement_reached)

    def test_equivocation_detection(self):
        nodes = ["a1", "a2", "a3", "a4", "a5", "a6", "a7"]
        receipts = [
            AgentExecutionReceipt("a1", "task1", "root_A", "h1", "s1"),
            AgentExecutionReceipt("a1", "task1", "root_B", "h2", "s2"),  # Equivocation!
            AgentExecutionReceipt("a2", "task1", "root_A", "h3", "s3"),
            AgentExecutionReceipt("a3", "task1", "root_A", "h4", "s4"),
            AgentExecutionReceipt("a4", "task1", "root_A", "h5", "s5"),
            AgentExecutionReceipt("a5", "task1", "root_A", "h6", "s6"),
            AgentExecutionReceipt("a6", "task1", "root_A", "h7", "s7"),
        ]
        consensus = ByzantineAgentConsensus(nodes)
        res = consensus.verify_and_agree(receipts)
        self.assertIn("a1", res.quarantine_traitors)

    def test_supermajority_consensus(self):
        nodes = ["a1", "a2", "a3", "a4", "a5", "a6", "a7"]
        receipts = [
            AgentExecutionReceipt(f"a{i}", "task1", "root_A", f"h{i}", f"s{i}")
            for i in range(1, 8)
        ]
        consensus = ByzantineAgentConsensus(nodes)
        res = consensus.verify_and_agree(receipts)
        self.assertTrue(res.bft_agreement_reached)
        self.assertEqual(res.consensus_state_root, "root_A")

    def test_no_consensus(self):
        nodes = ["a1", "a2", "a3", "a4", "a5", "a6", "a7"]
        receipts = [
            AgentExecutionReceipt(f"a{i}", "task1", f"root_{i}", f"h{i}", f"s{i}")
            for i in range(1, 8)
        ]
        consensus = ByzantineAgentConsensus(nodes)
        res = consensus.verify_and_agree(receipts)
        # No supermajority
        self.assertFalse(res.bft_agreement_reached)

    def test_merkle_validity(self):
        nodes = ["a1", "a2", "a3", "a4", "a5", "a6", "a7"]
        receipts = [
            AgentExecutionReceipt(f"a{i}", "task1", "root_A", f"h{i}", f"s{i}")
            for i in range(1, 8)
        ]
        consensus = ByzantineAgentConsensus(nodes)
        res = consensus.verify_and_agree(receipts)
        self.assertTrue(res.merkle_validity_certified)

    def test_algorithm_name(self):
        nodes = ["a1", "a2", "a3"]
        consensus = ByzantineAgentConsensus(nodes)
        res = consensus.verify_and_agree([])
        self.assertEqual(res.algorithm, "BFT_3PHASE_MERKLE_CONSENSUS")

    def test_execution_time(self):
        nodes = ["a1", "a2", "a3"]
        consensus = ByzantineAgentConsensus(nodes)
        res = consensus.verify_and_agree([])
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_dissenter_quarantine(self):
        nodes = ["a1", "a2", "a3", "a4", "a5", "a6", "a7"]
        receipts = [
            AgentExecutionReceipt("a1", "task1", "root_A", "h1", "s1"),
            AgentExecutionReceipt("a2", "task1", "root_A", "h2", "s2"),
            AgentExecutionReceipt("a3", "task1", "root_A", "h3", "s3"),
            AgentExecutionReceipt("a4", "task1", "root_A", "h4", "s4"),
            AgentExecutionReceipt("a5", "task1", "root_A", "h5", "s5"),
            AgentExecutionReceipt("a6", "task1", "root_B", "h6", "s6"),  # Dissenter
            AgentExecutionReceipt("a7", "task1", "root_A", "h7", "s7"),
        ]
        consensus = ByzantineAgentConsensus(nodes)
        res = consensus.verify_and_agree(receipts)
        self.assertIn("a6", res.quarantine_traitors)

    def test_small_network(self):
        nodes = ["a1", "a2", "a3"]
        receipts = [
            AgentExecutionReceipt("a1", "task1", "root_A", "h1", "s1"),
            AgentExecutionReceipt("a2", "task1", "root_A", "h2", "s2"),
            AgentExecutionReceipt("a3", "task1", "root_A", "h3", "s3"),
        ]
        consensus = ByzantineAgentConsensus(nodes)
        res = consensus.verify_and_agree(receipts)
        self.assertTrue(res.bft_agreement_reached)

    def test_single_node(self):
        nodes = ["a1"]
        receipts = [AgentExecutionReceipt("a1", "task1", "root_A", "h1", "s1")]
        consensus = ByzantineAgentConsensus(nodes)
        res = consensus.verify_and_agree(receipts)
        self.assertTrue(res.bft_agreement_reached)

    def test_many_agents(self):
        nodes = [f"a{i}" for i in range(13)]
        receipts = [
            AgentExecutionReceipt(f"a{i}", "task1", "root_A", f"h{i}", f"s{i}")
            for i in range(13)
        ]
        consensus = ByzantineAgentConsensus(nodes)
        res = consensus.verify_and_agree(receipts)
        self.assertTrue(res.bft_agreement_reached)

    def test_consensus_root_value(self):
        nodes = ["a1", "a2", "a3", "a4", "a5", "a6", "a7"]
        receipts = [
            AgentExecutionReceipt(f"a{i}", "task1", "root_X", f"h{i}", f"s{i}")
            for i in range(1, 8)
        ]
        consensus = ByzantineAgentConsensus(nodes)
        res = consensus.verify_and_agree(receipts)
        self.assertEqual(res.consensus_state_root, "root_X")


if __name__ == '__main__':
    unittest.main()
