"""Comprehensive Test Suite for all 10 Apex Agentic Graph Swarm Solvers."""
import unittest
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
from agentic_graph_swarm_kernel.engine import AgenticGraphSwarmEngine


class TestAgenticGraphSwarmKernel(unittest.TestCase):

    def test_p1_hypergraph_csg(self):
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

    def test_p2_causal_dag(self):
        vars_obs = [
            VariableObservation("v1", "Var1", [float(i) for i in range(20)]),
            VariableObservation("v2", "Var2", [float(i * 2) for i in range(20)]),
            VariableObservation("v3", "Var3", [float(i % 3) for i in range(20)]),
        ]
        res = solve_causal_dag_synthesis(vars_obs, max_in_degree=2)
        self.assertTrue(res.is_acyclic)
        self.assertIsInstance(res.bic_score, float)

    def test_p3_epistemic_consensus(self):
        graphs = [
            AgentBeliefGraph("ag1", 0.9, [FactStatement("Sun", "is", "Star", 0.95)]),
            AgentBeliefGraph("ag2", 0.8, [FactStatement("Sun", "is", "Star", 0.90)]),
        ]
        res = solve_epistemic_consensus(graphs)
        self.assertEqual(len(res.consensus_graph), 1)
        self.assertTrue(res.cycle_free_certified)

    def test_p4_attention_routing(self):
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

    def test_p5_spectral_memory_decay(self):
        nodes = [MemoryNode("m1", 1000.0, 5), MemoryNode("m2", 900.0, 3)]
        edges = [MemoryEdge("m1", "m2", 0.8, 1.0)]
        res = solve_spectral_memory_decay(nodes, edges, target_retention_ratio=1.0)
        self.assertEqual(len(res.retained_nodes), 2)
        self.assertTrue(res.causal_connectivity_preserved)

    def test_p6_tool_scheduling(self):
        tasks = [
            AgentToolTask("t1", "a1", "res1", 20),
            AgentToolTask("t2", "a2", "res1", 30, precedence_prereqs=["t1"]),
        ]
        resources = [ToolResource("res1", 1)]
        res = solve_disjunctive_tool_scheduling(tasks, resources)
        self.assertTrue(res.deadlock_free_certified)
        self.assertGreaterEqual(res.makespan_ms, 50)

    def test_p7_byzantine_truth(self):
        claims = [
            AgentClaim("c1", "honest_1", "Entity", "attr", "TrueVal", 1.0),
            AgentClaim("c2", "honest_2", "Entity", "attr", "TrueVal", 2.0),
            AgentClaim("c3", "byzantine", "Entity", "attr", "FalseVal", 3.0),
        ]
        res = solve_byzantine_truth_discovery(claims)
        self.assertEqual(res.resolved_attributes["Entity.attr"], "TrueVal")
        self.assertIn("byzantine", res.quarantined_byzantine_agents)

    def test_p8_graph_grammar_evolution(self):
        agents = ["w1", "w2", "w3", "w4"]
        res = solve_graph_grammar_evolution(agents, population_size=6, generations=5)
        self.assertIn("w1", res.best_topology)
        self.assertGreater(res.best_fitness, -1000.0)

    def test_p9_temporal_subgraph(self):
        events = [
            TemporalEvent("e1", "a", "b", "Msg", 1.0),
            TemporalEvent("e2", "b", "c", "Ack", 2.0),
        ]
        pattern = BehaviorPattern("p1", ["Msg", "Ack"], max_delta_time=3.0)
        res = solve_temporal_subgraph_detection(events, pattern)
        self.assertEqual(res.total_detections, 1)
        self.assertTrue(res.causality_strictly_ordered)

    def test_p10_pareto_game(self):
        players = [PlayerAgent("p1", ["A", "B"]), PlayerAgent("p2", ["A", "B"])]
        payoffs = [HyperedgePayoff("he1", ["p1", "p2"], {
            ("A", "A"): {"p1": 5.0, "p2": 5.0},
            ("B", "B"): {"p1": 2.0, "p2": 2.0},
        })]
        res = solve_pareto_game_hypergraph(players, payoffs, iterations=10)
        self.assertTrue(res.pareto_efficient)
        self.assertGreater(res.expected_social_welfare, 0.0)

    def test_engine_full_benchmark(self):
        engine = AgenticGraphSwarmEngine()
        bench = engine.benchmark_all_10()
        self.assertEqual(len(bench["solvers"]), 10)
        self.assertGreater(bench["total_benchmark_time_us"], 0.0)

    def test_adapters(self):
        engine = AgenticGraphSwarmEngine()
        suite = engine.generate_synthetic_benchmark_suite()
        # Test digital world simulator adapter
        sim_res = engine.world_simulator.synthesize_macro_causality(*suite["p2_causal"])
        self.assertTrue(sim_res.is_acyclic)
        # Test enterprise mesh adapter
        mesh_res = engine.enterprise_mesh.schedule_tool_sandboxes(*suite["p6_tool"])
        self.assertTrue(mesh_res.deadlock_free_certified)


if __name__ == "__main__":
    unittest.main()
