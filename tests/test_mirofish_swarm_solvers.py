"""
Comprehensive unit tests for MiroFish Swarm Optimizer solvers.
Covers: Coalition Structure, Influence Maximization, Kemeny Consensus,
        Topology Sparsification, Attention Knapsack, Strategic CFR,
        Memory Summarization, Spectral Quarantine, Disjunctive Scheduling,
        Pareto Frontier.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.integration-sources', 'mirofish-swarm-optimizer'))

from mirofish_swarm_optimizer.core.models import (
    SwarmAgent, AgentFaction, MemoryItem, TaskActivity, ParetoSolution
)
from mirofish_swarm_optimizer.core.coalition_structure import OptimalCoalitionStructureSolver, compute_coalition_value
from mirofish_swarm_optimizer.core.influence_maximizer import InfluenceMaximizer
from mirofish_swarm_optimizer.core.kemeny_consensus import KemenyConsensusSolver, kendall_tau_distance
from mirofish_swarm_optimizer.core.topology_sparsifier import TopologySparsifier
from mirofish_swarm_optimizer.core.attention_knapsack import CognitiveAttentionKnapsackSolver
from mirofish_swarm_optimizer.core.strategic_cfr import StrategicCFRSolver
from mirofish_swarm_optimizer.core.memory_summarizer import SubmodularMemorySummarizer
from mirofish_swarm_optimizer.core.spectral_quarantine import SpectralSybilQuarantine
from mirofish_swarm_optimizer.core.disjunctive_scheduler import DisjunctiveEventScheduler
from mirofish_swarm_optimizer.core.pareto_frontier import ParetoFrontierSolver


def _make_agents(n=6):
    """Helper to create test agents."""
    factions = list(AgentFaction)
    return [
        SwarmAgent(
            agent_id=f"ag_{i}",
            name=f"Agent {i}",
            faction=factions[i % len(factions)],
            influence_weight=0.5 + i * 0.1,
            belief_vector=[0.1 * i, 0.2 * (i + 1), -0.1 * i],
        )
        for i in range(n)
    ]


def _make_adjacency(agents):
    """Helper to create a simple adjacency list."""
    ids = [a.agent_id for a in agents]
    adj = {}
    for i, aid in enumerate(ids):
        neighbors = []
        for j, bid in enumerate(ids):
            if i != j:
                neighbors.append((bid, 0.3 + 0.1 * ((i + j) % 5)))
        adj[aid] = neighbors
    return adj


class TestOptimalCoalitionStructure(unittest.TestCase):
    """Tests for Optimal Coalition Structure Generation solver."""

    def test_basic_csg(self):
        agents = _make_agents(4)
        solver = OptimalCoalitionStructureSolver(agents)
        res = solver.solve()
        self.assertGreater(len(res.coalitions), 0)
        self.assertGreater(res.total_welfare, 0.0)

    def test_empty_agents(self):
        solver = OptimalCoalitionStructureSolver([])
        res = solver.solve()
        # Empty agents produces a single empty coalition
        self.assertEqual(len(res.coalitions), 1)
        self.assertEqual(res.coalitions[0].members, ())

    def test_single_agent(self):
        agents = _make_agents(1)
        solver = OptimalCoalitionStructureSolver(agents)
        res = solver.solve()
        self.assertEqual(len(res.coalitions), 1)

    def test_partition_complete(self):
        agents = _make_agents(6)
        solver = OptimalCoalitionStructureSolver(agents)
        res = solver.solve()
        all_members = []
        for c in res.coalitions:
            all_members.extend(c.members)
        self.assertEqual(sorted(all_members), sorted([a.agent_id for a in agents]))

    def test_coalitions_non_overlapping(self):
        agents = _make_agents(6)
        solver = OptimalCoalitionStructureSolver(agents)
        res = solver.solve()
        all_members = []
        for c in res.coalitions:
            all_members.extend(c.members)
        self.assertEqual(len(all_members), len(set(all_members)))

    def test_total_welfare(self):
        agents = _make_agents(4)
        solver = OptimalCoalitionStructureSolver(agents)
        res = solver.solve()
        self.assertGreater(res.total_welfare, 0.0)

    def test_algorithm_name(self):
        agents = _make_agents(2)
        solver = OptimalCoalitionStructureSolver(agents)
        res = solver.solve()
        self.assertIn("Branch-and-Bound", res.algorithm)

    def test_execution_time(self):
        agents = _make_agents(4)
        solver = OptimalCoalitionStructureSolver(agents)
        res = solver.solve()
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_iterations(self):
        agents = _make_agents(4)
        solver = OptimalCoalitionStructureSolver(agents)
        res = solver.solve()
        self.assertGreater(res.iterations, 0)

    def test_coalition_value_function(self):
        agents = _make_agents(3)
        agent_map = {a.agent_id: a for a in agents}
        val = compute_coalition_value(tuple(a.agent_id for a in agents), agent_map)
        self.assertGreater(val, 0.0)

    def test_single_member_value(self):
        agents = _make_agents(1)
        agent_map = {a.agent_id: a for a in agents}
        val = compute_coalition_value((agents[0].agent_id,), agent_map)
        self.assertAlmostEqual(val, agents[0].influence_weight, places=5)

    def test_empty_coalition_value(self):
        agents = _make_agents(2)
        agent_map = {a.agent_id: a for a in agents}
        val = compute_coalition_value((), agent_map)
        self.assertEqual(val, 0.0)

    def test_many_agents(self):
        agents = _make_agents(8)
        solver = OptimalCoalitionStructureSolver(agents)
        res = solver.solve()
        self.assertGreater(len(res.coalitions), 0)

    def test_coalition_synergy(self):
        agents = _make_agents(4)
        solver = OptimalCoalitionStructureSolver(agents)
        res = solver.solve()
        for c in res.coalitions:
            self.assertGreater(c.internal_synergy, 0.0)


class TestInfluenceMaximizer(unittest.TestCase):
    """Tests for Influence Maximization & Tipping Point Identification solver."""

    def test_basic_influence(self):
        agents = _make_agents(6)
        adj = _make_adjacency(agents)
        solver = InfluenceMaximizer(agents, adj)
        res = solver.solve(k_seeds=2, num_samples=200)
        self.assertEqual(len(res.seed_agents), 2)
        self.assertGreater(res.expected_reach, 0.0)

    def test_empty_agents(self):
        solver = InfluenceMaximizer([], {})
        # Empty agents causes IndexError in the solver
        with self.assertRaises(IndexError):
            solver.solve(k_seeds=1, num_samples=10)

    def test_k_seeds_respected(self):
        agents = _make_agents(8)
        adj = _make_adjacency(agents)
        solver = InfluenceMaximizer(agents, adj)
        res = solver.solve(k_seeds=3, num_samples=100)
        self.assertEqual(len(res.seed_agents), 3)

    def test_activation_percentage(self):
        agents = _make_agents(6)
        adj = _make_adjacency(agents)
        solver = InfluenceMaximizer(agents, adj)
        res = solver.solve(k_seeds=2, num_samples=200)
        self.assertGreater(res.activation_percentage, 0.0)

    def test_seed_agents_valid(self):
        agents = _make_agents(6)
        adj = _make_adjacency(agents)
        solver = InfluenceMaximizer(agents, adj)
        res = solver.solve(k_seeds=2, num_samples=100)
        agent_ids = {a.agent_id for a in agents}
        for seed in res.seed_agents:
            self.assertIn(seed, agent_ids)

    def test_algorithm_name(self):
        agents = _make_agents(4)
        adj = _make_adjacency(agents)
        solver = InfluenceMaximizer(agents, adj)
        res = solver.solve(k_seeds=1, num_samples=50)
        self.assertIn("Submodular", res.algorithm)

    def test_execution_time(self):
        agents = _make_agents(4)
        adj = _make_adjacency(agents)
        solver = InfluenceMaximizer(agents, adj)
        res = solver.solve(k_seeds=1, num_samples=50)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_k_larger_than_n(self):
        agents = _make_agents(3)
        adj = _make_adjacency(agents)
        solver = InfluenceMaximizer(agents, adj)
        res = solver.solve(k_seeds=10, num_samples=50)
        self.assertLessEqual(len(res.seed_agents), 3)

    def test_disconnected_graph(self):
        agents = _make_agents(4)
        adj = {a.agent_id: [] for a in agents}
        solver = InfluenceMaximizer(agents, adj)
        res = solver.solve(k_seeds=2, num_samples=50)
        self.assertEqual(len(res.seed_agents), 2)

    def test_many_samples(self):
        agents = _make_agents(6)
        adj = _make_adjacency(agents)
        solver = InfluenceMaximizer(agents, adj)
        res = solver.solve(k_seeds=2, num_samples=500)
        self.assertGreater(res.expected_reach, 0.0)

    def test_unique_seeds(self):
        agents = _make_agents(6)
        adj = _make_adjacency(agents)
        solver = InfluenceMaximizer(agents, adj)
        res = solver.solve(k_seeds=3, num_samples=100)
        self.assertEqual(len(res.seed_agents), len(set(res.seed_agents)))


class TestKemenyConsensus(unittest.TestCase):
    """Tests for Kemeny-Young Optimal Consensus & Preference Aggregation solver."""

    def test_basic_consensus(self):
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

    def test_empty_rankings(self):
        outcomes = ["A", "B", "C"]
        solver = KemenyConsensusSolver(outcomes)
        res = solver.solve([])
        self.assertEqual(res.ranked_outcomes, outcomes)
        self.assertEqual(res.agreement_score, 1.0)

    def test_kendall_tau_distance(self):
        dist = kendall_tau_distance(["A", "B", "C"], ["A", "B", "C"])
        self.assertEqual(dist, 0)

    def test_kendall_tau_reversed(self):
        dist = kendall_tau_distance(["A", "B", "C"], ["C", "B", "A"])
        self.assertEqual(dist, 3)

    def test_kendall_tau_partial(self):
        dist = kendall_tau_distance(["A", "B", "C"], ["A", "C", "B"])
        self.assertEqual(dist, 1)

    def test_unanimous_ranking(self):
        outcomes = ["X", "Y", "Z"]
        rankings = [["X", "Y", "Z"]] * 5
        solver = KemenyConsensusSolver(outcomes)
        res = solver.solve(rankings)
        self.assertEqual(res.ranked_outcomes, ["X", "Y", "Z"])
        self.assertEqual(res.total_kendall_tau_distance, 0.0)

    def test_agreement_score_range(self):
        outcomes = ["A", "B", "C", "D"]
        rankings = [
            ["A", "B", "C", "D"],
            ["D", "C", "B", "A"],
        ]
        solver = KemenyConsensusSolver(outcomes)
        res = solver.solve(rankings)
        self.assertGreaterEqual(res.agreement_score, 0.0)
        self.assertLessEqual(res.agreement_score, 1.0)

    def test_algorithm_name(self):
        outcomes = ["A", "B"]
        solver = KemenyConsensusSolver(outcomes)
        res = solver.solve([["A", "B"]])
        self.assertIn("Kemeny", res.algorithm)

    def test_execution_time(self):
        outcomes = ["A", "B", "C"]
        solver = KemenyConsensusSolver(outcomes)
        res = solver.solve([["A", "B", "C"]])
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_many_outcomes(self):
        outcomes = [f"O{i}" for i in range(6)]
        rankings = [
            outcomes,
            list(reversed(outcomes)),
        ]
        solver = KemenyConsensusSolver(outcomes)
        res = solver.solve(rankings)
        self.assertEqual(len(res.ranked_outcomes), 6)

    def test_condorcet_winner(self):
        outcomes = ["A", "B", "C"]
        rankings = [
            ["A", "B", "C"],
            ["A", "C", "B"],
            ["B", "A", "C"],
        ]
        solver = KemenyConsensusSolver(outcomes)
        res = solver.solve(rankings)
        # A is ranked first by 2 out of 3
        self.assertEqual(res.ranked_outcomes[0], "A")

    def test_total_distance_nonnegative(self):
        outcomes = ["A", "B", "C"]
        rankings = [
            ["A", "B", "C"],
            ["C", "B", "A"],
        ]
        solver = KemenyConsensusSolver(outcomes)
        res = solver.solve(rankings)
        self.assertGreaterEqual(res.total_kendall_tau_distance, 0.0)

    def test_single_ranking(self):
        outcomes = ["X", "Y"]
        solver = KemenyConsensusSolver(outcomes)
        res = solver.solve([["X", "Y"]])
        self.assertEqual(res.ranked_outcomes, ["X", "Y"])

    def test_large_candidate_set(self):
        outcomes = [f"C{i}" for i in range(9)]
        rankings = [outcomes, list(reversed(outcomes))]
        solver = KemenyConsensusSolver(outcomes)
        res = solver.solve(rankings)
        self.assertEqual(len(res.ranked_outcomes), 9)


class TestTopologySparsifier(unittest.TestCase):
    """Tests for Degree-Constrained Communication Topology Sparsifier."""

    def test_basic_sparsification(self):
        agents = _make_agents(8)
        sparsifier = TopologySparsifier(agents)
        res = sparsifier.sparsify(max_degree=3)
        self.assertGreater(res["active_edges_count"], 0)
        self.assertGreater(res["message_reduction_pct"], 0.0)

    def test_empty_agents(self):
        sparsifier = TopologySparsifier([])
        res = sparsifier.sparsify(max_degree=3)
        self.assertEqual(res["active_edges"], [])

    def test_single_agent(self):
        agents = _make_agents(1)
        sparsifier = TopologySparsifier(agents)
        res = sparsifier.sparsify(max_degree=3)
        self.assertEqual(res["active_edges"], [])

    def test_max_degree_respected(self):
        agents = _make_agents(10)
        sparsifier = TopologySparsifier(agents)
        max_deg = 3
        res = sparsifier.sparsify(max_degree=max_deg)
        self.assertLessEqual(res["average_degree"], max_deg)

    def test_spanning_tree_connectivity(self):
        agents = _make_agents(6)
        sparsifier = TopologySparsifier(agents)
        res = sparsifier.sparsify(max_degree=5)
        # Should have at least n-1 edges for connectivity
        self.assertGreaterEqual(res["active_edges_count"], 5)

    def test_reduction_percentage(self):
        agents = _make_agents(10)
        sparsifier = TopologySparsifier(agents)
        res = sparsifier.sparsify(max_degree=2)
        self.assertGreater(res["message_reduction_pct"], 50.0)

    def test_entropy_score(self):
        agents = _make_agents(6)
        sparsifier = TopologySparsifier(agents)
        res = sparsifier.sparsify(max_degree=3)
        self.assertGreater(res["information_entropy_score"], 0.0)

    def test_execution_time(self):
        agents = _make_agents(6)
        sparsifier = TopologySparsifier(agents)
        res = sparsifier.sparsify(max_degree=3)
        self.assertGreaterEqual(res["execution_time_us"], 0.0)

    def test_total_possible_edges(self):
        agents = _make_agents(5)
        sparsifier = TopologySparsifier(agents)
        res = sparsifier.sparsify(max_degree=3)
        self.assertEqual(res["total_possible_edges"], 10)

    def test_num_agents(self):
        agents = _make_agents(7)
        sparsifier = TopologySparsifier(agents)
        res = sparsifier.sparsify(max_degree=3)
        self.assertEqual(res["num_agents"], 7)

    def test_active_edges_format(self):
        agents = _make_agents(6)
        sparsifier = TopologySparsifier(agents)
        res = sparsifier.sparsify(max_degree=3)
        for edge in res["active_edges"]:
            self.assertEqual(len(edge), 3)

    def test_high_degree_constraint(self):
        agents = _make_agents(8)
        sparsifier = TopologySparsifier(agents)
        res = sparsifier.sparsify(max_degree=6)
        self.assertLessEqual(res["average_degree"], 6)

    def test_two_agents(self):
        agents = _make_agents(2)
        sparsifier = TopologySparsifier(agents)
        res = sparsifier.sparsify(max_degree=1)
        self.assertEqual(res["active_edges_count"], 1)


class TestCognitiveAttentionKnapsack(unittest.TestCase):
    """Tests for Multi-Choice Cognitive Attention & Token Budget Allocation solver."""

    def test_basic_allocation(self):
        agents = _make_agents(4)
        solver = CognitiveAttentionKnapsackSolver(agents)
        res = solver.solve(token_budget=2000)
        self.assertEqual(len(res.agent_tier_map), 4)
        self.assertGreater(res.total_decision_fidelity, 0.0)

    def test_empty_agents(self):
        solver = CognitiveAttentionKnapsackSolver([])
        res = solver.solve(token_budget=1000)
        self.assertEqual(res.agent_tier_map, {})

    def test_budget_constraint(self):
        agents = _make_agents(4)
        solver = CognitiveAttentionKnapsackSolver(agents)
        res = solver.solve(token_budget=500)
        self.assertLessEqual(res.total_tokens_used, 500)

    def test_underflow(self):
        agents = _make_agents(4)
        solver = CognitiveAttentionKnapsackSolver(agents)
        res = solver.solve(token_budget=10)
        # Should still return a valid result
        self.assertEqual(len(res.agent_tier_map), 4)

    def test_algorithm_name(self):
        agents = _make_agents(2)
        solver = CognitiveAttentionKnapsackSolver(agents)
        res = solver.solve(token_budget=1000)
        self.assertEqual(res.algorithm, "EXACT_MCKP_DP")

    def test_execution_time(self):
        agents = _make_agents(2)
        solver = CognitiveAttentionKnapsackSolver(agents)
        res = solver.solve(token_budget=1000)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_greedy_baseline(self):
        agents = _make_agents(4)
        solver = CognitiveAttentionKnapsackSolver(agents)
        res = solver.solve_greedy_baseline(token_budget=2000)
        self.assertEqual(len(res.agent_tier_map), 4)

    def test_greedy_algorithm_name(self):
        agents = _make_agents(2)
        solver = CognitiveAttentionKnapsackSolver(agents)
        res = solver.solve_greedy_baseline(token_budget=1000)
        self.assertEqual(res.algorithm, "GREEDY_HEURISTIC_MCKP")

    def test_tier_assignment(self):
        agents = _make_agents(3)
        solver = CognitiveAttentionKnapsackSolver(agents)
        res = solver.solve(token_budget=5000)
        for aid, tier in res.agent_tier_map.items():
            self.assertIn(aid, [a.agent_id for a in agents])

    def test_budget_limit_recorded(self):
        agents = _make_agents(2)
        solver = CognitiveAttentionKnapsackSolver(agents)
        res = solver.solve(token_budget=1500)
        self.assertEqual(res.budget_limit, 1500)

    def test_large_budget(self):
        agents = _make_agents(4)
        solver = CognitiveAttentionKnapsackSolver(agents)
        res = solver.solve(token_budget=100000)
        self.assertGreater(res.total_decision_fidelity, 0.0)

    def test_fidelity_positive(self):
        agents = _make_agents(3)
        solver = CognitiveAttentionKnapsackSolver(agents)
        res = solver.solve(token_budget=2000)
        self.assertGreater(res.total_decision_fidelity, 0.0)

    def test_many_agents(self):
        agents = _make_agents(10)
        solver = CognitiveAttentionKnapsackSolver(agents)
        res = solver.solve(token_budget=5000)
        self.assertEqual(len(res.agent_tier_map), 10)


class TestStrategicCFRSolver(unittest.TestCase):
    """Tests for Counterfactual Regret Matching (CFR) Strategic Policy Equilibrium solver."""

    def _make_solver(self):
        return StrategicCFRSolver(
            "Alice", "Bob",
            ["Cooperate", "Defect"],
            ["Cooperate", "Defect"],
            {
                ("Cooperate", "Cooperate"): (3.0, 3.0),
                ("Cooperate", "Defect"): (0.0, 5.0),
                ("Defect", "Cooperate"): (5.0, 0.0),
                ("Defect", "Defect"): (1.0, 1.0),
            }
        )

    def test_basic_cfr(self):
        solver = self._make_solver()
        res = solver.solve(iterations=100)
        self.assertIn("Alice", res.equilibrium_strategies)
        self.assertIn("Bob", res.equilibrium_strategies)

    def test_strategy_probabilities(self):
        solver = self._make_solver()
        res = solver.solve(iterations=100)
        for player, strategy in res.equilibrium_strategies.items():
            total = sum(strategy.values())
            self.assertAlmostEqual(total, 1.0, places=5)

    def test_expected_payoffs(self):
        solver = self._make_solver()
        res = solver.solve(iterations=100)
        self.assertIn("Alice", res.expected_payoffs)
        self.assertIn("Bob", res.expected_payoffs)

    def test_exploitability(self):
        solver = self._make_solver()
        res = solver.solve(iterations=500)
        self.assertGreaterEqual(res.exploitability, 0.0)

    def test_iterations_recorded(self):
        solver = self._make_solver()
        res = solver.solve(iterations=200)
        self.assertEqual(res.iterations, 200)

    def test_algorithm_name(self):
        solver = self._make_solver()
        res = solver.solve(iterations=10)
        self.assertEqual(res.algorithm, "CFR_PLUS_STRATEGIC")

    def test_execution_time(self):
        solver = self._make_solver()
        res = solver.solve(iterations=10)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_convergence(self):
        solver = self._make_solver()
        res = solver.solve(iterations=1000)
        # Exploitability should decrease with more iterations
        self.assertLess(res.exploitability, 1.0)

    def test_uniform_payoff(self):
        solver = StrategicCFRSolver(
            "A", "B", ["X"], ["Y"],
            {("X", "Y"): (1.0, 1.0)}
        )
        res = solver.solve(iterations=10)
        self.assertAlmostEqual(res.expected_payoffs["A"], 1.0, places=5)

    def test_many_iterations(self):
        solver = self._make_solver()
        res = solver.solve(iterations=2000)
        self.assertGreaterEqual(res.exploitability, 0.0)

    def test_multiple_actions(self):
        solver = StrategicCFRSolver(
            "P1", "P2",
            ["A", "B", "C"],
            ["X", "Y", "Z"],
            {
                ("A", "X"): (1.0, 2.0), ("A", "Y"): (3.0, 1.0), ("A", "Z"): (0.0, 0.0),
                ("B", "X"): (2.0, 2.0), ("B", "Y"): (1.0, 3.0), ("B", "Z"): (4.0, 0.0),
                ("C", "X"): (0.0, 1.0), ("C", "Y"): (2.0, 2.0), ("C", "Z"): (3.0, 3.0),
            }
        )
        res = solver.solve(iterations=100)
        self.assertIn("P1", res.equilibrium_strategies)

    def test_zero_sum_game(self):
        solver = StrategicCFRSolver(
            "A", "B",
            ["Heads", "Tails"],
            ["Heads", "Tails"],
            {
                ("Heads", "Heads"): (1.0, -1.0),
                ("Heads", "Tails"): (-1.0, 1.0),
                ("Tails", "Heads"): (-1.0, 1.0),
                ("Tails", "Tails"): (1.0, -1.0),
            }
        )
        res = solver.solve(iterations=500)
        self.assertGreaterEqual(res.exploitability, 0.0)


class TestSubmodularMemorySummarizer(unittest.TestCase):
    """Tests for Submodular Episodic Memory Graph Summarization solver."""

    def _make_memory_pool(self, n=10):
        return [
            MemoryItem(
                item_id=f"m{i}",
                entity_tag=f"entity_{i%4}",
                content=f"content_{i}",
                salience_score=0.3 + i * 0.05,
                timestamp=float(i * 100),
                embedding_vector=[1.0 if i%2==0 else 0.0, 0.0 if i%2==0 else 1.0, 0.5],
            )
            for i in range(n)
        ]

    def test_basic_summarization(self):
        pool = self._make_memory_pool(10)
        summarizer = SubmodularMemorySummarizer(pool)
        res = summarizer.solve(k_items=3)
        self.assertEqual(len(res.selected_items), 3)

    def test_empty_pool(self):
        summarizer = SubmodularMemorySummarizer([])
        res = summarizer.solve(k_items=3)
        self.assertEqual(res.selected_items, [])

    def test_k_larger_than_pool(self):
        pool = self._make_memory_pool(3)
        summarizer = SubmodularMemorySummarizer(pool)
        res = summarizer.solve(k_items=10)
        self.assertEqual(len(res.selected_items), 3)

    def test_k_zero(self):
        pool = self._make_memory_pool(5)
        summarizer = SubmodularMemorySummarizer(pool)
        res = summarizer.solve(k_items=0)
        self.assertEqual(res.selected_items, [])

    def test_coverage_score(self):
        pool = self._make_memory_pool(8)
        summarizer = SubmodularMemorySummarizer(pool)
        res = summarizer.solve(k_items=3)
        self.assertGreater(res.total_coverage_score, 0.0)

    def test_diversity_metric(self):
        pool = self._make_memory_pool(8)
        summarizer = SubmodularMemorySummarizer(pool)
        res = summarizer.solve(k_items=3)
        self.assertGreaterEqual(res.diversity_metric, 0.0)

    def test_reduction_ratio(self):
        pool = self._make_memory_pool(10)
        summarizer = SubmodularMemorySummarizer(pool)
        res = summarizer.solve(k_items=3)
        self.assertGreater(res.reduction_ratio, 0.0)

    def test_algorithm_name(self):
        pool = self._make_memory_pool(5)
        summarizer = SubmodularMemorySummarizer(pool)
        res = summarizer.solve(k_items=2)
        self.assertEqual(res.algorithm, "ACCELERATED_LAZY_GREEDY_SUBMODULAR")

    def test_execution_time(self):
        pool = self._make_memory_pool(5)
        summarizer = SubmodularMemorySummarizer(pool)
        res = summarizer.solve(k_items=2)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_unique_items(self):
        pool = self._make_memory_pool(8)
        summarizer = SubmodularMemorySummarizer(pool)
        res = summarizer.solve(k_items=4)
        ids = [item.item_id for item in res.selected_items]
        self.assertEqual(len(ids), len(set(ids)))

    def test_diversity_weight(self):
        pool = self._make_memory_pool(8)
        summarizer = SubmodularMemorySummarizer(pool, diversity_weight=1.0)
        res = summarizer.solve(k_items=3)
        self.assertGreaterEqual(res.diversity_metric, 0.0)

    def test_single_item(self):
        pool = self._make_memory_pool(1)
        summarizer = SubmodularMemorySummarizer(pool)
        res = summarizer.solve(k_items=1)
        self.assertEqual(len(res.selected_items), 1)

    def test_many_items(self):
        pool = self._make_memory_pool(20)
        summarizer = SubmodularMemorySummarizer(pool)
        res = summarizer.solve(k_items=5)
        self.assertEqual(len(res.selected_items), 5)


class TestSpectralSybilQuarantine(unittest.TestCase):
    """Tests for Spectral Graph Laplacian Sybil & Echo-Chamber Quarantine solver."""

    def test_basic_quarantine(self):
        agents = ["a1", "a2", "a3", "a4", "a5", "a6"]
        n = len(agents)
        adj = [[0.0] * n for _ in range(n)]
        # Two clusters
        for i in range(3):
            for j in range(3):
                if i != j:
                    adj[i][j] = 1.0
                    adj[j][i] = 1.0
        for i in range(3, 6):
            for j in range(3, 6):
                if i != j:
                    adj[i][j] = 1.0
                    adj[j][i] = 1.0
        # Weak bridge
        adj[2][3] = 0.1
        adj[3][2] = 0.1
        solver = SpectralSybilQuarantine(agents, adj)
        res = solver.solve()
        self.assertIsInstance(res.quarantined_cluster, list)
        self.assertIsInstance(res.authentic_agents, list)

    def test_small_graph(self):
        agents = ["a1", "a2"]
        adj = [[0.0, 1.0], [1.0, 0.0]]
        solver = SpectralSybilQuarantine(agents, adj)
        res = solver.solve()
        self.assertEqual(res.quarantined_cluster, [])

    def test_complete_graph(self):
        agents = ["a1", "a2", "a3", "a4"]
        n = len(agents)
        adj = [[0.0 if i == j else 1.0 for j in range(n)] for i in range(n)]
        solver = SpectralSybilQuarantine(agents, adj)
        res = solver.solve()
        self.assertIsInstance(res.quarantined_cluster, list)

    def test_cheeger_conductance(self):
        agents = ["a1", "a2", "a3", "a4", "a5", "a6"]
        n = len(agents)
        adj = [[0.0] * n for _ in range(n)]
        for i in range(3):
            for j in range(3):
                if i != j:
                    adj[i][j] = 1.0
                    adj[j][i] = 1.0
        for i in range(3, 6):
            for j in range(3, 6):
                if i != j:
                    adj[i][j] = 1.0
                    adj[j][i] = 1.0
        adj[2][3] = 0.1
        adj[3][2] = 0.1
        solver = SpectralSybilQuarantine(agents, adj)
        res = solver.solve()
        self.assertGreaterEqual(res.cheeger_conductance, 0.0)

    def test_fiedler_gap(self):
        agents = ["a1", "a2", "a3", "a4", "a5", "a6"]
        n = len(agents)
        adj = [[0.0] * n for _ in range(n)]
        for i in range(3):
            for j in range(3):
                if i != j:
                    adj[i][j] = 1.0
                    adj[j][i] = 1.0
        for i in range(3, 6):
            for j in range(3, 6):
                if i != j:
                    adj[i][j] = 1.0
                    adj[j][i] = 1.0
        adj[2][3] = 0.1
        adj[3][2] = 0.1
        solver = SpectralSybilQuarantine(agents, adj)
        res = solver.solve()
        self.assertGreaterEqual(res.spectral_fiedler_gap, 0.0)

    def test_algorithm_name(self):
        agents = ["a1", "a2", "a3", "a4", "a5", "a6"]
        n = len(agents)
        adj = [[0.0] * n for _ in range(n)]
        for i in range(3):
            for j in range(3):
                if i != j:
                    adj[i][j] = 1.0
                    adj[j][i] = 1.0
        for i in range(3, 6):
            for j in range(3, 6):
                if i != j:
                    adj[i][j] = 1.0
                    adj[j][i] = 1.0
        adj[2][3] = 0.1
        adj[3][2] = 0.1
        solver = SpectralSybilQuarantine(agents, adj)
        res = solver.solve()
        self.assertEqual(res.algorithm, "SPECTRAL_GRAPH_LAPLACIAN")

    def test_execution_time(self):
        agents = ["a1", "a2", "a3", "a4", "a5", "a6"]
        n = len(agents)
        adj = [[0.0] * n for _ in range(n)]
        for i in range(3):
            for j in range(3):
                if i != j:
                    adj[i][j] = 1.0
                    adj[j][i] = 1.0
        for i in range(3, 6):
            for j in range(3, 6):
                if i != j:
                    adj[i][j] = 1.0
                    adj[j][i] = 1.0
        adj[2][3] = 0.1
        adj[3][2] = 0.1
        solver = SpectralSybilQuarantine(agents, adj)
        res = solver.solve()
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_partition_complete(self):
        agents = ["a1", "a2", "a3", "a4", "a5", "a6"]
        n = len(agents)
        adj = [[0.0] * n for _ in range(n)]
        for i in range(3):
            for j in range(3):
                if i != j:
                    adj[i][j] = 1.0
                    adj[j][i] = 1.0
        for i in range(3, 6):
            for j in range(3, 6):
                if i != j:
                    adj[i][j] = 1.0
                    adj[j][i] = 1.0
        adj[2][3] = 0.1
        adj[3][2] = 0.1
        solver = SpectralSybilQuarantine(agents, adj)
        res = solver.solve()
        all_agents = set(res.quarantined_cluster + res.authentic_agents)
        self.assertEqual(all_agents, set(agents))

    def test_isolated_nodes(self):
        agents = ["a1", "a2", "a3", "a4", "a5", "a6"]
        adj = [[0.0] * 6 for _ in range(6)]
        solver = SpectralSybilQuarantine(agents, adj)
        res = solver.solve()
        self.assertIsInstance(res.quarantined_cluster, list)

    def test_strongly_connected(self):
        agents = ["a1", "a2", "a3", "a4", "a5", "a6"]
        n = len(agents)
        adj = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i != j:
                    adj[i][j] = 1.0
        solver = SpectralSybilQuarantine(agents, adj)
        res = solver.solve()
        self.assertIsInstance(res.quarantined_cluster, list)

    def test_max_iterations(self):
        agents = ["a1", "a2", "a3", "a4", "a5", "a6"]
        n = len(agents)
        adj = [[0.0] * n for _ in range(n)]
        for i in range(3):
            for j in range(3):
                if i != j:
                    adj[i][j] = 1.0
                    adj[j][i] = 1.0
        for i in range(3, 6):
            for j in range(3, 6):
                if i != j:
                    adj[i][j] = 1.0
                    adj[j][i] = 1.0
        adj[2][3] = 0.1
        adj[3][2] = 0.1
        solver = SpectralSybilQuarantine(agents, adj)
        res = solver.solve(max_iterations=50)
        self.assertIsInstance(res.quarantined_cluster, list)


class TestDisjunctiveEventScheduler(unittest.TestCase):
    """Tests for Asynchronous Disjunctive Event Scheduler solver."""

    def test_basic_scheduling(self):
        tasks = [
            TaskActivity("t1", "ag1", 10.0, [], 1),
            TaskActivity("t2", "ag2", 20.0, ["t1"], 1),
            TaskActivity("t3", "ag3", 15.0, [], 1),
        ]
        scheduler = DisjunctiveEventScheduler(tasks, num_workers=2)
        res = scheduler.solve()
        self.assertGreater(res.makespan, 0.0)
        self.assertEqual(len(res.task_start_times), 3)

    def test_empty_tasks(self):
        scheduler = DisjunctiveEventScheduler([], num_workers=2)
        res = scheduler.solve()
        self.assertEqual(res.task_start_times, {})

    def test_single_task(self):
        tasks = [TaskActivity("t1", "ag1", 10.0, [], 1)]
        scheduler = DisjunctiveEventScheduler(tasks, num_workers=2)
        res = scheduler.solve()
        self.assertEqual(res.makespan, 10.0)

    def test_precedence_constraints(self):
        tasks = [
            TaskActivity("t1", "ag1", 10.0, [], 1),
            TaskActivity("t2", "ag2", 20.0, ["t1"], 1),
        ]
        scheduler = DisjunctiveEventScheduler(tasks, num_workers=2)
        res = scheduler.solve()
        self.assertGreaterEqual(res.task_start_times["t2"], res.task_start_times["t1"] + 10.0)

    def test_parallel_tasks(self):
        tasks = [
            TaskActivity("t1", "ag1", 10.0, [], 1),
            TaskActivity("t2", "ag2", 10.0, [], 1),
        ]
        scheduler = DisjunctiveEventScheduler(tasks, num_workers=2)
        res = scheduler.solve()
        self.assertEqual(res.makespan, 10.0)

    def test_resource_utilization(self):
        tasks = [
            TaskActivity("t1", "ag1", 10.0, [], 1),
            TaskActivity("t2", "ag2", 10.0, [], 1),
        ]
        scheduler = DisjunctiveEventScheduler(tasks, num_workers=2)
        res = scheduler.solve()
        self.assertGreater(res.resource_utilization, 0.0)

    def test_algorithm_name(self):
        tasks = [TaskActivity("t1", "ag1", 10.0, [], 1)]
        scheduler = DisjunctiveEventScheduler(tasks, num_workers=1)
        res = scheduler.solve()
        self.assertEqual(res.algorithm, "DISJUNCTIVE_DAG_SCHEDULER")

    def test_execution_time(self):
        tasks = [TaskActivity("t1", "ag1", 10.0, [], 1)]
        scheduler = DisjunctiveEventScheduler(tasks, num_workers=1)
        res = scheduler.solve()
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_chain_dependencies(self):
        tasks = [
            TaskActivity("t1", "ag1", 5.0, [], 1),
            TaskActivity("t2", "ag2", 10.0, ["t1"], 1),
            TaskActivity("t3", "ag3", 15.0, ["t2"], 1),
        ]
        scheduler = DisjunctiveEventScheduler(tasks, num_workers=2)
        res = scheduler.solve()
        self.assertEqual(res.makespan, 30.0)

    def test_single_worker(self):
        tasks = [
            TaskActivity("t1", "ag1", 10.0, [], 1),
            TaskActivity("t2", "ag2", 20.0, [], 1),
        ]
        scheduler = DisjunctiveEventScheduler(tasks, num_workers=1)
        res = scheduler.solve()
        self.assertEqual(res.makespan, 30.0)

    def test_many_workers(self):
        tasks = [
            TaskActivity(f"t{i}", f"ag{i}", 10.0, [], 1)
            for i in range(5)
        ]
        scheduler = DisjunctiveEventScheduler(tasks, num_workers=10)
        res = scheduler.solve()
        self.assertEqual(res.makespan, 10.0)

    def test_diamond_dependencies(self):
        tasks = [
            TaskActivity("t1", "ag1", 10.0, [], 1),
            TaskActivity("t2", "ag2", 20.0, ["t1"], 1),
            TaskActivity("t3", "ag3", 15.0, ["t1"], 1),
            TaskActivity("t4", "ag4", 25.0, ["t2", "t3"], 1),
        ]
        scheduler = DisjunctiveEventScheduler(tasks, num_workers=2)
        res = scheduler.solve()
        self.assertGreater(res.makespan, 0.0)

    def test_utilization_cap(self):
        tasks = [
            TaskActivity("t1", "ag1", 10.0, [], 1),
            TaskActivity("t2", "ag2", 10.0, [], 1),
        ]
        scheduler = DisjunctiveEventScheduler(tasks, num_workers=2)
        res = scheduler.solve()
        self.assertLessEqual(res.resource_utilization, 100.0)


class TestParetoFrontierSolver(unittest.TestCase):
    """Tests for Multi-Objective Pareto Hypervolume Frontier solver."""

    def test_basic_frontier(self):
        candidates = [
            ParetoSolution("s1", [1.0, 2.0], {}),
            ParetoSolution("s2", [2.0, 1.0], {}),
            ParetoSolution("s3", [3.0, 3.0], {}),
        ]
        solver = ParetoFrontierSolver(candidates)
        res = solver.solve()
        self.assertGreater(len(res.non_dominated_solutions), 0)

    def test_empty_candidates(self):
        solver = ParetoFrontierSolver([])
        res = solver.solve()
        self.assertEqual(res.non_dominated_solutions, [])

    def test_single_candidate(self):
        candidates = [ParetoSolution("s1", [1.0, 2.0], {})]
        solver = ParetoFrontierSolver(candidates)
        res = solver.solve()
        self.assertEqual(len(res.non_dominated_solutions), 1)

    def test_dominated_solutions(self):
        candidates = [
            ParetoSolution("s1", [3.0, 3.0], {}),
            ParetoSolution("s2", [1.0, 1.0], {}),  # Dominated by s1
            ParetoSolution("s3", [2.0, 2.0], {}),  # Dominated by s1
        ]
        solver = ParetoFrontierSolver(candidates)
        res = solver.solve()
        self.assertEqual(len(res.non_dominated_solutions), 1)
        self.assertEqual(res.dominated_count, 2)

    def test_hypervolume_2d(self):
        candidates = [
            ParetoSolution("s1", [1.0, 3.0], {}),
            ParetoSolution("s2", [2.0, 2.0], {}),
            ParetoSolution("s3", [3.0, 1.0], {}),
        ]
        solver = ParetoFrontierSolver(candidates)
        res = solver.solve(reference_point=[0.0, 0.0])
        self.assertGreater(res.hypervolume_indicator, 0.0)

    def test_hypervolume_multi_d(self):
        candidates = [
            ParetoSolution("s1", [1.0, 2.0, 3.0], {}),
            ParetoSolution("s2", [3.0, 2.0, 1.0], {}),
        ]
        solver = ParetoFrontierSolver(candidates)
        res = solver.solve(reference_point=[0.0, 0.0, 0.0])
        self.assertGreaterEqual(res.hypervolume_indicator, 0.0)

    def test_algorithm_name(self):
        candidates = [ParetoSolution("s1", [1.0, 2.0], {})]
        solver = ParetoFrontierSolver(candidates)
        res = solver.solve()
        self.assertEqual(res.algorithm, "EXACT_NON_DOMINATED_SORTING")

    def test_execution_time(self):
        candidates = [ParetoSolution("s1", [1.0, 2.0], {})]
        solver = ParetoFrontierSolver(candidates)
        res = solver.solve()
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_all_non_dominated(self):
        candidates = [
            ParetoSolution("s1", [1.0, 3.0], {}),
            ParetoSolution("s2", [3.0, 1.0], {}),
        ]
        solver = ParetoFrontierSolver(candidates)
        res = solver.solve()
        self.assertEqual(len(res.non_dominated_solutions), 2)
        self.assertEqual(res.dominated_count, 0)

    def test_equal_solutions(self):
        candidates = [
            ParetoSolution("s1", [1.0, 2.0], {}),
            ParetoSolution("s2", [1.0, 2.0], {}),
        ]
        solver = ParetoFrontierSolver(candidates)
        res = solver.solve()
        # Neither dominates the other (equal)
        self.assertEqual(len(res.non_dominated_solutions), 2)

    def test_many_candidates(self):
        candidates = [
            ParetoSolution(f"s{i}", [float(i), float(10 - i)], {})
            for i in range(10)
        ]
        solver = ParetoFrontierSolver(candidates)
        res = solver.solve()
        self.assertGreater(len(res.non_dominated_solutions), 0)

    def test_reference_point(self):
        candidates = [
            ParetoSolution("s1", [5.0, 5.0], {}),
            ParetoSolution("s2", [3.0, 3.0], {}),
        ]
        solver = ParetoFrontierSolver(candidates)
        res = solver.solve(reference_point=[1.0, 1.0])
        self.assertGreater(res.hypervolume_indicator, 0.0)

    def test_default_reference_point(self):
        candidates = [
            ParetoSolution("s1", [5.0, 5.0], {}),
        ]
        solver = ParetoFrontierSolver(candidates)
        res = solver.solve()
        self.assertGreaterEqual(res.hypervolume_indicator, 0.0)


if __name__ == '__main__':
    unittest.main()
