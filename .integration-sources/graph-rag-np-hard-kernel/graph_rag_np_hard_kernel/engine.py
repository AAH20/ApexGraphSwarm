"""Unified Engine Facade for Graph Engineering & GraphRAG NP-Hard Optimization."""
from typing import List, Dict, Tuple, Optional, Any, Set
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
from .adapters.biomedical_genomics_rag import run_biomedical_rag_benchmark
from .adapters.financial_fraud_kg import run_financial_fraud_benchmark

class GraphRAGNPHardEngine:
    """
    Unified Engine solving the 10 Fundamental NP-Hard Computational Bottlenecks
    in Modern Graph Engineering and GraphRAG Knowledge Graph Systems.
    Pure Python 3.10+ Standard Library with microsecond/sub-millisecond deterministic guarantees.
    """

    # 1. Prize-Collecting Steiner Tree (PCST)
    def extract_steiner_subgraph(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        root_seed_id: Optional[str] = None
    ) -> SteinerTreeResult:
        solver = PrizeCollectingSteinerTreeSolver(nodes, edges)
        return solver.solve(root_seed_id)

    # 2. Modularity Maximization Community Detection
    def detect_communities_modularity(
        self,
        nodes: List[str],
        edges: List[Tuple[str, str, float]],
        gamma: float = 1.0
    ) -> CommunityPartitionResult:
        detector = HierarchicalCommunityDetector(nodes, edges, gamma)
        return detector.solve()

    # 3. Entity Resolution & Correlation Clustering
    def resolve_entities_correlation(
        self,
        mentions: List[EntityMention],
        affinity_threshold: float = 0.70
    ) -> CorrelationClusteringResult:
        resolver = CorrelationClusteringEntityResolver(mentions, affinity_threshold)
        return resolver.solve()

    # 4. Constrained Shortest Path Causal Reasoning
    def find_constrained_causal_path(
        self,
        edges: List[TemporalCausalEdge],
        source: str,
        target: str,
        max_delay_hours: float = 72.0,
        min_confidence: float = 0.50
    ) -> ConstrainedPathResult:
        finder = ConstrainedCausalPathFinder(edges)
        return finder.solve(source, target, max_delay_hours, min_confidence)

    # 5. Submodular Graph Summarization for Context Windows
    def summarize_graph_submodular(
        self,
        units: List[KnowledgeUnit],
        token_budget: int = 4000
    ) -> SubmodularSummaryResult:
        summarizer = SubmodularGraphSummarizer(units)
        return summarizer.solve(token_budget)

    # 6. Temporal Subgraph Isomorphism
    def match_temporal_subgraph(
        self,
        target_edges: List[GraphEdge],
        pattern_edges: List[PatternEdge]
    ) -> IsomorphismResult:
        matcher = TemporalSubgraphMatcher(target_edges)
        return matcher.match(pattern_edges)

    # 7. Degree-Constrained Spectral Sparsification
    def sparsify_graph_spectral(
        self,
        nodes: List[str],
        edges: List[Tuple[str, str, float]],
        max_degree: int = 4
    ) -> SparsificationResult:
        sparsifier = SpectralGraphSparsifier(nodes, edges)
        return sparsifier.sparsify(max_degree)

    # 8. Bipartite Text-to-Ontology Alignment
    def align_bipartite_ontology(
        self,
        mentions: List[str],
        ontology_nodes: List[OntologyNode],
        affinities: Dict[Tuple[str, str], float]
    ) -> AlignmentResult:
        aligner = BipartiteOntologyAligner(mentions, ontology_nodes)
        return aligner.solve(affinities)

    # 9. Metric Dimension & Resolving Landmarks
    def find_metric_dimension_landmarks(
        self,
        nodes: List[str],
        edges: List[Tuple[str, str]]
    ) -> MetricDimensionResult:
        finder = MetricDimensionLandmarkFinder(nodes, edges)
        return finder.solve()

    # 10. k-Degree Anonymity Graph Sanitization
    def anonymize_graph_k_degree(
        self,
        nodes: List[str],
        edges: List[Tuple[str, str]],
        k: int = 3
    ) -> AnonymizationResult:
        anonymizer = KDegreeGraphAnonymizer(nodes, edges)
        return anonymizer.anonymize(k)

    # Scenario Benchmarks
    def run_biomedical_benchmark(self) -> Dict[str, Any]:
        return run_biomedical_rag_benchmark()

    def run_financial_benchmark(self) -> Dict[str, Any]:
        return run_financial_fraud_benchmark()
