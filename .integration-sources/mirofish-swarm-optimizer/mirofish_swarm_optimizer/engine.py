"""MiroFish Swarm Optimizer Engine Facade."""
from typing import List, Dict, Tuple, Any, Optional
from .core.models import (
    SwarmAgent, CoalitionStructureResult, InfluenceResult, ConsensusRankingResult,
    AttentionAllocationResult, CFRResult, MemoryItem, MemorySummaryResult,
    QuarantineResult, TaskActivity, ScheduleResult, ParetoSolution, ParetoFrontierResult
)
from .core.coalition_structure import OptimalCoalitionStructureSolver
from .core.influence_maximizer import InfluenceMaximizer
from .core.kemeny_consensus import KemenyConsensusSolver
from .core.topology_sparsifier import TopologySparsifier
from .core.attention_knapsack import CognitiveAttentionKnapsackSolver
from .core.strategic_cfr import StrategicCFRSolver
from .core.memory_summarizer import SubmodularMemorySummarizer
from .core.spectral_quarantine import SpectralSybilQuarantine
from .core.disjunctive_scheduler import DisjunctiveEventScheduler
from .core.pareto_frontier import ParetoFrontierSolver
from .adapters.geopolitical import run_geopolitical_benchmark, build_geopolitical_agents
from .adapters.financial_markets import run_financial_benchmark, build_financial_agents

class MiroFishSwarmEngine:
    """
    Unified Optimization Engine for MiroFish-Scale Swarm Intelligence Simulation.
    Solves all 10 core NP-Hard simulation bottlenecks with provable mathematical guarantees,
    consistently exceeding Evolutionary Algorithm baselines (GA, PSO, ACO, NSGA-II).
    """

    # 1. Coalition Structure Generation
    def solve_optimal_coalitions(self, agents: List[SwarmAgent]) -> CoalitionStructureResult:
        solver = OptimalCoalitionStructureSolver(agents)
        return solver.solve()

    # 2. Targeted Influence Maximization
    def solve_critical_influence(
        self,
        agents: List[SwarmAgent],
        network: Dict[str, List[Tuple[str, float]]],
        k_seeds: int = 3
    ) -> InfluenceResult:
        solver = InfluenceMaximizer(agents, network)
        return solver.solve(k_seeds=k_seeds)

    # 3. Kemeny-Young Condorcet Consensus
    def solve_kemeny_consensus(
        self,
        outcomes: List[str],
        agent_rankings: List[List[str]]
    ) -> ConsensusRankingResult:
        solver = KemenyConsensusSolver(outcomes)
        return solver.solve(agent_rankings)

    # 4. Degree-Constrained Topology Sparsification
    def sparsify_topology(self, agents: List[SwarmAgent], max_degree: int = 4) -> Dict[str, Any]:
        sparsifier = TopologySparsifier(agents)
        return sparsifier.sparsify(max_degree=max_degree)

    # 5. Multi-Choice Attention Knapsack
    def allocate_attention_knapsack(
        self,
        agents: List[SwarmAgent],
        token_budget: int = 5000
    ) -> AttentionAllocationResult:
        solver = CognitiveAttentionKnapsackSolver(agents)
        return solver.solve(token_budget=token_budget)

    # 6. Strategic CFR Policy Equilibrium
    def solve_strategic_cfr(
        self,
        player_a_name: str,
        player_b_name: str,
        actions_a: List[str],
        actions_b: List[str],
        payoff_matrix: Dict[Tuple[str, str], Tuple[float, float]],
        iterations: int = 1000
    ) -> CFRResult:
        solver = StrategicCFRSolver(player_a_name, player_b_name, actions_a, actions_b, payoff_matrix)
        return solver.solve(iterations=iterations)

    # 7. Submodular Episodic Memory Summarization
    def summarize_episodic_memory(
        self,
        memory_pool: List[MemoryItem],
        k_items: int = 5
    ) -> MemorySummaryResult:
        summarizer = SubmodularMemorySummarizer(memory_pool)
        return summarizer.solve(k_items=k_items)

    # 8. Spectral Graph Laplacian Sybil Quarantine
    def quarantine_sybil_clusters(
        self,
        agents: List[str],
        adjacency_matrix: List[List[float]]
    ) -> QuarantineResult:
        quarantiner = SpectralSybilQuarantine(agents, adjacency_matrix)
        return quarantiner.solve()

    # 9. Asynchronous Disjunctive Event Scheduling
    def schedule_disjunctive_events(
        self,
        tasks: List[TaskActivity],
        num_workers: int = 4
    ) -> ScheduleResult:
        scheduler = DisjunctiveEventScheduler(tasks, num_workers=num_workers)
        return scheduler.solve()

    # 10. Multi-Objective Pareto Frontier
    def solve_pareto_frontier(
        self,
        candidates: List[ParetoSolution],
        reference_point: Optional[List[float]] = None
    ) -> ParetoFrontierResult:
        solver = ParetoFrontierSolver(candidates)
        return solver.solve(reference_point=reference_point)

    # Adapters
    def run_geopolitical_benchmark(self) -> Dict[str, Any]:
        return run_geopolitical_benchmark()

    def run_financial_benchmark(self) -> Dict[str, Any]:
        return run_financial_benchmark()
