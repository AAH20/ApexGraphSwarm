"""Core models and data structures for MiroFish Swarm Optimization."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Set, Tuple, Optional, Any

class AgentFaction(Enum):
    SOVEREIGN_STATE = "SOVEREIGN_STATE"
    INSTITUTIONAL_CAPITAL = "INSTITUTIONAL_CAPITAL"
    PUBLIC_OPINION_BLOC = "PUBLIC_OPINION_BLOC"
    MEDIA_INFLUENCER = "MEDIA_INFLUENCER"
    REGULATORY_BODY = "REGULATORY_BODY"

@dataclass
class SwarmAgent:
    agent_id: str
    name: str
    faction: AgentFaction
    influence_weight: float
    belief_vector: List[float]  # Multi-dimensional stance [-1.0, 1.0]
    token_budget: int = 1000

@dataclass
class Coalition:
    members: Tuple[str, ...]
    value: float
    internal_synergy: float

@dataclass
class CoalitionStructureResult:
    coalitions: List[Coalition]
    total_welfare: float
    algorithm: str
    execution_time_us: float
    iterations: int = 1

@dataclass
class InfluenceResult:
    seed_agents: List[str]
    expected_reach: float
    activation_percentage: float
    algorithm: str
    execution_time_us: float

@dataclass
class ConsensusRankingResult:
    ranked_outcomes: List[str]
    total_kendall_tau_distance: float
    agreement_score: float
    algorithm: str
    execution_time_us: float

@dataclass
class AttentionTier:
    tier_id: int
    name: str
    token_cost: int
    fidelity_multiplier: float

@dataclass
class AttentionAllocationResult:
    agent_tier_map: Dict[str, AttentionTier]
    total_tokens_used: int
    budget_limit: int
    total_decision_fidelity: float
    algorithm: str
    execution_time_us: float

@dataclass
class CFRResult:
    equilibrium_strategies: Dict[str, Dict[str, float]]  # agent_id -> action -> prob
    expected_payoffs: Dict[str, float]
    iterations: int
    exploitability: float
    algorithm: str
    execution_time_us: float

@dataclass
class MemoryItem:
    item_id: str
    entity_tag: str
    content: str
    salience_score: float
    timestamp: float
    embedding_vector: List[float]

@dataclass
class MemorySummaryResult:
    selected_items: List[MemoryItem]
    total_coverage_score: float
    diversity_metric: float
    reduction_ratio: float
    algorithm: str
    execution_time_us: float

@dataclass
class QuarantineResult:
    quarantined_cluster: List[str]
    authentic_agents: List[str]
    cheeger_conductance: float
    spectral_fiedler_gap: float
    algorithm: str
    execution_time_us: float

@dataclass
class TaskActivity:
    task_id: str
    agent_id: str
    duration: float
    predecessors: List[str]
    required_worker: int

@dataclass
class ScheduleResult:
    task_start_times: Dict[str, float]
    makespan: float
    resource_utilization: float
    algorithm: str
    execution_time_us: float

@dataclass
class ParetoSolution:
    solution_id: str
    objective_values: List[float]  # All to be maximized
    parameter_payload: Dict[str, Any]

@dataclass
class ParetoFrontierResult:
    non_dominated_solutions: List[ParetoSolution]
    hypervolume_indicator: float
    dominated_count: int
    algorithm: str
    execution_time_us: float

@dataclass
class BenchmarkComparison:
    problem_name: str
    optimizer_algorithm: str
    optimizer_score: float
    optimizer_latency_us: float
    evolutionary_baseline: str
    baseline_score: float
    baseline_latency_us: float
    speedup_multiplier: float
    quality_advantage_pct: float
