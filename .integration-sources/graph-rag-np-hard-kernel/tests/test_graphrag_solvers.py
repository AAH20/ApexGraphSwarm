"""Comprehensive unit test suite for the 10 Apex NP-Hard GraphRAG & Graph Engineering Solvers."""
import unittest
from graph_rag_np_hard_kernel.engine import GraphRAGNPHardEngine
from graph_rag_np_hard_kernel.core.models import (
    GraphNode, GraphEdge, EntityMention, TemporalCausalEdge,
    KnowledgeUnit, PatternEdge, OntologyNode
)
from graph_rag_np_hard_kernel.core.subgraph_extraction import PrizeCollectingSteinerTreeSolver
from graph_rag_np_hard_kernel.core.community_detection import HierarchicalCommunityDetector
from graph_rag_np_hard_kernel.core.entity_resolution import CorrelationClusteringEntityResolver
from graph_rag_np_hard_kernel.core.constrained_path import ConstrainedCausalPathFinder
from graph_rag_np_hard_kernel.core.submodular_graph_summary import SubmodularGraphSummarizer
from graph_rag_np_hard_kernel.core.temporal_subgraph_isomorphism import TemporalSubgraphMatcher
from graph_rag_np_hard_kernel.core.spectral_sparsifier import SpectralGraphSparsifier
from graph_rag_np_hard_kernel.core.bipartite_alignment import BipartiteOntologyAligner
from graph_rag_np_hard_kernel.core.metric_dimension import MetricDimensionLandmarkFinder
from graph_rag_np_hard_kernel.core.graph_anonymizer import KDegreeGraphAnonymizer

class TestGraphRAGNPHardSolvers(unittest.TestCase):

    def setUp(self):
        self.engine = GraphRAGNPHardEngine()

    # 1. PCST Subgraph Extraction
    def test_pcst_subgraph_extraction(self):
        nodes = [
            GraphNode("N1", "Entity", 50.0),
            GraphNode("N2", "Entity", 40.0),
            GraphNode("N3", "Entity", 10.0),
            GraphNode("N4", "Noise", 0.0),
        ]
        edges = [
            GraphEdge("N1", "N2", 5.0),
            GraphEdge("N2", "N3", 4.0),
            GraphEdge("N3", "N4", 30.0),  # High cost edge to low prize node
        ]
        solver = PrizeCollectingSteinerTreeSolver(nodes, edges)
        res = solver.solve("N1")

        self.assertIn("N1", res.selected_nodes)
        self.assertIn("N2", res.selected_nodes)
        self.assertNotIn("N4", res.selected_nodes)  # Noise node must be pruned
        self.assertTrue(res.is_connected)
        self.assertGreater(res.net_utility, 0.0)

    # 2. Modularity Community Detection
    def test_modularity_community_detection(self):
        # Two triangles with a weak bridge
        nodes = ["A1", "A2", "A3", "B1", "B2", "B3"]
        edges = [
            ("A1", "A2", 10.0), ("A2", "A3", 10.0), ("A3", "A1", 10.0),
            ("B1", "B2", 10.0), ("B2", "B3", 10.0), ("B3", "B1", 10.0),
            ("A3", "B1", 1.0),
        ]
        detector = HierarchicalCommunityDetector(nodes, edges, gamma=1.0)
        res = detector.solve()

        self.assertEqual(res.num_communities, 2)
        self.assertGreater(res.modularity_score, 0.3)

    # 3. Entity Resolution & Correlation Clustering
    def test_entity_resolution_correlation_clustering(self):
        mentions = [
            EntityMention("M1", "Apple Inc", [1.0, 0.0], "c1"),
            EntityMention("M2", "Apple", [0.98, 0.02], "c2"),
            EntityMention("M3", "Microsoft", [0.0, 1.0], "c3"),
            EntityMention("M4", "MSFT", [0.05, 0.95], "c4"),
        ]
        resolver = CorrelationClusteringEntityResolver(mentions, affinity_threshold=0.7)
        res = resolver.solve()

        self.assertEqual(res.cluster_count, 2)
        # Verify M1 and M2 in same cluster, M3 and M4 in same cluster
        cluster_sets = [set(c) for c in res.resolved_clusters.values()]
        self.assertTrue(any({"M1", "M2"}.issubset(s) for s in cluster_sets))
        self.assertTrue(any({"M3", "M4"}.issubset(s) for s in cluster_sets))

    # 4. Constrained Causal Path
    def test_constrained_causal_path(self):
        edges = [
            TemporalCausalEdge("A", "B", 10.0, 5.0, 0.95, 10.0),
            TemporalCausalEdge("B", "C", 10.0, 5.0, 0.90, 20.0),
            TemporalCausalEdge("A", "C_NON_CAUSAL", 5.0, 2.0, 0.99, 30.0),
            TemporalCausalEdge("C_NON_CAUSAL", "C", 5.0, 2.0, 0.99, 15.0),  # violates t2 >= t1
        ]
        finder = ConstrainedCausalPathFinder(edges)
        res = finder.solve("A", "C", max_delay_hours=15.0)

        self.assertTrue(res.is_causally_valid)
        self.assertEqual(res.path_nodes, ["A", "B", "C"])
        self.assertEqual(res.total_cost, 20.0)

    # 5. Submodular Graph Summarization
    def test_submodular_graph_summarization(self):
        units = [
            KnowledgeUnit("U1", "Doc 1", 50, {"X", "Y"}, 1.0),
            KnowledgeUnit("U2", "Doc 2 Duplicate", 50, {"X", "Y"}, 0.9),
            KnowledgeUnit("U3", "Doc 3 Novel", 50, {"Z", "W"}, 1.0),
        ]
        summarizer = SubmodularGraphSummarizer(units)
        res = summarizer.solve(token_budget=100)

        self.assertEqual(len(res.selected_units), 2)
        unit_ids = {u.unit_id for u in res.selected_units}
        self.assertIn("U1", unit_ids)
        self.assertIn("U3", unit_ids)  # U3 chosen for coverage over duplicate U2
        self.assertEqual(res.total_entity_coverage, 4)

    # 6. Temporal Subgraph Isomorphism
    def test_temporal_subgraph_isomorphism(self):
        target_edges = [
            GraphEdge("X", "Y", 1.0, "TRANSFERS_TO", 1.0),
            GraphEdge("Y", "Z", 1.0, "TRANSFERS_TO", 2.0),
            GraphEdge("P", "Q", 1.0, "UNRELATED", 3.0),
        ]
        pattern = [
            PatternEdge("A", "B", "TRANSFERS_TO"),
            PatternEdge("B", "C", "TRANSFERS_TO"),
        ]
        matcher = TemporalSubgraphMatcher(target_edges)
        res = matcher.match(pattern)

        self.assertEqual(res.total_matches, 1)
        self.assertEqual(res.matched_subgraphs[0], {"A": "X", "B": "Y", "C": "Z"})

    # 7. Degree-Constrained Spectral Sparsifier
    def test_spectral_sparsifier(self):
        nodes = ["N1", "N2", "N3", "N4"]
        edges = [
            ("N1", "N2", 1.0), ("N2", "N3", 1.0), ("N3", "N4", 1.0),
            ("N4", "N1", 1.0), ("N1", "N3", 1.0), ("N2", "N4", 1.0),
        ]
        sparsifier = SpectralGraphSparsifier(nodes, edges)
        res = sparsifier.sparsify(max_degree=2)

        self.assertLessEqual(res.max_observed_degree, 2)
        self.assertGreater(len(res.retained_edges), 0)

    # 8. Bipartite Ontology Alignment
    def test_bipartite_ontology_alignment(self):
        mentions = ["m_drug", "m_disease"]
        onto_nodes = [
            OntologyNode("O_DRUG", "Aspirin", "Drug"),
            OntologyNode("O_DISEASE", "Headache", "Disease"),
        ]
        affinities = {
            ("m_drug", "O_DRUG"): 0.95,
            ("m_drug", "O_DISEASE"): 0.10,
            ("m_disease", "O_DISEASE"): 0.98,
            ("m_disease", "O_DRUG"): 0.05,
        }
        aligner = BipartiteOntologyAligner(mentions, onto_nodes)
        res = aligner.solve(affinities)

        self.assertEqual(len(res.matched_pairs), 2)
        self.assertEqual(res.unmapped_entities_count, 0)
        matches = {p[0]: p[1] for p in res.matched_pairs}
        self.assertEqual(matches["m_drug"], "O_DRUG")
        self.assertEqual(matches["m_disease"], "O_DISEASE")

    # 9. Metric Dimension Landmarks
    def test_metric_dimension(self):
        # Line graph 1 - 2 - 3. End node 1 or 3 uniquely distinguishes all pairs.
        nodes = ["1", "2", "3"]
        edges = [("1", "2"), ("2", "3")]
        finder = MetricDimensionLandmarkFinder(nodes, edges)
        res = finder.solve()

        self.assertEqual(res.metric_dimension_k, 1)
        self.assertEqual(res.uniquely_resolved_percentage, 100.0)

    # 10. k-Degree Anonymity
    def test_graph_anonymizer(self):
        nodes = ["A", "B", "C", "D"]
        # A: 2, B: 2, C: 1, D: 1. Already 2-anonymous!
        edges = [("A", "B"), ("A", "C"), ("B", "D")]
        anonymizer = KDegreeGraphAnonymizer(nodes, edges)
        res = anonymizer.anonymize(k=2)

        self.assertEqual(res.k_anonymity_degree, 2)
        self.assertLessEqual(res.graph_distortion_ratio, 0.5)

if __name__ == "__main__":
    unittest.main()
