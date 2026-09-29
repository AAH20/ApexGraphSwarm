"""
MiroFish Swarm Optimizer: NP-Hard Multi-Agent Simulation Engine.
Exceeding Evolutionary Algorithms (GA, PSO, ACO, NSGA-II) through exact dynamic programming,
submodular guarantees, spectral graph theory, and tournament elimination.
"""

from .core.models import (
    AgentFaction, SwarmAgent, Coalition, CoalitionStructureResult,
    InfluenceResult, ConsensusRankingResult, BenchmarkComparison,
    AttentionTier, AttentionAllocationResult, CFRResult, MemoryItem,
    MemorySummaryResult, QuarantineResult, TaskActivity, ScheduleResult,
    ParetoSolution, ParetoFrontierResult
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
from .engine import MiroFishSwarmEngine

__all__ = [
    "AgentFaction",
    "SwarmAgent",
    "Coalition",
    "CoalitionStructureResult",
    "InfluenceResult",
    "ConsensusRankingResult",
    "BenchmarkComparison",
    "AttentionTier",
    "AttentionAllocationResult",
    "CFRResult",
    "MemoryItem",
    "MemorySummaryResult",
    "QuarantineResult",
    "TaskActivity",
    "ScheduleResult",
    "ParetoSolution",
    "ParetoFrontierResult",
    "OptimalCoalitionStructureSolver",
    "InfluenceMaximizer",
    "KemenyConsensusSolver",
    "TopologySparsifier",
    "CognitiveAttentionKnapsackSolver",
    "StrategicCFRSolver",
    "SubmodularMemorySummarizer",
    "SpectralSybilQuarantine",
    "DisjunctiveEventScheduler",
    "ParetoFrontierSolver",
    "MiroFishSwarmEngine",
]

__version__ = "1.1.0"
