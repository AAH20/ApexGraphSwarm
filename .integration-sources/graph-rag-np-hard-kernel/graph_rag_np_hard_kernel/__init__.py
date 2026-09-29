"""
GraphRAG NP-Hard Kernel: The Mathematical Operating Substrate for Graph Engineering and GraphRAG.
Deterministically solving the 10 apex NP-Hard computational bottlenecks across:
PCST subgraph extraction, modularity maximization, correlation clustering entity resolution,
constrained causal paths, submodular context summarization, temporal subgraph isomorphism,
spectral sparsification, bipartite ontology alignment, metric dimension, and k-degree anonymity.
"""

from .core.models import (
    GraphNode, GraphEdge, SteinerTreeResult, CommunityPartitionResult,
    EntityMention, CorrelationClusteringResult, TemporalCausalEdge,
    ConstrainedPathResult, KnowledgeUnit, SubmodularSummaryResult,
    PatternEdge, IsomorphismResult, SparsificationResult,
    OntologyNode, AlignmentResult, MetricDimensionResult, AnonymizationResult
)
from .core.subgraph_extraction import PrizeCollectingSteinerTreeSolver
from .core.community_detection import HierarchicalCommunityDetector
from .core.entity_resolution import CorrelationClusteringEntityResolver
from .core.constrained_path import ConstrainedCausalPathFinder
from .core.submodular_graph_summary import SubmodularGraphSummarizer
from .core.temporal_subgraph_isomorphism import TemporalSubgraphMatcher
from .core.spectral_sparsifier import SpectralGraphSparsifier
from .core.bipartite_alignment import BipartiteOntologyAligner
from .core.metric_dimension import MetricDimensionLandmarkFinder
from .core.graph_anonymizer import KDegreeGraphAnonymizer
from .engine import GraphRAGNPHardEngine

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
    "GraphRAGNPHardEngine",
]

__version__ = "1.0.0"
