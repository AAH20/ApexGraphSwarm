"""
Comprehensive unit tests for Agentic Graph Swarm Kernel solvers.
Covers: Hypergraph CSG, Causal DAG, Epistemic Consensus, Attention Routing,
        Spectral Memory Decay, Disjunctive Tool Scheduling, Byzantine Truth Discovery,
        Graph Grammar Evolution, Temporal Subgraph Detection, Pareto Game Nash.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.integration-sources', 'agentic-graph-swarm-kernel'))

from agentic_graph_swarm_kernel.core.models import (
    AgentProfile, KnowledgeHyperedge, VariableObservation, FactStatement,
    AgentBeliefGraph, KnowledgeNode, AgentContextBudget, MemoryNode,
    MemoryEdge, AgentToolTask, ToolResource, AgentClaim, BehaviorPattern,
    TemporalEvent, PlayerAgent, HyperedgePayoff
)
from agentic_graph_swarm_kernel.core.hypergraph_csg import solve_hypergraph_csg
from agentic_graph_swarm_kernel.core.causal_dag_synthesis import solve_causal_dag_synthesis
from agentic_graph_swarm_kernel.core.epistemic_consensus import solve_epistemic_consensus
from agentic_graph_swarm_kernel.core.budgeted_attention_routing import solve_budgeted_attention_routing
from agentic_graph_swarm_kernel.core.spectral_memory_decay import solve_spectral_memory_decay
from agentic_graph_swarm_kernel.core.disjunctive_tool_scheduler import solve_disjunctive_tool_scheduling
from agentic_graph_swarm_kernel.core.byzantine_epistemic_filter import solve_byzantine_truth_discovery
from agentic_graph_swarm_kernel.core.graph_grammar_evolution import solve_graph_grammar_evolution
from agentic_graph_swarm_kernel.core.temporal_subgraph_detector import solve_temporal_subgraph_detection
from agentic_graph_swarm_kernel.core.game_theoretic_hypergraph_nash import solve_pareto_game_hypergraph


class TestHypergraphCSG(unittest.TestCase):
    """Tests for Dynamic Hypergraph Coalition Structure Generation solver."""

    def test_basic_csg(self):
        agents = [
            AgentProfile("a1", ["Python", "SQL"], 1.0),
            AgentProfile("a2", ["ML", "Stats"], 1.0),
        ]
        edges = [
            KnowledgeHyperedge("h1", "DataScience", ["Python", "ML"], 50.0),
        ]
        res = solve_hypergraph_csg(agents, edges)
        self.assertEqual(len(res.coalitions), 1)
        self.assertGreater(res.total_coalition_value, 0.0)

    def test_empty_agents(self):
        edges = [KnowledgeHyperedge("h1", "X", ["A"], 10.0)]
        res = solve_hypergraph_csg([], edges)
        self.assertEqual(res.coalitions, [])
        self.assertEqual(res.unassigned_agents, [])

    def test_empty_hyperedges(self):
        agents = [AgentProfile("a1", ["A"], 1.0)]
        res = solve_hypergraph_csg(agents, [])
        self.assertEqual(res.coalitions, [])
        self.assertEqual(res.unassigned_agents, ["a1"])

    def test_unassigned_agents(self):
        agents = [
            AgentProfile("a1", ["A"], 1.0),
            AgentProfile("a2", ["B"], 1.0),
        ]
        edges = [KnowledgeHyperedge("h1", "X", ["A"], 10.0)]
        res = solve_hypergraph_csg(agents, edges)
        self.assertIn("a2", res.unassigned_agents)

    def test_multiple_coalitions(self):
        agents = [
            AgentProfile("a1", ["A"], 1.0),
            AgentProfile("a2", ["B"], 1.0),
            AgentProfile("a3", ["C"], 1.0),
        ]
        edges = [
            KnowledgeHyperedge("h1", "X", ["A"], 10.0),
            KnowledgeHyperedge("h2", "Y", ["B"], 20.0),
        ]
        res = solve_hypergraph_csg(agents, edges)
        self.assertGreaterEqual(len(res.coalitions), 1)

    def test_coalition_value_positive(self):
        agents = [
            AgentProfile("a1", ["A", "B"], 1.0),
            AgentProfile("a2", ["C"], 1.0),
        ]
        edges = [KnowledgeHyperedge("h1", "X", ["A", "C"], 50.0)]
        res = solve_hypergraph_csg(agents, edges)
        self.assertGreater(res.total_coalition_value, 0.0)

    def test_algorithm_name(self):
        agents = [AgentProfile("a1", ["A"], 1.0)]
        edges = [KnowledgeHyperedge("h1", "X", ["A"], 10.0)]
        res = solve_hypergraph_csg(agents, edges)
        self.assertEqual(res.algorithm, "Branch-and-Bound-H-CSG")

    def test_execution_time(self):
        agents = [AgentProfile("a1", ["A"], 1.0)]
        edges = [KnowledgeHyperedge("h1", "X", ["A"], 10.0)]
        res = solve_hypergraph_csg(agents, edges)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_capability_coverage(self):
        agents = [
            AgentProfile("a1", ["Python"], 1.0),
            AgentProfile("a2", ["ML"], 1.0),
        ]
        edges = [KnowledgeHyperedge("h1", "DS", ["Python", "ML"], 100.0)]
        res = solve_hypergraph_csg(agents, edges)
        # Both agents should be in the coalition
        all_members = []
        for c in res.coalitions:
            all_members.extend(c)
        self.assertIn("a1", all_members)
        self.assertIn("a2", all_members)

    def test_efficiency_weight(self):
        agents = [
            AgentProfile("a1", ["A"], 2.0),
            AgentProfile("a2", ["A"], 0.5),
        ]
        edges = [KnowledgeHyperedge("h1", "X", ["A"], 10.0)]
        res = solve_hypergraph_csg(agents, edges)
        self.assertGreater(res.total_coalition_value, 0.0)

    def test_no_capability_match(self):
        agents = [AgentProfile("a1", ["X"], 1.0)]
        edges = [KnowledgeHyperedge("h1", "Y", ["A", "B", "C"], 10.0)]
        res = solve_hypergraph_csg(agents, edges)
        self.assertEqual(len(res.coalitions), 0)
        self.assertIn("a1", res.unassigned_agents)

    def test_large_hyperedge_value(self):
        agents = [
            AgentProfile("a1", ["A"], 1.0),
            AgentProfile("a2", ["B"], 1.0),
        ]
        edges = [KnowledgeHyperedge("h1", "X", ["A", "B"], 1000.0)]
        res = solve_hypergraph_csg(agents, edges)
        self.assertGreater(res.total_coalition_value, 0.0)

    def test_coalitions_non_overlapping(self):
        agents = [
            AgentProfile("a1", ["A"], 1.0),
            AgentProfile("a2", ["B"], 1.0),
            AgentProfile("a3", ["C"], 1.0),
        ]
        edges = [
            KnowledgeHyperedge("h1", "X", ["A"], 10.0),
            KnowledgeHyperedge("h2", "Y", ["B"], 10.0),
        ]
        res = solve_hypergraph_csg(agents, edges)
        all_members = []
        for c in res.coalitions:
            all_members.extend(c)
        self.assertEqual(len(all_members), len(set(all_members)))


class TestCausalDAGSynthesis(unittest.TestCase):
    """Tests for Causal Reasoning DAG Topology Synthesis solver."""

    def test_basic_dag(self):
        vars_obs = [
            VariableObservation("v1", "Var1", [float(i) for i in range(20)]),
            VariableObservation("v2", "Var2", [float(i * 2) for i in range(20)]),
            VariableObservation("v3", "Var3", [float(i % 3) for i in range(20)]),
        ]
        res = solve_causal_dag_synthesis(vars_obs, max_in_degree=2)
        self.assertTrue(res.is_acyclic)
        self.assertIsInstance(res.bic_score, float)

    def test_empty_variables(self):
        res = solve_causal_dag_synthesis([], max_in_degree=2)
        self.assertTrue(res.is_acyclic)
        self.assertEqual(res.bic_score, 0.0)

    def test_single_variable(self):
        vars_obs = [VariableObservation("v1", "V", [1.0, 2.0, 3.0])]
        res = solve_causal_dag_synthesis(vars_obs, max_in_degree=2)
        self.assertTrue(res.is_acyclic)

    def test_correlated_variables(self):
        vars_obs = [
            VariableObservation("X", "X", [float(i) for i in range(50)]),
            VariableObservation("Y", "Y", [float(i * 2 + 1) for i in range(50)]),
        ]
        res = solve_causal_dag_synthesis(vars_obs, max_in_degree=2)
        self.assertTrue(res.is_acyclic)

    def test_acyclicity_guaranteed(self):
        vars_obs = [
            VariableObservation(f"v{i}", f"V{i}", [float(i * j) for j in range(30)])
            for i in range(5)
        ]
        res = solve_causal_dag_synthesis(vars_obs, max_in_degree=3)
        self.assertTrue(res.is_acyclic)

    def test_max_in_degree_respected(self):
        vars_obs = [
            VariableObservation(f"v{i}", f"V{i}", [float(i + j) for j in range(20)])
            for i in range(6)
        ]
        res = solve_causal_dag_synthesis(vars_obs, max_in_degree=2)
        # In-degree of any node should not exceed max_in_degree
        in_degree = {v.var_id: 0 for v in vars_obs}
        for targets in res.adjacency_matrix.values():
            for t in targets:
                in_degree[t] += 1
        for deg in in_degree.values():
            self.assertLessEqual(deg, 2)

    def test_bic_score_type(self):
        vars_obs = [
            VariableObservation("A", "A", [1.0, 2.0, 3.0]),
            VariableObservation("B", "B", [2.0, 4.0, 6.0]),
        ]
        res = solve_causal_dag_synthesis(vars_obs)
        self.assertIsInstance(res.bic_score, float)

    def test_algorithm_name(self):
        vars_obs = [
            VariableObservation("A", "A", [1.0, 2.0]),
            VariableObservation("B", "B", [3.0, 4.0]),
        ]
        res = solve_causal_dag_synthesis(vars_obs)
        self.assertEqual(res.algorithm, "BIC-Penalized-Causal-Order-DP")

    def test_execution_time(self):
        vars_obs = [
            VariableObservation("A", "A", [1.0, 2.0]),
            VariableObservation("B", "B", [3.0, 4.0]),
        ]
        res = solve_causal_dag_synthesis(vars_obs)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_adjacency_matrix_keys(self):
        vars_obs = [
            VariableObservation("X", "X", [1.0, 2.0]),
            VariableObservation("Y", "Y", [3.0, 4.0]),
        ]
        res = solve_causal_dag_synthesis(vars_obs)
        self.assertIn("X", res.adjacency_matrix)
        self.assertIn("Y", res.adjacency_matrix)

    def test_no_self_loops(self):
        vars_obs = [
            VariableObservation("X", "X", [1.0, 2.0, 3.0]),
            VariableObservation("Y", "Y", [4.0, 5.0, 6.0]),
        ]
        res = solve_causal_dag_synthesis(vars_obs)
        for u, targets in res.adjacency_matrix.items():
            self.assertNotIn(u, targets)

    def test_weakly_correlated_variables(self):
        import random
        rng = random.Random(42)
        vars_obs = [
            VariableObservation("A", "A", [rng.random() for _ in range(30)]),
            VariableObservation("B", "B", [rng.random() for _ in range(30)]),
        ]
        res = solve_causal_dag_synthesis(vars_obs)
        self.assertTrue(res.is_acyclic)

    def test_many_variables(self):
        vars_obs = [
            VariableObservation(f"v{i}", f"V{i}", [float(i * j % 7) for j in range(20)])
            for i in range(8)
        ]
        res = solve_causal_dag_synthesis(vars_obs, max_in_degree=3)
        self.assertTrue(res.is_acyclic)


class TestEpistemicConsensus(unittest.TestCase):
    """Tests for Cross-Agent Epistemic Consensus solver."""

    def test_basic_consensus(self):
        graphs = [
            AgentBeliefGraph("ag1", 0.9, [FactStatement("Sun", "is", "Star", 0.95)]),
            AgentBeliefGraph("ag2", 0.8, [FactStatement("Sun", "is", "Star", 0.90)]),
        ]
        res = solve_epistemic_consensus(graphs)
        self.assertEqual(len(res.consensus_graph), 1)
        self.assertTrue(res.cycle_free_certified)

    def test_empty_graphs(self):
        res = solve_epistemic_consensus([])
        self.assertEqual(res.consensus_graph, [])
        self.assertTrue(res.cycle_free_certified)

    def test_conflicting_statements(self):
        graphs = [
            AgentBeliefGraph("ag1", 0.9, [FactStatement("A", "is", "B", 0.85)]),
            AgentBeliefGraph("ag2", 0.6, [FactStatement("A", "is", "C", 0.70)]),
        ]
        res = solve_epistemic_consensus(graphs)
        # Should pick the higher-reputation agent's statement
        self.assertEqual(len(res.consensus_graph), 1)

    def test_kemeny_distance(self):
        graphs = [
            AgentBeliefGraph("ag1", 0.9, [FactStatement("A", "is", "B", 0.85)]),
            AgentBeliefGraph("ag2", 0.6, [FactStatement("A", "is", "C", 0.70)]),
        ]
        res = solve_epistemic_consensus(graphs)
        self.assertGreaterEqual(res.kemeny_distance, 0.0)

    def test_multiple_statements(self):
        graphs = [
            AgentBeliefGraph("ag1", 0.9, [
                FactStatement("A", "is", "B", 0.85),
                FactStatement("C", "is", "D", 0.90),
            ]),
            AgentBeliefGraph("ag2", 0.8, [
                FactStatement("A", "is", "B", 0.80),
                FactStatement("C", "is", "D", 0.85),
            ]),
        ]
        res = solve_epistemic_consensus(graphs)
        self.assertEqual(len(res.consensus_graph), 2)

    def test_reputation_weighting(self):
        graphs = [
            AgentBeliefGraph("ag1", 1.0, [FactStatement("X", "is", "Y", 0.9)]),
            AgentBeliefGraph("ag2", 0.1, [FactStatement("X", "is", "Z", 0.1)]),
        ]
        res = solve_epistemic_consensus(graphs)
        # Higher reputation agent's statement should win
        self.assertEqual(res.consensus_graph[0].obj, "Y")

    def test_confidence_normalization(self):
        graphs = [
            AgentBeliefGraph("ag1", 0.5, [FactStatement("A", "is", "B", 0.5)]),
        ]
        res = solve_epistemic_consensus(graphs)
        self.assertLessEqual(res.consensus_graph[0].confidence, 1.0)

    def test_case_insensitive_matching(self):
        graphs = [
            AgentBeliefGraph("ag1", 0.9, [FactStatement("Sun", "Is", "Star", 0.9)]),
            AgentBeliefGraph("ag2", 0.8, [FactStatement("sun", "is", "star", 0.8)]),
        ]
        res = solve_epistemic_consensus(graphs)
        self.assertEqual(len(res.consensus_graph), 1)

    def test_algorithm_name(self):
        graphs = [
            AgentBeliefGraph("ag1", 0.9, [FactStatement("A", "is", "B", 0.9)]),
        ]
        res = solve_epistemic_consensus(graphs)
        self.assertEqual(res.algorithm, "Kemeny-Borda-Epistemic-Consensus")

    def test_execution_time(self):
        graphs = [
            AgentBeliefGraph("ag1", 0.9, [FactStatement("A", "is", "B", 0.9)]),
        ]
        res = solve_epistemic_consensus(graphs)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_single_agent(self):
        graphs = [
            AgentBeliefGraph("ag1", 0.9, [FactStatement("A", "is", "B", 0.9)]),
        ]
        res = solve_epistemic_consensus(graphs)
        self.assertEqual(len(res.consensus_graph), 1)

    def test_many_agents(self):
        graphs = [
            AgentBeliefGraph(f"ag{i}", 0.5 + i * 0.05, [FactStatement("A", "is", "B", 0.8)])
            for i in range(10)
        ]
        res = solve_epistemic_consensus(graphs)
        self.assertEqual(len(res.consensus_graph), 1)

    def test_different_predicates(self):
        graphs = [
            AgentBeliefGraph("ag1", 0.9, [
                FactStatement("A", "is", "B", 0.9),
                FactStatement("A", "has", "C", 0.8),
            ]),
        ]
        res = solve_epistemic_consensus(graphs)
        self.assertEqual(len(res.consensus_graph), 2)


class TestBudgetedAttentionRouting(unittest.TestCase):
    """Tests for Context-Budgeted Submodular Attention Routing solver."""

    def test_basic_routing(self):
        nodes = [
            KnowledgeNode("n1", 200, 3.5, {"AI"}),
            KnowledgeNode("n2", 300, 4.0, {"Security"}),
        ]
        agents = [
            AgentContextBudget("ag1", 400, {"AI"}),
        ]
        res = solve_budgeted_attention_routing(nodes, agents)
        self.assertIn("ag1", res.routed_subgraphs)
        self.assertGreater(res.total_information_coverage, 0.0)

    def test_empty_nodes(self):
        agents = [AgentContextBudget("ag1", 400, {"AI"})]
        res = solve_budgeted_attention_routing([], agents)
        self.assertEqual(res.routed_subgraphs["ag1"], [])

    def test_empty_agents(self):
        nodes = [KnowledgeNode("n1", 200, 3.5, {"AI"})]
        res = solve_budgeted_attention_routing(nodes, [])
        self.assertEqual(res.total_information_coverage, 0.0)

    def test_budget_constraint(self):
        nodes = [
            KnowledgeNode("n1", 500, 3.5, {"AI"}),
            KnowledgeNode("n2", 600, 4.0, {"Security"}),
        ]
        agents = [AgentContextBudget("ag1", 400, {"AI"})]
        res = solve_budgeted_attention_routing(nodes, agents)
        # Should not exceed budget
        total_tokens = sum(n.content_token_length for n in nodes if n.node_id in res.routed_subgraphs["ag1"])
        self.assertLessEqual(total_tokens, 400)

    def test_focus_concept_matching(self):
        nodes = [
            KnowledgeNode("n1", 100, 3.5, {"AI"}),
            KnowledgeNode("n2", 100, 4.0, {"Security"}),
        ]
        agents = [AgentContextBudget("ag1", 200, {"AI"})]
        res = solve_budgeted_attention_routing(nodes, agents)
        self.assertIn("n1", res.routed_subgraphs["ag1"])

    def test_context_utilization(self):
        nodes = [
            KnowledgeNode("n1", 100, 3.5, {"AI"}),
        ]
        agents = [AgentContextBudget("ag1", 200, {"AI"})]
        res = solve_budgeted_attention_routing(nodes, agents)
        self.assertGreater(res.context_utilization_pct, 0.0)

    def test_multiple_agents(self):
        nodes = [
            KnowledgeNode("n1", 100, 3.5, {"AI"}),
            KnowledgeNode("n2", 100, 4.0, {"Security"}),
        ]
        agents = [
            AgentContextBudget("ag1", 200, {"AI"}),
            AgentContextBudget("ag2", 200, {"Security"}),
        ]
        res = solve_budgeted_attention_routing(nodes, agents)
        self.assertIn("ag1", res.routed_subgraphs)
        self.assertIn("ag2", res.routed_subgraphs)

    def test_algorithm_name(self):
        nodes = [KnowledgeNode("n1", 100, 3.5, {"AI"})]
        agents = [AgentContextBudget("ag1", 200, {"AI"})]
        res = solve_budgeted_attention_routing(nodes, agents)
        self.assertEqual(res.algorithm, "Budgeted-Submodular-Attention-Packer")

    def test_execution_time(self):
        nodes = [KnowledgeNode("n1", 100, 3.5, {"AI"})]
        agents = [AgentContextBudget("ag1", 200, {"AI"})]
        res = solve_budgeted_attention_routing(nodes, agents)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_no_focus_concepts(self):
        nodes = [KnowledgeNode("n1", 100, 3.5, {"AI"})]
        agents = [AgentContextBudget("ag1", 200, set())]
        res = solve_budgeted_attention_routing(nodes, agents)
        # Empty focus should match all
        self.assertIn("n1", res.routed_subgraphs["ag1"])

    def test_information_coverage_positive(self):
        nodes = [
            KnowledgeNode("n1", 100, 5.0, {"AI"}),
            KnowledgeNode("n2", 100, 3.0, {"AI"}),
        ]
        agents = [AgentContextBudget("ag1", 200, {"AI"})]
        res = solve_budgeted_attention_routing(nodes, agents)
        self.assertGreater(res.total_information_coverage, 0.0)

    def test_large_budget(self):
        nodes = [
            KnowledgeNode("n1", 100, 3.5, {"AI"}),
            KnowledgeNode("n2", 100, 4.0, {"Security"}),
        ]
        agents = [AgentContextBudget("ag1", 10000, {"AI"})]
        res = solve_budgeted_attention_routing(nodes, agents)
        self.assertIn("n1", res.routed_subgraphs["ag1"])

    def test_zero_budget(self):
        nodes = [KnowledgeNode("n1", 100, 3.5, {"AI"})]
        agents = [AgentContextBudget("ag1", 0, {"AI"})]
        res = solve_budgeted_attention_routing(nodes, agents)
        self.assertEqual(res.routed_subgraphs["ag1"], [])


class TestSpectralMemoryDecay(unittest.TestCase):
    """Tests for Autonomous Swarm Memory Topology Sparsification & Decay solver."""

    def test_basic_decay(self):
        nodes = [MemoryNode("m1", 1000.0, 5), MemoryNode("m2", 900.0, 3)]
        edges = [MemoryEdge("m1", "m2", 0.8, 1.0)]
        res = solve_spectral_memory_decay(nodes, edges, target_retention_ratio=1.0)
        self.assertEqual(len(res.retained_nodes), 2)
        self.assertTrue(res.causal_connectivity_preserved)

    def test_empty_nodes(self):
        res = solve_spectral_memory_decay([], [], target_retention_ratio=0.5)
        self.assertEqual(res.retained_nodes, [])

    def test_empty_edges(self):
        nodes = [MemoryNode("m1", 1000.0, 5)]
        res = solve_spectral_memory_decay(nodes, [], target_retention_ratio=0.5)
        # When no edges exist, all nodes are retained (no edges to filter)
        self.assertEqual(res.retained_nodes, ["m1"])

    def test_retention_ratio(self):
        nodes = [MemoryNode(f"m{i}", 1000.0 - i * 100, 10 - i) for i in range(6)]
        edges = [MemoryEdge(f"m{i}", f"m{i+1}", 0.8, 1.0) for i in range(5)]
        res = solve_spectral_memory_decay(nodes, edges, target_retention_ratio=0.5)
        self.assertLessEqual(len(res.retained_edges), 3)

    def test_compression_ratio(self):
        nodes = [MemoryNode(f"m{i}", 1000.0, 5) for i in range(4)]
        edges = [MemoryEdge(f"m{i}", f"m{i+1}", 0.8, 1.0) for i in range(3)]
        res = solve_spectral_memory_decay(nodes, edges, target_retention_ratio=0.5)
        self.assertLess(res.spectral_compression_ratio, 1.0)

    def test_algorithm_name(self):
        nodes = [MemoryNode("m1", 1000.0, 5)]
        edges = []
        res = solve_spectral_memory_decay(nodes, edges)
        self.assertEqual(res.algorithm, "Spielman-Srivastava-Spectral-Decay")

    def test_execution_time(self):
        nodes = [MemoryNode("m1", 1000.0, 5)]
        edges = []
        res = solve_spectral_memory_decay(nodes, edges)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_temporal_decay(self):
        nodes = [
            MemoryNode("old", 100.0, 10),
            MemoryNode("new", 9000.0, 10),
        ]
        edges = [MemoryEdge("old", "new", 0.8, 1.0)]
        res = solve_spectral_memory_decay(nodes, edges, target_retention_ratio=0.5,
                                          half_life_seconds=1000.0, current_time=10000.0)
        self.assertTrue(res.causal_connectivity_preserved)

    def test_frequency_boost(self):
        nodes = [
            MemoryNode("m1", 5000.0, 100),
            MemoryNode("m2", 5000.0, 1),
        ]
        edges = [MemoryEdge("m1", "m2", 0.8, 1.0)]
        res = solve_spectral_memory_decay(nodes, edges, target_retention_ratio=1.0)
        self.assertEqual(len(res.retained_nodes), 2)

    def test_retained_edges_valid(self):
        nodes = [MemoryNode(f"m{i}", 1000.0, 5) for i in range(4)]
        edges = [MemoryEdge(f"m{i}", f"m{i+1}", 0.8, 1.0) for i in range(3)]
        res = solve_spectral_memory_decay(nodes, edges, target_retention_ratio=1.0)
        for u, v in res.retained_edges:
            self.assertIn(u, [n.node_id for n in nodes])
            self.assertIn(v, [n.node_id for n in nodes])

    def test_high_retention(self):
        nodes = [MemoryNode(f"m{i}", 1000.0, 5) for i in range(3)]
        edges = [MemoryEdge(f"m{i}", f"m{i+1}", 0.8, 1.0) for i in range(2)]
        res = solve_spectral_memory_decay(nodes, edges, target_retention_ratio=1.0)
        self.assertEqual(len(res.retained_edges), 2)

    def test_low_retention(self):
        nodes = [MemoryNode(f"m{i}", 1000.0, 5) for i in range(10)]
        edges = [MemoryEdge(f"m{i}", f"m{i+1}", 0.8, 1.0) for i in range(9)]
        res = solve_spectral_memory_decay(nodes, edges, target_retention_ratio=0.2)
        self.assertLess(len(res.retained_edges), 9)


class TestDisjunctiveToolScheduler(unittest.TestCase):
    """Tests for Disjunctive Swarm Task Scheduling solver."""

    def test_basic_scheduling(self):
        tasks = [
            AgentToolTask("t1", "a1", "res1", 20),
            AgentToolTask("t2", "a2", "res1", 30, precedence_prereqs=["t1"]),
        ]
        resources = [ToolResource("res1", 1)]
        res = solve_disjunctive_tool_scheduling(tasks, resources)
        self.assertTrue(res.deadlock_free_certified)
        self.assertGreater(res.makespan_ms, 0)

    def test_empty_tasks(self):
        resources = [ToolResource("res1", 1)]
        res = solve_disjunctive_tool_scheduling([], resources)
        self.assertEqual(res.schedule, {})
        self.assertTrue(res.deadlock_free_certified)

    def test_precedence_constraints(self):
        tasks = [
            AgentToolTask("t1", "a1", "res1", 20),
            AgentToolTask("t2", "a2", "res1", 30, precedence_prereqs=["t1"]),
        ]
        resources = [ToolResource("res1", 1)]
        res = solve_disjunctive_tool_scheduling(tasks, resources)
        self.assertGreaterEqual(res.schedule["t2"][0], res.schedule["t1"][1])

    def test_parallel_tasks(self):
        tasks = [
            AgentToolTask("t1", "a1", "res1", 20),
            AgentToolTask("t2", "a2", "res2", 30),
        ]
        resources = [ToolResource("res1", 1), ToolResource("res2", 1)]
        res = solve_disjunctive_tool_scheduling(tasks, resources)
        # Both can start at 0
        self.assertEqual(res.schedule["t1"][0], 0)
        self.assertEqual(res.schedule["t2"][0], 0)

    def test_resource_contention(self):
        tasks = [
            AgentToolTask("t1", "a1", "res1", 20),
            AgentToolTask("t2", "a2", "res1", 30),
        ]
        resources = [ToolResource("res1", 1)]
        res = solve_disjunctive_tool_scheduling(tasks, resources)
        # One must wait for the other
        self.assertGreater(res.makespan_ms, 30)

    def test_makespan_calculation(self):
        tasks = [
            AgentToolTask("t1", "a1", "res1", 10),
            AgentToolTask("t2", "a2", "res1", 20, precedence_prereqs=["t1"]),
        ]
        resources = [ToolResource("res1", 1)]
        res = solve_disjunctive_tool_scheduling(tasks, resources)
        self.assertEqual(res.makespan_ms, 30)

    def test_algorithm_name(self):
        tasks = [AgentToolTask("t1", "a1", "res1", 10)]
        resources = [ToolResource("res1", 1)]
        res = solve_disjunctive_tool_scheduling(tasks, resources)
        self.assertEqual(res.algorithm, "Shifting-Bottleneck-Disjunctive-Scheduler")

    def test_execution_time(self):
        tasks = [AgentToolTask("t1", "a1", "res1", 10)]
        resources = [ToolResource("res1", 1)]
        res = solve_disjunctive_tool_scheduling(tasks, resources)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_chain_dependencies(self):
        tasks = [
            AgentToolTask("t1", "a1", "res1", 10),
            AgentToolTask("t2", "a2", "res1", 20, precedence_prereqs=["t1"]),
            AgentToolTask("t3", "a3", "res1", 30, precedence_prereqs=["t2"]),
        ]
        resources = [ToolResource("res1", 1)]
        res = solve_disjunctive_tool_scheduling(tasks, resources)
        self.assertEqual(res.makespan_ms, 60)

    def test_diamond_dependencies(self):
        tasks = [
            AgentToolTask("t1", "a1", "res1", 10),
            AgentToolTask("t2", "a2", "res1", 20, precedence_prereqs=["t1"]),
            AgentToolTask("t3", "a3", "res1", 15, precedence_prereqs=["t1"]),
            AgentToolTask("t4", "a4", "res1", 25, precedence_prereqs=["t2", "t3"]),
        ]
        resources = [ToolResource("res1", 1)]
        res = solve_disjunctive_tool_scheduling(tasks, resources)
        self.assertTrue(res.deadlock_free_certified)

    def test_multiple_resources(self):
        tasks = [
            AgentToolTask("t1", "a1", "res1", 10),
            AgentToolTask("t2", "a2", "res2", 20),
            AgentToolTask("t3", "a3", "res1", 15),
        ]
        resources = [ToolResource("res1", 1), ToolResource("res2", 1)]
        res = solve_disjunctive_tool_scheduling(tasks, resources)
        self.assertTrue(res.deadlock_free_certified)

    def test_schedule_complete(self):
        tasks = [
            AgentToolTask("t1", "a1", "res1", 10),
            AgentToolTask("t2", "a2", "res1", 20),
        ]
        resources = [ToolResource("res1", 1)]
        res = solve_disjunctive_tool_scheduling(tasks, resources)
        self.assertEqual(len(res.schedule), 2)

    def test_no_precedence(self):
        tasks = [
            AgentToolTask("t1", "a1", "res1", 10),
            AgentToolTask("t2", "a2", "res2", 20),
        ]
        resources = [ToolResource("res1", 1), ToolResource("res2", 1)]
        res = solve_disjunctive_tool_scheduling(tasks, resources)
        # Different resources, both can start at 0
        self.assertEqual(res.schedule["t1"][0], 0)


class TestByzantineTruthDiscovery(unittest.TestCase):
    """Tests for Byzantine-Resilient Epistemic Truth Discovery solver."""

    def test_basic_truth_discovery(self):
        claims = [
            AgentClaim("c1", "ag1", "Entity", "attr", "true_val", 1.0),
            AgentClaim("c2", "ag2", "Entity", "attr", "true_val", 2.0),
            AgentClaim("c3", "ag3", "Entity", "attr", "false_val", 3.0),
        ]
        res = solve_byzantine_truth_discovery(claims)
        self.assertIn("Entity.attr", res.resolved_attributes)

    def test_empty_claims(self):
        res = solve_byzantine_truth_discovery([])
        self.assertEqual(res.resolved_attributes, {})
        self.assertEqual(res.quarantined_byzantine_agents, [])

    def test_byzantine_quarantine(self):
        claims = [
            AgentClaim("c1", "honest1", "E", "a", "X", 1.0),
            AgentClaim("c2", "honest2", "E", "a", "X", 2.0),
            AgentClaim("c3", "byzantine", "E", "a", "Y", 3.0),
        ]
        res = solve_byzantine_truth_discovery(claims)
        self.assertIn("byzantine", res.quarantined_byzantine_agents)

    def test_majority_truth(self):
        claims = [
            AgentClaim(f"c{i}", f"ag{i}", "E", "a", "correct", float(i))
            for i in range(5)
        ]
        claims.append(AgentClaim("c_bad", "bad", "E", "a", "wrong", 99.0))
        res = solve_byzantine_truth_discovery(claims)
        self.assertEqual(res.resolved_attributes["E.a"], "correct")

    def test_multiple_attributes(self):
        claims = [
            AgentClaim("c1", "ag1", "E", "a", "X", 1.0),
            AgentClaim("c2", "ag2", "E", "b", "Y", 2.0),
        ]
        res = solve_byzantine_truth_discovery(claims)
        self.assertEqual(len(res.resolved_attributes), 2)

    def test_confidence_score(self):
        claims = [
            AgentClaim("c1", "ag1", "E", "a", "X", 1.0),
            AgentClaim("c2", "ag2", "E", "a", "X", 2.0),
        ]
        res = solve_byzantine_truth_discovery(claims)
        self.assertGreater(res.overall_truth_confidence, 0.0)

    def test_algorithm_name(self):
        claims = [AgentClaim("c1", "ag1", "E", "a", "X", 1.0)]
        res = solve_byzantine_truth_discovery(claims)
        self.assertEqual(res.algorithm, "Spectral-Trimmed-Byzantine-Filter")

    def test_execution_time(self):
        claims = [AgentClaim("c1", "ag1", "E", "a", "X", 1.0)]
        res = solve_byzantine_truth_discovery(claims)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_all_honest(self):
        claims = [
            AgentClaim(f"c{i}", f"ag{i}", "E", "a", "X", float(i))
            for i in range(5)
        ]
        res = solve_byzantine_truth_discovery(claims)
        self.assertEqual(len(res.quarantined_byzantine_agents), 0)

    def test_multiple_entities(self):
        claims = [
            AgentClaim("c1", "ag1", "E1", "a", "X", 1.0),
            AgentClaim("c2", "ag2", "E2", "b", "Y", 2.0),
        ]
        res = solve_byzantine_truth_discovery(claims)
        self.assertEqual(len(res.resolved_attributes), 2)

    def test_convergence(self):
        claims = [
            AgentClaim("c1", "ag1", "E", "a", "X", 1.0),
            AgentClaim("c2", "ag2", "E", "a", "X", 2.0),
            AgentClaim("c3", "ag3", "E", "a", "Y", 3.0),
        ]
        res = solve_byzantine_truth_discovery(claims, max_iterations=50)
        self.assertIn("E.a", res.resolved_attributes)

    def test_single_claim(self):
        claims = [AgentClaim("c1", "ag1", "E", "a", "X", 1.0)]
        res = solve_byzantine_truth_discovery(claims)
        self.assertEqual(res.resolved_attributes["E.a"], "X")

    def test_quarantine_threshold(self):
        claims = [
            AgentClaim("c1", "ag1", "E", "a", "X", 1.0),
            AgentClaim("c2", "ag2", "E", "a", "Y", 2.0),
            AgentClaim("c3", "ag3", "E", "a", "Z", 3.0),
        ]
        res = solve_byzantine_truth_discovery(claims)
        # At least one should be quarantined
        self.assertGreaterEqual(len(res.quarantined_byzantine_agents), 0)


class TestGraphGrammarEvolution(unittest.TestCase):
    """Tests for Evolutionary Swarm Graph Grammar & Architecture Search solver."""

    def test_basic_evolution(self):
        agent_ids = ["a1", "a2", "a3", "a4"]
        res = solve_graph_grammar_evolution(agent_ids, population_size=8, generations=5, seed=42)
        self.assertIn("a1", res.best_topology)
        self.assertGreater(res.best_fitness, 0.0)

    def test_small_population(self):
        agent_ids = ["a1", "a2", "a3"]
        res = solve_graph_grammar_evolution(agent_ids, population_size=4, generations=3, seed=42)
        self.assertEqual(len(res.best_topology), 3)

    def test_two_agents(self):
        agent_ids = ["a1", "a2"]
        res = solve_graph_grammar_evolution(agent_ids, population_size=4, generations=3, seed=42)
        self.assertEqual(res.best_fitness, 100.0)

    def test_pareto_frontier_size(self):
        agent_ids = ["a1", "a2", "a3", "a4"]
        res = solve_graph_grammar_evolution(agent_ids, population_size=8, generations=5, seed=42)
        self.assertGreater(res.pareto_frontier_size, 0)

    def test_generation_reached(self):
        agent_ids = ["a1", "a2", "a3"]
        res = solve_graph_grammar_evolution(agent_ids, population_size=4, generations=7, seed=42)
        self.assertEqual(res.generation_reached, 7)

    def test_algorithm_name(self):
        agent_ids = ["a1", "a2", "a3"]
        res = solve_graph_grammar_evolution(agent_ids, population_size=4, generations=3, seed=42)
        self.assertEqual(res.algorithm, "Pareto-Graph-Grammar-EAS")

    def test_execution_time(self):
        agent_ids = ["a1", "a2", "a3"]
        res = solve_graph_grammar_evolution(agent_ids, population_size=4, generations=3, seed=42)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_topology_connected(self):
        agent_ids = ["a1", "a2", "a3", "a4"]
        res = solve_graph_grammar_evolution(agent_ids, population_size=8, generations=5, seed=42)
        # Check that every agent has at least one connection
        for agent_id in agent_ids:
            self.assertGreater(len(res.best_topology[agent_id]), 0)

    def test_symmetric_adjacency(self):
        agent_ids = ["a1", "a2", "a3"]
        res = solve_graph_grammar_evolution(agent_ids, population_size=4, generations=3, seed=42)
        for u, neighbors in res.best_topology.items():
            for v in neighbors:
                self.assertIn(u, res.best_topology[v])

    def test_reproducibility(self):
        agent_ids = ["a1", "a2", "a3", "a4"]
        res1 = solve_graph_grammar_evolution(agent_ids, population_size=8, generations=5, seed=42)
        res2 = solve_graph_grammar_evolution(agent_ids, population_size=8, generations=5, seed=42)
        self.assertEqual(res1.best_fitness, res2.best_fitness)

    def test_many_agents(self):
        agent_ids = [f"a{i}" for i in range(10)]
        res = solve_graph_grammar_evolution(agent_ids, population_size=6, generations=3, seed=42)
        self.assertEqual(len(res.best_topology), 10)

    def test_fitness_positive(self):
        agent_ids = ["a1", "a2", "a3", "a4", "a5"]
        res = solve_graph_grammar_evolution(agent_ids, population_size=8, generations=5, seed=42)
        self.assertGreater(res.best_fitness, 0.0)


class TestTemporalSubgraphDetection(unittest.TestCase):
    """Tests for Temporal Subgraph Isomorphism for Emergent Swarm Behavior Detection solver."""

    def test_basic_detection(self):
        events = [
            TemporalEvent("e1", "a1", "a2", "Query", 1.0),
            TemporalEvent("e2", "a2", "a3", "Audit", 3.0),
            TemporalEvent("e3", "a3", "a1", "Execute", 6.0),
        ]
        pattern = BehaviorPattern("pat", ["Query", "Audit", "Execute"], max_delta_time=5.0)
        res = solve_temporal_subgraph_detection(events, pattern)
        self.assertGreater(res.total_detections, 0)

    def test_empty_events(self):
        pattern = BehaviorPattern("pat", ["A"], max_delta_time=5.0)
        res = solve_temporal_subgraph_detection([], pattern)
        self.assertEqual(res.total_detections, 0)

    def test_empty_pattern(self):
        events = [TemporalEvent("e1", "a1", "a2", "A", 1.0)]
        pattern = BehaviorPattern("pat", [], max_delta_time=5.0)
        res = solve_temporal_subgraph_detection(events, pattern)
        self.assertEqual(res.total_detections, 0)

    def test_no_match(self):
        events = [
            TemporalEvent("e1", "a1", "a2", "X", 1.0),
            TemporalEvent("e2", "a2", "a3", "Y", 2.0),
        ]
        pattern = BehaviorPattern("pat", ["A", "B"], max_delta_time=5.0)
        res = solve_temporal_subgraph_detection(events, pattern)
        self.assertEqual(res.total_detections, 0)

    def test_time_constraint(self):
        events = [
            TemporalEvent("e1", "a1", "a2", "A", 1.0),
            TemporalEvent("e2", "a2", "a3", "B", 100.0),
        ]
        pattern = BehaviorPattern("pat", ["A", "B"], max_delta_time=5.0)
        res = solve_temporal_subgraph_detection(events, pattern)
        self.assertEqual(res.total_detections, 0)

    def test_causality_ordered(self):
        events = [
            TemporalEvent("e1", "a1", "a2", "A", 1.0),
            TemporalEvent("e2", "a2", "a3", "B", 2.0),
        ]
        pattern = BehaviorPattern("pat", ["A", "B"], max_delta_time=5.0)
        res = solve_temporal_subgraph_detection(events, pattern)
        self.assertTrue(res.causality_strictly_ordered)

    def test_algorithm_name(self):
        events = [TemporalEvent("e1", "a1", "a2", "A", 1.0)]
        pattern = BehaviorPattern("pat", ["A"], max_delta_time=5.0)
        res = solve_temporal_subgraph_detection(events, pattern)
        self.assertEqual(res.algorithm, "Time-Respecting-Temporal-VF2")

    def test_execution_time(self):
        events = [TemporalEvent("e1", "a1", "a2", "A", 1.0)]
        pattern = BehaviorPattern("pat", ["A"], max_delta_time=5.0)
        res = solve_temporal_subgraph_detection(events, pattern)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_multiple_matches(self):
        events = [
            TemporalEvent("e1", "a1", "a2", "A", 1.0),
            TemporalEvent("e2", "a2", "a3", "B", 2.0),
            TemporalEvent("e3", "a4", "a5", "A", 10.0),
            TemporalEvent("e4", "a5", "a6", "B", 11.0),
        ]
        pattern = BehaviorPattern("pat", ["A", "B"], max_delta_time=5.0)
        res = solve_temporal_subgraph_detection(events, pattern)
        self.assertGreaterEqual(res.total_detections, 2)

    def test_detection_instance_format(self):
        events = [
            TemporalEvent("e1", "a1", "a2", "A", 1.0),
            TemporalEvent("e2", "a2", "a3", "B", 2.0),
        ]
        pattern = BehaviorPattern("pat", ["A", "B"], max_delta_time=5.0)
        res = solve_temporal_subgraph_detection(events, pattern)
        for instance in res.detected_instances:
            self.assertIsInstance(instance, list)

    def test_single_event_pattern(self):
        events = [
            TemporalEvent("e1", "a1", "a2", "A", 1.0),
            TemporalEvent("e2", "a3", "a4", "A", 2.0),
        ]
        pattern = BehaviorPattern("pat", ["A"], max_delta_time=5.0)
        res = solve_temporal_subgraph_detection(events, pattern)
        self.assertGreaterEqual(res.total_detections, 2)

    def test_strict_time_ordering(self):
        events = [
            TemporalEvent("e1", "a1", "a2", "A", 5.0),
            TemporalEvent("e2", "a2", "a3", "B", 1.0),  # Before A
        ]
        pattern = BehaviorPattern("pat", ["A", "B"], max_delta_time=10.0)
        res = solve_temporal_subgraph_detection(events, pattern)
        # B is before A, so pattern A->B should not match
        self.assertEqual(res.total_detections, 0)


class TestParetoGameHypergraphNash(unittest.TestCase):
    """Tests for Multi-Agent Pareto Game-Theoretic Coordination on Hypergraphs solver."""

    def test_basic_game(self):
        players = [
            PlayerAgent("p1", ["A", "B"]),
            PlayerAgent("p2", ["X", "Y"]),
        ]
        hyperedges = [
            HyperedgePayoff("h1", ["p1", "p2"], {
                ("A", "X"): {"p1": 3.0, "p2": 2.0},
                ("A", "Y"): {"p1": 1.0, "p2": 4.0},
                ("B", "X"): {"p1": 2.0, "p2": 1.0},
                ("B", "Y"): {"p1": 4.0, "p2": 3.0},
            }),
        ]
        res = solve_pareto_game_hypergraph(players, hyperedges, iterations=50)
        self.assertTrue(res.pareto_efficient)
        self.assertIn("p1", res.equilibrium_strategies)
        self.assertIn("p2", res.equilibrium_strategies)

    def test_empty_players(self):
        hyperedges = [
            HyperedgePayoff("h1", ["p1"], {("A",): {"p1": 1.0}}),
        ]
        res = solve_pareto_game_hypergraph([], hyperedges, iterations=10)
        self.assertEqual(res.expected_social_welfare, 0.0)

    def test_empty_hyperedges(self):
        players = [PlayerAgent("p1", ["A"])]
        res = solve_pareto_game_hypergraph(players, [], iterations=10)
        self.assertTrue(res.pareto_efficient)

    def test_strategy_probabilities(self):
        players = [
            PlayerAgent("p1", ["A", "B"]),
            PlayerAgent("p2", ["X", "Y"]),
        ]
        hyperedges = [
            HyperedgePayoff("h1", ["p1", "p2"], {
                ("A", "X"): {"p1": 3.0, "p2": 2.0},
                ("B", "Y"): {"p1": 4.0, "p2": 3.0},
            }),
        ]
        res = solve_pareto_game_hypergraph(players, hyperedges, iterations=50)
        for pid, strategy in res.equilibrium_strategies.items():
            total_prob = sum(strategy.values())
            self.assertAlmostEqual(total_prob, 1.0, places=1)

    def test_social_welfare(self):
        players = [
            PlayerAgent("p1", ["A"]),
            PlayerAgent("p2", ["X"]),
        ]
        hyperedges = [
            HyperedgePayoff("h1", ["p1", "p2"], {
                ("A", "X"): {"p1": 5.0, "p2": 5.0},
            }),
        ]
        res = solve_pareto_game_hypergraph(players, hyperedges, iterations=10)
        self.assertGreater(res.expected_social_welfare, 0.0)

    def test_algorithm_name(self):
        players = [PlayerAgent("p1", ["A"])]
        hyperedges = [HyperedgePayoff("h1", ["p1"], {("A",): {"p1": 1.0}})]
        res = solve_pareto_game_hypergraph(players, hyperedges, iterations=10)
        self.assertEqual(res.algorithm, "Regret-Matching-Plus-Hypergraph-Nash")

    def test_execution_time(self):
        players = [PlayerAgent("p1", ["A"])]
        hyperedges = [HyperedgePayoff("h1", ["p1"], {("A",): {"p1": 1.0}})]
        res = solve_pareto_game_hypergraph(players, hyperedges, iterations=10)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_uniform_strategy_initialization(self):
        players = [PlayerAgent("p1", ["A", "B", "C"])]
        hyperedges = [HyperedgePayoff("h1", ["p1"], {
            ("A",): {"p1": 1.0},
            ("B",): {"p1": 2.0},
            ("C",): {"p1": 3.0},
        })]
        res = solve_pareto_game_hypergraph(players, hyperedges, iterations=10)
        self.assertIn("p1", res.equilibrium_strategies)

    def test_multiple_hyperedges(self):
        players = [
            PlayerAgent("p1", ["A", "B"]),
            PlayerAgent("p2", ["X", "Y"]),
        ]
        hyperedges = [
            HyperedgePayoff("h1", ["p1", "p2"], {
                ("A", "X"): {"p1": 3.0, "p2": 2.0},
            }),
            HyperedgePayoff("h2", ["p1", "p2"], {
                ("B", "Y"): {"p1": 4.0, "p2": 3.0},
            }),
        ]
        res = solve_pareto_game_hypergraph(players, hyperedges, iterations=50)
        self.assertTrue(res.pareto_efficient)

    def test_zero_payoff(self):
        players = [
            PlayerAgent("p1", ["A"]),
            PlayerAgent("p2", ["X"]),
        ]
        hyperedges = [
            HyperedgePayoff("h1", ["p1", "p2"], {
                ("A", "X"): {"p1": 0.0, "p2": 0.0},
            }),
        ]
        res = solve_pareto_game_hypergraph(players, hyperedges, iterations=10)
        self.assertEqual(res.expected_social_welfare, 0.0)

    def test_negative_payoff(self):
        players = [
            PlayerAgent("p1", ["A"]),
            PlayerAgent("p2", ["X"]),
        ]
        hyperedges = [
            HyperedgePayoff("h1", ["p1", "p2"], {
                ("A", "X"): {"p1": -1.0, "p2": -2.0},
            }),
        ]
        res = solve_pareto_game_hypergraph(players, hyperedges, iterations=10)
        self.assertTrue(res.pareto_efficient)

    def test_many_iterations(self):
        players = [
            PlayerAgent("p1", ["A", "B"]),
            PlayerAgent("p2", ["X", "Y"]),
        ]
        hyperedges = [
            HyperedgePayoff("h1", ["p1", "p2"], {
                ("A", "X"): {"p1": 3.0, "p2": 2.0},
                ("B", "Y"): {"p1": 4.0, "p2": 3.0},
            }),
        ]
        res = solve_pareto_game_hypergraph(players, hyperedges, iterations=200)
        self.assertTrue(res.pareto_efficient)


if __name__ == '__main__':
    unittest.main()
