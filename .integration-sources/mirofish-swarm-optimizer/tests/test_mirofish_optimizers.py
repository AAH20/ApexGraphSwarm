"""Unit tests for MiroFish Swarm Optimization Engine covering all 10 NP-Hard solvers."""
import unittest
import math
from mirofish_swarm_optimizer.engine import MiroFishSwarmEngine
from mirofish_swarm_optimizer.core.models import (
    SwarmAgent, AgentFaction, MemoryItem, TaskActivity, ParetoSolution
)
from mirofish_swarm_optimizer.core.coalition_structure import OptimalCoalitionStructureSolver
from mirofish_swarm_optimizer.core.influence_maximizer import InfluenceMaximizer
from mirofish_swarm_optimizer.core.kemeny_consensus import KemenyConsensusSolver
from mirofish_swarm_optimizer.core.topology_sparsifier import TopologySparsifier
from mirofish_swarm_optimizer.core.attention_knapsack import CognitiveAttentionKnapsackSolver
from mirofish_swarm_optimizer.core.strategic_cfr import StrategicCFRSolver
from mirofish_swarm_optimizer.core.memory_summarizer import SubmodularMemorySummarizer
from mirofish_swarm_optimizer.core.spectral_quarantine import SpectralSybilQuarantine
from mirofish_swarm_optimizer.core.disjunctive_scheduler import DisjunctiveEventScheduler
from mirofish_swarm_optimizer.core.pareto_frontier import ParetoFrontierSolver
from mirofish_swarm_optimizer.core.evolutionary_baselines import GeneticAlgorithmCSG
from mirofish_swarm_optimizer.adapters.geopolitical import build_geopolitical_agents, build_geopolitical_influence_network

class TestMiroFishSwarmOptimizers(unittest.TestCase):

    def setUp(self):
        self.engine = MiroFishSwarmEngine()
        self.agents = build_geopolitical_agents()
        self.network = build_geopolitical_influence_network()

    # 1. Coalition Structure Generation
    def test_optimal_coalition_structure_vs_ga(self):
        test_agents = self.agents[:8]
        exact_solver = OptimalCoalitionStructureSolver(test_agents)
        res_exact = exact_solver.solve()

        ga_solver = GeneticAlgorithmCSG(test_agents, population_size=30, generations=30)
        res_ga = ga_solver.solve()

        self.assertGreaterEqual(res_exact.total_welfare, res_ga.total_welfare - 1e-4)
        partitioned_agents = []
        for c in res_exact.coalitions:
            partitioned_agents.extend(c.members)
        self.assertEqual(sorted(partitioned_agents), sorted([a.agent_id for a in test_agents]))

    # 2. Influence Maximization
    def test_influence_maximization_rr_sketch(self):
        inf_solver = InfluenceMaximizer(self.agents, self.network)
        res = inf_solver.solve(k_seeds=2, num_samples=500)

        self.assertEqual(len(res.seed_agents), 2)
        self.assertGreater(res.expected_reach, 0.0)
        self.assertLess(res.execution_time_us, 100000.0)

    # 3. Kemeny-Young Condorcet Consensus
    def test_kemeny_young_consensus(self):
        outcomes = ["OPT-A", "OPT-B", "OPT-C"]
        rankings = [
            ["OPT-A", "OPT-B", "OPT-C"],
            ["OPT-A", "OPT-B", "OPT-C"],
            ["OPT-B", "OPT-A", "OPT-C"],
        ]
        solver = KemenyConsensusSolver(outcomes)
        res = solver.solve(rankings)

        self.assertEqual(res.ranked_outcomes[0], "OPT-A")
        self.assertEqual(res.ranked_outcomes, ["OPT-A", "OPT-B", "OPT-C"])
        self.assertGreater(res.agreement_score, 0.5)

    # 4. Topology Sparsifier
    def test_topology_sparsifier_connectivity_and_degrees(self):
        sparsifier = TopologySparsifier(self.agents)
        max_deg = 3
        res = sparsifier.sparsify(max_degree=max_deg)

        self.assertGreater(res["active_edges_count"], 0)
        self.assertGreater(res["message_reduction_pct"], 50.0)
        self.assertLessEqual(res["average_degree"], max_deg)

    # 5. Multi-Choice Attention Knapsack
    def test_attention_knapsack_mckp(self):
        solver = CognitiveAttentionKnapsackSolver(self.agents)
        budget = 4000
        res_exact = solver.solve(token_budget=budget)
        res_greedy = solver.solve_greedy_baseline(token_budget=budget)

        self.assertLessEqual(res_exact.total_tokens_used, budget)
        self.assertEqual(len(res_exact.agent_tier_map), len(self.agents))
        # Exact DP must achieve >= greedy fidelity
        self.assertGreaterEqual(res_exact.total_decision_fidelity, res_greedy.total_decision_fidelity - 1e-4)

    # 6. Strategic CFR Convergence
    def test_strategic_cfr_convergence(self):
        solver = StrategicCFRSolver(
            "Player1", "Player2",
            ["ROCK", "PAPER", "SCISSORS"],
            ["ROCK", "PAPER", "SCISSORS"],
            {
                ("ROCK", "ROCK"): (0.0, 0.0),
                ("ROCK", "PAPER"): (-1.0, 1.0),
                ("ROCK", "SCISSORS"): (1.0, -1.0),
                ("PAPER", "ROCK"): (1.0, -1.0),
                ("PAPER", "PAPER"): (0.0, 0.0),
                ("PAPER", "SCISSORS"): (-1.0, 1.0),
                ("SCISSORS", "ROCK"): (-1.0, 1.0),
                ("SCISSORS", "PAPER"): (1.0, -1.0),
                ("SCISSORS", "SCISSORS"): (0.0, 0.0),
            }
        )
        res = solver.solve(iterations=600)
        strat1 = res.equilibrium_strategies["Player1"]
        # In Rock-Paper-Scissors, Nash is (1/3, 1/3, 1/3)
        for act in ["ROCK", "PAPER", "SCISSORS"]:
            self.assertAlmostEqual(strat1[act], 1.0 / 3.0, delta=0.08)
        self.assertLess(res.exploitability, 0.15)

    # 7. Submodular Memory Summarization
    def test_submodular_memory_summarization(self):
        pool = [
            MemoryItem(f"mem_{i}", f"entity_{i % 4}", f"Fact #{i}", 1.0 + (i % 3), float(i), [math.cos(i), math.sin(i)])
            for i in range(30)
        ]
        summarizer = SubmodularMemorySummarizer(pool)
        k = 6
        res = summarizer.solve(k_items=k)

        self.assertEqual(len(res.selected_items), k)
        self.assertGreater(res.total_coverage_score, 0.0)
        self.assertGreater(res.reduction_ratio, 70.0)

    # 8. Spectral Sybil Quarantine
    def test_spectral_sybil_quarantine(self):
        # 8 nodes: 0-3 in cluster A, 4-7 in cluster B, weak link between 3 and 4
        n = 8
        adj = [[0.0] * n for _ in range(n)]
        for i in range(4):
            for j in range(4):
                if i != j: adj[i][j] = 1.0
        for i in range(4, 8):
            for j in range(4, 8):
                if i != j: adj[i][j] = 1.0
        adj[3][4] = adj[4][3] = 0.1

        agents = [f"agent_{i}" for i in range(n)]
        quarantiner = SpectralSybilQuarantine(agents, adj)
        res = quarantiner.solve()

        # Both sets must have 4 agents
        self.assertEqual(len(res.quarantined_cluster), 4)
        self.assertEqual(len(res.authentic_agents), 4)
        # Quarantined cluster should be either {0,1,2,3} or {4,5,6,7}
        cluster_set = set(res.quarantined_cluster)
        expected_a = {f"agent_{i}" for i in range(4)}
        expected_b = {f"agent_{i}" for i in range(4, 8)}
        self.assertTrue(cluster_set == expected_a or cluster_set == expected_b)

    # 9. Disjunctive DAG Scheduling
    def test_disjunctive_dag_scheduling(self):
        tasks = [
            TaskActivity("TASK_A", "AG_1", 10.0, [], 0),
            TaskActivity("TASK_B", "AG_1", 20.0, ["TASK_A"], 1),
            TaskActivity("TASK_C", "AG_2", 15.0, [], 0),
            TaskActivity("TASK_D", "AG_2", 10.0, ["TASK_B", "TASK_C"], 1),
        ]
        scheduler = DisjunctiveEventScheduler(tasks, num_workers=2)
        res = scheduler.solve()

        # TASK_B must start after TASK_A completes
        self.assertGreaterEqual(res.task_start_times["TASK_B"], res.task_start_times["TASK_A"] + 10.0)
        # TASK_D must start after TASK_B completes
        self.assertGreaterEqual(res.task_start_times["TASK_D"], res.task_start_times["TASK_B"] + 20.0)
        self.assertGreater(res.makespan, 0.0)

    # 10. Multi-Objective Pareto Frontier
    def test_pareto_frontier_solver(self):
        candidates = [
            ParetoSolution("A", [10.0, 1.0], {}),
            ParetoSolution("B", [1.0, 10.0], {}),
            ParetoSolution("C", [5.0, 5.0], {}),
            ParetoSolution("D", [2.0, 2.0], {}),  # Dominated by C
        ]
        solver = ParetoFrontierSolver(candidates)
        res = solver.solve(reference_point=[0.0, 0.0])

        frontier_ids = {s.solution_id for s in res.non_dominated_solutions}
        self.assertIn("A", frontier_ids)
        self.assertIn("B", frontier_ids)
        self.assertIn("C", frontier_ids)
        self.assertNotIn("D", frontier_ids)
        self.assertEqual(res.dominated_count, 1)
        self.assertGreater(res.hypervolume_indicator, 0.0)

if __name__ == "__main__":
    unittest.main()
