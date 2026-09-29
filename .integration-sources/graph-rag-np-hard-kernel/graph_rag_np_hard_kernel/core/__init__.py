"""Core mathematical solvers for Graph Engineering and GraphRAG NP-Hard bottlenecks."""
from .models import (
    GraphNode, GraphEdge, SteinerTreeResult, CommunityPartitionResult,
    EntityMention, CorrelationClusteringResult, TemporalCausalEdge,
    ConstrainedPathResult, KnowledgeUnit, SubmodularSummaryResult,
    PatternEdge, IsomorphismResult, SparsificationResult,
    OntologyNode, AlignmentResult, MetricDimensionResult, AnonymizationResult
)
from .subgraph_extraction import PrizeCollectingSteinerTreeSolver
from .community_detection import HierarchicalCommunityDetector
from .entity_resolution import CorrelationClusteringEntityResolver
from .constrained_path import ConstrainedCausalPathFinder
from .submodular_graph_summary import SubmodularGraphSummarizer
from .temporal_subgraph_isomorphism import TemporalSubgraphMatcher
from .spectral_sparsifier import SpectralGraphSparsifier
from .bipartite_alignment import BipartiteOntologyAligner
from .metric_dimension import MetricDimensionLandmarkFinder
from .graph_anonymizer import KDegreeGraphAnonymizer

__all__ = [
    "GraphNode", "GraphEdge", "SteinerTreeResult", "CommunityPartitionResult",
    "EntityMention", "CorrelationClusteringResult", "TemporalCausalEdge",
    "ConstrainedPathResult", "KnowledgeUnit", "SubmodularSummaryResult",
    "PatternEdge", "IsomorphismResult", "SparsificationResult",
    "OntologyNode", "AlignmentResult", "MetricDimensionResult", "AnonymizationResult",
    "PrizeCollectingSteinerTreeSolver",
    "HierarchicalCommunityDetector",
    "CorrelationClusteringEntityResolver",
    "ConstrainedCausalPathFinder",
    "SubmodularGraphSummarizer",
    "TemporalSubgraphMatcher",
    "SpectralGraphSparsifier",
    "BipartiteOntologyAligner",
    "MetricDimensionLandmarkFinder",
    "KDegreeGraphAnonymizer",
]
