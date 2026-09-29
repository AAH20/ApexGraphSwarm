"""Comprehensive unit test suite for the 10 Apex NP-Hard Agentic AI Solvers."""
import unittest
import math
from agentic_np_hard_kernel.engine import AgenticNPHardEngine
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

class TestAgenticNPHardSolvers(unittest.TestCase):

    def setUp(self):
        self.engine = AgenticNPHardEngine()

    # 1. Combinatorial Tool Routing
    def test_combinatorial_tool_routing(self):
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
        self.assertGreater(res.total_utility, 1.5)

    # 2. Workflow DAG Synthesis (CPM)
    def test_workflow_dag_synthesis(self):
        tasks = [
            SubTask("A", "Task A", 10.0, [], "ROLE_1"),
            SubTask("B", "Task B", 20.0, ["A"], "ROLE_2"),
            SubTask("C", "Task C", 15.0, ["A"], "ROLE_3"),
            SubTask("D", "Task D", 25.0, ["B", "C"], "ROLE_4"),
        ]
        synth = WorkflowDAGSynthesizer(tasks)
        res = synth.solve()

        # Makespan must be A (10) + B (20) + D (25) = 55
        self.assertEqual(res.total_makespan_ms, 55.0)
        self.assertEqual(res.critical_path, ["A", "B", "D"])
        self.assertEqual(res.task_schedule["A"], 0.0)
        self.assertEqual(res.task_schedule["B"], 10.0)
        self.assertEqual(res.task_schedule["D"], 30.0)

    # 3. Shared Prefix-KV Cache
    def test_prefix_kv_cache(self):
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

    # 4. Speculative Tree Search
    def test_speculative_tree_search(self):
        nodes = [
            SpeculativeActionNode("N0", None, "Root", 0, 0.5, False, 0),
            SpeculativeActionNode("N1", "N0", "Branch 1", 500, 0.85, True, 1),
            SpeculativeActionNode("N2", "N0", "Branch 2", 800, 0.95, True, 1),
            SpeculativeActionNode("N3", "N0", "Branch 3 Too Expensive", 5000, 0.99, True, 1),
        ]
        solver = SpeculativeTreeSearchSolver(nodes, token_budget=1000)
        res = solver.solve()

        self.assertEqual(res.optimal_path, ["N0", "N2"])
        self.assertEqual(res.highest_verification_score, 0.95)
        self.assertGreaterEqual(res.nodes_pruned, 1)

    # 5. Fault-Tolerant Reconfiguration
    def test_fault_tolerant_dag_reconfiguration(self):
        tasks = [
            SubTask("T1", "Initial", 10.0, [], "R1"),
            SubTask("T2", "Fails", 30.0, ["T1"], "R2"),
            SubTask("T3", "Final", 20.0, ["T2"], "R3"),
        ]
        healer = SelfHealingDAGReconfigurator(tasks)
        fail = TaskFailureEvent("T2", "TIMEOUT", ["T2_ALT"])
        fallbacks = {
            "T2_ALT": SubTask("T2_ALT", "Fast alternative", 15.0, [], "R2")
        }
        res = healer.reconfigure(fail, fallbacks)

        self.assertEqual(res.tasks_rerouted, 1)
        self.assertIn("T2_ALT", res.repaired_schedule)
        self.assertNotIn("T2", res.repaired_schedule)
        self.assertEqual(res.repaired_schedule["T2_ALT"], 10.0)
        self.assertEqual(res.repaired_schedule["T3"], 25.0)

    # 6. Submodular Memory Retrieval
    def test_submodular_memory_retrieval(self):
        pool = [
            AgentMemoryRecord("M1", "A", "Record A1", 0.9, 1.0, [1.0, 0.0]),
            AgentMemoryRecord("M2", "A", "Record A2 Duplicate", 0.88, 2.0, [0.99, 0.01]),
            AgentMemoryRecord("M3", "B", "Record B1 Novel", 0.85, 3.0, [0.0, 1.0]),
        ]
        retriever = SubmodularMemoryRetriever(pool, diversity_penalty=0.5)
        res = retriever.solve(k_records=2)

        self.assertEqual(len(res.retrieved_records), 2)
        rec_ids = {r.memory_id for r in res.retrieved_records}
        self.assertIn("M1", rec_ids)
        self.assertIn("M3", rec_ids)  # M3 selected for diversity over duplicate M2
        self.assertGreater(res.semantic_diversity, 0.5)

    # 7. Multi-Objective Model Routing
    def test_pareto_model_routing(self):
        catalog = [
            ModelOption("CHEAP_FAST", "Cheap-Fast", 0.1, 20.0, 0.70),
            ModelOption("EXPENSIVE_ACCURATE", "Frontier", 2.0, 200.0, 0.95),
            ModelOption("DOMINATED", "Worst-of-Both", 5.0, 500.0, 0.50),
        ]
        router = ParetoModelRouter(catalog)
        res = router.solve(max_cost_budget=1.0)

        self.assertEqual(res.selected_model.model_id, "CHEAP_FAST")
        self.assertTrue(res.is_pareto_optimal)
        self.assertGreater(res.hypervolume_delta, 0.0)

    # 8. Deadlock-Free Sandbox Concurrency
    def test_sandbox_resource_scheduler(self):
        reqs = [
            AgentResourceRequest("AG1", "T1", ["LOCK_A", "LOCK_B"], 50.0),
            AgentResourceRequest("AG2", "T2", ["LOCK_B", "LOCK_C"], 50.0),
            AgentResourceRequest("AG3", "T3", ["LOCK_C", "LOCK_A"], 50.0),
        ]
        scheduler = SandboxResourceScheduler(reqs)
        res = scheduler.solve()

        self.assertTrue(res.zero_deadlock_certified)
        self.assertEqual(len(res.execution_sequence), 3)

    # 9. Least-Privilege RBAC
    def test_least_privilege_rbac(self):
        rules = [
            CapabilityRule("CAP_RO_DB", "READ", "db:*", 2.0),
            CapabilityRule("CAP_RW_USERS", "WRITE", "db:users", 10.0),
            CapabilityRule("CAP_ADMIN", "*", "*", 100.0),
        ]
        solver = LeastPrivilegeRBACSolver(rules)
        res = solver.solve([("READ", "db:orders"), ("WRITE", "db:users")])

        granted_ids = {c.capability_id for c in res.granted_capabilities}
        self.assertIn("CAP_RO_DB", granted_ids)
        self.assertIn("CAP_RW_USERS", granted_ids)
        self.assertNotIn("CAP_ADMIN", granted_ids)
        self.assertGreater(res.blast_radius_reduction_pct, 50.0)

    # 10. Byzantine Consensus
    def test_byzantine_consensus(self):
        receipts = [
            AgentExecutionReceipt("A1", "T_HASH", "ROOT_VALID", "DIFF", "SIG1"),
            AgentExecutionReceipt("A2", "T_HASH", "ROOT_VALID", "DIFF", "SIG2"),
            AgentExecutionReceipt("A3", "T_HASH", "ROOT_VALID", "DIFF", "SIG3"),
            AgentExecutionReceipt("A4", "T_HASH", "ROOT_TRAITOR", "DIFF_FORGED", "SIG4"),
        ]
        bft = ByzantineAgentConsensus(["A1", "A2", "A3", "A4"])
        res = bft.verify_and_agree(receipts)

        self.assertTrue(res.bft_agreement_reached)
        self.assertEqual(res.consensus_state_root, "ROOT_VALID")
        self.assertEqual(res.quarantine_traitors, ["A4"])

if __name__ == "__main__":
    unittest.main()
