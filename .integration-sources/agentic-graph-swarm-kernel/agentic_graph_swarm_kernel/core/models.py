"""Data contracts and model definitions for the 10 Apex NP-Hard Problems in Agentic Graph Engineering and Swarm Orchestration."""
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional, Any

# --- Problem 1: Dynamic Hypergraph Coalition Structure Generation (H-CSG) ---
@dataclass
class AgentProfile:
    agent_id: str
    capabilities: List[str]
    efficiency_weight: float = 1.0

@dataclass
class KnowledgeHyperedge:
    hyperedge_id: str
    target_concept: str
    required_capabilities: List[str]
    value: float
    participating_agents: List[str] = field(default_factory=list)

@dataclass
class HypergraphCSGResult:
    coalitions: List[List[str]]  # list of agent_id subsets
    total_coalition_value: float
    unassigned_agents: List[str]
    algorithm: str
    execution_time_us: float

# --- Problem 2: Causal Reasoning DAG Topology Synthesis under BIC/MDL ---
@dataclass
class VariableObservation:
    var_id: str
    name: str
    sample_values: List[float]

@dataclass
class CausalDAGResult:
    adjacency_matrix: Dict[str, List[str]]  # source_var -> [target_vars]
    bic_score: float
    is_acyclic: bool
    algorithm: str
    execution_time_us: float

# --- Problem 3: Cross-Agent Epistemic Consensus over Attributed Knowledge Hypergraphs ---
@dataclass
class FactStatement:
    subject: str
    predicate: str
    obj: str
    confidence: float

@dataclass
class AgentBeliefGraph:
    agent_id: str
    reputation: float
    statements: List[FactStatement]

@dataclass
class EpistemicConsensusResult:
    consensus_graph: List[FactStatement]
    kemeny_distance: float
    cycle_free_certified: bool
    algorithm: str
    execution_time_us: float

# --- Problem 4: Context-Budgeted Submodular Knowledge Graph Attention Routing ---
@dataclass
class KnowledgeNode:
    node_id: str
    content_token_length: int
    information_entropy: float
    concept_tags: Set[str]

@dataclass
class AgentContextBudget:
    agent_id: str
    max_token_capacity: int
    focus_concepts: Set[str]

@dataclass
class AttentionRoutingResult:
    routed_subgraphs: Dict[str, List[str]]  # agent_id -> [node_ids]
    total_information_coverage: float
    context_utilization_pct: float
    algorithm: str
    execution_time_us: float

# --- Problem 5: Autonomous Swarm Memory Topology Sparsification & Decay ---
@dataclass
class MemoryNode:
    node_id: str
    timestamp: float
    access_count: int

@dataclass
class MemoryEdge:
    source_id: str
    target_id: str
    semantic_weight: float
    effective_resistance: float = 1.0

@dataclass
class SpectralDecayResult:
    retained_nodes: List[str]
    retained_edges: List[Tuple[str, str]]
    spectral_compression_ratio: float
    causal_connectivity_preserved: bool
    algorithm: str
    execution_time_us: float

# --- Problem 6: Disjunctive Swarm Task Scheduling with Multi-Tool Resource Contention ---
@dataclass
class AgentToolTask:
    task_id: str
    agent_id: str
    tool_resource_id: str
    duration_ms: int
    precedence_prereqs: List[str] = field(default_factory=list)

@dataclass
class ToolResource:
    resource_id: str
    capacity: int = 1  # mutex or multi-instance pool

@dataclass
class DisjunctiveToolScheduleResult:
    schedule: Dict[str, Tuple[int, int]]  # task_id -> (start_ms, end_ms)
    makespan_ms: int
    deadlock_free_certified: bool
    algorithm: str
    execution_time_us: float

# --- Problem 7: Byzantine-Resilient Epistemic Truth Discovery on Distributed Graphs ---
@dataclass
class AgentClaim:
    claim_id: str
    agent_id: str
    entity_id: str
    attribute_name: str
    claimed_value: str
    timestamp: float

@dataclass
class TruthDiscoveryResult:
    resolved_attributes: Dict[str, str]  # entity_id.attribute -> true_value
    quarantined_byzantine_agents: List[str]
    overall_truth_confidence: float
    algorithm: str
    execution_time_us: float

# --- Problem 8: Evolutionary Swarm Graph Grammar & Architecture Search ---
@dataclass
class SwarmTopologyGenome:
    genome_id: str
    adjacency_matrix: Dict[str, List[str]]
    fitness_score: float = 0.0
    structural_complexity: float = 0.0

@dataclass
class TopologyEvolutionResult:
    best_topology: Dict[str, List[str]]
    pareto_frontier_size: int
    generation_reached: int
    best_fitness: float
    algorithm: str
    execution_time_us: float

# --- Problem 9: Temporal Subgraph Isomorphism for Emergent Swarm Behavior Detection ---
@dataclass
class TemporalEvent:
    event_id: str
    source_agent: str
    target_agent: str
    action_type: str
    timestamp: float

@dataclass
class BehaviorPattern:
    pattern_id: str
    sequence_actions: List[str]
    max_delta_time: float

@dataclass
class TemporalPatternResult:
    detected_instances: List[List[str]]  # lists of event_ids matching the emergent pattern
    total_detections: int
    causality_strictly_ordered: bool
    algorithm: str
    execution_time_us: float

# --- Problem 10: Multi-Agent Pareto Game-Theoretic Coordination on Hypergraphs ---
@dataclass
class PlayerAgent:
    player_id: str
    action_space: List[str]

@dataclass
class HyperedgePayoff:
    hyperedge_id: str
    participating_players: List[str]
    joint_action_payoffs: Dict[Tuple[str, ...], Dict[str, float]]  # joint_action -> {player: payoff}

@dataclass
class ParetoGameResult:
    equilibrium_strategies: Dict[str, Dict[str, float]]  # player_id -> {action: probability}
    expected_social_welfare: float
    pareto_efficient: bool
    algorithm: str
    execution_time_us: float
