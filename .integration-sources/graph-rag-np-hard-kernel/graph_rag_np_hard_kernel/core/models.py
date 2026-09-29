"""Data contracts and model definitions for the 10 Apex NP-Hard Problems in Graph Engineering and GraphRAG."""
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional, Any

# --- Problem 1: Prize-Collecting Steiner Tree (PCST) Subgraph Extraction ---
@dataclass
class GraphNode:
    node_id: str
    label: str
    prize: float  # Query relevance score [0, 100]
    attributes: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GraphEdge:
    source: str
    target: str
    weight: float  # Traversal penalty / communication cost
    relation_type: str = "RELATED_TO"
    timestamp: float = 0.0

@dataclass
class SteinerTreeResult:
    selected_nodes: List[str]
    selected_edges: List[Tuple[str, str]]
    total_prize: float
    total_cost: float
    net_utility: float
    is_connected: bool
    algorithm: str
    execution_time_us: float

# --- Problem 2: Modularity Maximization & Hierarchical Community Detection ---
@dataclass
class CommunityPartitionResult:
    communities: Dict[int, List[str]]  # community_id -> node_ids
    modularity_score: float  # Q score [-0.5, 1.0]
    num_communities: int
    algorithm: str
    execution_time_us: float

# --- Problem 3: Entity Resolution & Correlation Clustering ---
@dataclass
class EntityMention:
    mention_id: str
    surface_text: str
    embedding: List[float]
    source_chunk_id: str

@dataclass
class CorrelationClusteringResult:
    resolved_clusters: Dict[str, List[str]]  # canonical_entity_id -> mention_ids
    total_conflicts_cut: float
    cluster_count: int
    algorithm: str
    execution_time_us: float

# --- Problem 4: Constrained Shortest Path Causal Reasoning ---
@dataclass
class TemporalCausalEdge:
    source: str
    target: str
    traversal_cost: float
    delay_hours: float
    confidence: float  # [0, 1]
    timestamp: float

@dataclass
class ConstrainedPathResult:
    path_nodes: List[str]
    total_cost: float
    total_delay_hours: float
    bottleneck_confidence: float
    is_causally_valid: bool
    algorithm: str
    execution_time_us: float

# --- Problem 5: Submodular Graph Summarization for Context Windows ---
@dataclass
class KnowledgeUnit:
    unit_id: str
    text_summary: str
    token_count: int
    covered_entities: Set[str]
    salience_score: float

@dataclass
class SubmodularSummaryResult:
    selected_units: List[KnowledgeUnit]
    total_tokens: int
    total_entity_coverage: int
    diversity_score: float
    algorithm: str
    execution_time_us: float

# --- Problem 6: Temporal Subgraph Isomorphism Matching ---
@dataclass
class PatternEdge:
    source_var: str
    target_var: str
    relation_type: str
    min_time_delta: float = 0.0
    max_time_delta: float = float('inf')

@dataclass
class IsomorphismResult:
    matched_subgraphs: List[Dict[str, str]]  # pattern_var -> graph_node_id
    total_matches: int
    algorithm: str
    execution_time_us: float

# --- Problem 7: Degree-Constrained Spectral Sparsification ---
@dataclass
class SparsificationResult:
    retained_edges: List[Tuple[str, str]]
    edge_reduction_pct: float
    algebraic_connectivity_ratio: float
    max_observed_degree: int
    algorithm: str
    execution_time_us: float

# --- Problem 8: Bipartite Text-to-Ontology Alignment ---
@dataclass
class OntologyNode:
    onto_id: str
    canonical_name: str
    domain_category: str

@dataclass
class AlignmentResult:
    matched_pairs: List[Tuple[str, str, float]]  # (mention_id, onto_id, affinity)
    total_alignment_weight: float
    unmapped_entities_count: int
    algorithm: str
    execution_time_us: float

# --- Problem 9: Metric Dimension & Resolving Landmarks ---
@dataclass
class MetricDimensionResult:
    landmark_nodes: List[str]
    metric_dimension_k: int
    uniquely_resolved_percentage: float
    algorithm: str
    execution_time_us: float

# --- Problem 10: k-Degree Anonymity Graph Sanitization ---
@dataclass
class AnonymizationResult:
    added_edges: List[Tuple[str, str]]
    removed_edges: List[Tuple[str, str]]
    k_anonymity_degree: int
    graph_distortion_ratio: float
    algorithm: str
    execution_time_us: float
