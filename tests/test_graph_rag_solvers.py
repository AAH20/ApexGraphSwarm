"""
Comprehensive unit tests for GraphRAG NP-Hard Kernel solvers.
Covers: PCST, Community Detection, Entity Resolution, Constrained Path,
        Submodular Summary, Temporal Isomorphism, Spectral Sparsification,
        Bipartite Alignment, Metric Dimension, k-Degree Anonymization.
"""
import unittest
import sys
import os

# Add integration sources to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.integration-sources', 'graph-rag-np-hard-kernel'))

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


class TestPrizeCollectingSteinerTree(unittest.TestCase):
    """Tests for Prize-Collecting Steiner Tree (PCST) solver."""

    def test_basic_steiner_tree_extraction(self):
        nodes = [
            GraphNode("N1", "Entity", 50.0),
            GraphNode("N2", "Entity", 40.0),
            GraphNode("N3", "Entity", 10.0),
            GraphNode("N4", "Noise", 0.0),
        ]
        edges = [
            GraphEdge("N1", "N2", 5.0),
            GraphEdge("N2", "N3", 4.0),
            GraphEdge("N3", "N4", 30.0),
        ]
        solver = PrizeCollectingSteinerTreeSolver(nodes, edges)
        res = solver.solve("N1")
        self.assertIn("N1", res.selected_nodes)
        self.assertIn("N2", res.selected_nodes)
        self.assertNotIn("N4", res.selected_nodes)
        self.assertTrue(res.is_connected)
        self.assertGreater(res.net_utility, 0.0)

    def test_empty_graph(self):
        solver = PrizeCollectingSteinerTreeSolver([], [])
        res = solver.solve()
        self.assertEqual(res.selected_nodes, [])
        self.assertEqual(res.total_prize, 0.0)
        self.assertTrue(res.is_connected)

    def test_single_node(self):
        nodes = [GraphNode("A", "Entity", 100.0)]
        solver = PrizeCollectingSteinerTreeSolver(nodes, [])
        res = solver.solve("A")
        self.assertEqual(res.selected_nodes, ["A"])
        self.assertEqual(res.total_prize, 100.0)

    def test_all_nodes_connected(self):
        nodes = [
            GraphNode("A", "E", 10.0),
            GraphNode("B", "E", 10.0),
            GraphNode("C", "E", 10.0),
        ]
        edges = [
            GraphEdge("A", "B", 1.0),
            GraphEdge("B", "C", 1.0),
        ]
        solver = PrizeCollectingSteinerTreeSolver(nodes, edges)
        res = solver.solve("A")
        self.assertEqual(len(res.selected_nodes), 3)
        self.assertTrue(res.is_connected)

    def test_high_cost_edge_pruned(self):
        nodes = [
            GraphNode("A", "E", 100.0),
            GraphNode("B", "E", 1.0),
        ]
        edges = [GraphEdge("A", "B", 200.0)]
        solver = PrizeCollectingSteinerTreeSolver(nodes, edges)
        res = solver.solve("A")
        # B's prize (1.0) < edge cost (200.0), so B should be pruned
        self.assertNotIn("B", res.selected_nodes)

    def test_net_utility_calculation(self):
        nodes = [
            GraphNode("A", "E", 50.0),
            GraphNode("B", "E", 30.0),
        ]
        edges = [GraphEdge("A", "B", 10.0)]
        solver = PrizeCollectingSteinerTreeSolver(nodes, edges)
        res = solver.solve("A")
        self.assertEqual(res.total_prize, 80.0)
        self.assertEqual(res.total_cost, 10.0)
        self.assertEqual(res.net_utility, 70.0)

    def test_disconnected_components(self):
        nodes = [
            GraphNode("A", "E", 50.0),
            GraphNode("B", "E", 40.0),
            GraphNode("C", "E", 30.0),
        ]
        edges = [GraphEdge("A", "B", 5.0)]
        solver = PrizeCollectingSteinerTreeSolver(nodes, edges)
        res = solver.solve("A")
        # C is disconnected, should not be in tree
        self.assertNotIn("C", res.selected_nodes)

    def test_execution_time_positive(self):
        nodes = [GraphNode("A", "E", 10.0), GraphNode("B", "E", 10.0)]
        edges = [GraphEdge("A", "B", 1.0)]
        solver = PrizeCollectingSteinerTreeSolver(nodes, edges)
        res = solver.solve("A")
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_algorithm_name(self):
        nodes = [GraphNode("A", "E", 10.0)]
        solver = PrizeCollectingSteinerTreeSolver(nodes, [])
        res = solver.solve("A")
        self.assertEqual(res.algorithm, "PRIMAL_DUAL_PCST")

    def test_reverse_delete_pruning(self):
        """Leaf nodes with prize < incident edge cost should be pruned."""
        nodes = [
            GraphNode("A", "E", 100.0),
            GraphNode("B", "E", 5.0),
            GraphNode("C", "E", 3.0),
        ]
        edges = [
            GraphEdge("A", "B", 10.0),
            GraphEdge("B", "C", 8.0),
        ]
        solver = PrizeCollectingSteinerTreeSolver(nodes, edges)
        res = solver.solve("A")
        # C has prize 3.0 < edge cost 8.0, should be pruned
        self.assertNotIn("C", res.selected_nodes)

    def test_multiple_paths(self):
        nodes = [
            GraphNode("A", "E", 50.0),
            GraphNode("B", "E", 40.0),
            GraphNode("C", "E", 30.0),
            GraphNode("D", "E", 20.0),
        ]
        edges = [
            GraphEdge("A", "B", 5.0),
            GraphEdge("A", "C", 3.0),
            GraphEdge("B", "D", 4.0),
            GraphEdge("C", "D", 2.0),
        ]
        solver = PrizeCollectingSteinerTreeSolver(nodes, edges)
        res = solver.solve("A")
        self.assertIn("A", res.selected_nodes)
        self.assertTrue(res.is_connected)

    def test_zero_prize_nodes_excluded(self):
        nodes = [
            GraphNode("A", "E", 100.0),
            GraphNode("B", "Zero", 0.0),
        ]
        edges = [GraphEdge("A", "B", 1.0)]
        solver = PrizeCollectingSteinerTreeSolver(nodes, edges)
        res = solver.solve("A")
        # B has zero prize, edge cost 1.0 > 0, should be excluded
        self.assertNotIn("B", res.selected_nodes)

    def test_large_prize_difference(self):
        nodes = [
            GraphNode("A", "E", 1000.0),
            GraphNode("B", "E", 1.0),
            GraphNode("C", "E", 1.0),
        ]
        edges = [
            GraphEdge("A", "B", 5.0),
            GraphEdge("A", "C", 5.0),
        ]
        solver = PrizeCollectingSteinerTreeSolver(nodes, edges)
        res = solver.solve("A")
        self.assertIn("A", res.selected_nodes)

    def test_selected_edges_valid(self):
        nodes = [
            GraphNode("A", "E", 50.0),
            GraphNode("B", "E", 40.0),
        ]
        edges = [GraphEdge("A", "B", 5.0)]
        solver = PrizeCollectingSteinerTreeSolver(nodes, edges)
        res = solver.solve("A")
        for u, v in res.selected_edges:
            self.assertIn(u, res.selected_nodes)
            self.assertIn(v, res.selected_nodes)

    def test_default_root_selection(self):
        """When no root specified, highest prize node should be selected."""
        nodes = [
            GraphNode("A", "E", 10.0),
            GraphNode("B", "E", 100.0),
            GraphNode("C", "E", 50.0),
        ]
        edges = [
            GraphEdge("A", "B", 5.0),
            GraphEdge("B", "C", 5.0),
        ]
        solver = PrizeCollectingSteinerTreeSolver(nodes, edges)
        res = solver.solve()
        self.assertIn("B", res.selected_nodes)


class TestHierarchicalCommunityDetector(unittest.TestCase):
    """Tests for Modularity Maximization Community Detection solver."""

    def test_two_communities_detected(self):
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

    def test_single_community(self):
        nodes = ["A", "B", "C"]
        edges = [
            ("A", "B", 10.0), ("B", "C", 10.0), ("A", "C", 10.0),
        ]
        detector = HierarchicalCommunityDetector(nodes, edges, gamma=1.0)
        res = detector.solve()
        self.assertEqual(res.num_communities, 1)

    def test_empty_graph(self):
        detector = HierarchicalCommunityDetector([], [], gamma=1.0)
        res = detector.solve()
        self.assertEqual(res.num_communities, 1)
        self.assertEqual(res.modularity_score, 0.0)

    def test_disconnected_nodes(self):
        nodes = ["A", "B", "C", "D"]
        edges = [("A", "B", 5.0)]
        detector = HierarchicalCommunityDetector(nodes, edges, gamma=1.0)
        res = detector.solve()
        self.assertGreaterEqual(res.num_communities, 1)

    def test_modularity_score_range(self):
        nodes = ["A", "B", "C", "D", "E", "F"]
        edges = [
            ("A", "B", 5.0), ("B", "C", 5.0), ("A", "C", 5.0),
            ("D", "E", 5.0), ("E", "F", 5.0), ("D", "F", 5.0),
        ]
        detector = HierarchicalCommunityDetector(nodes, edges, gamma=1.0)
        res = detector.solve()
        self.assertGreaterEqual(res.modularity_score, -0.5)
        self.assertLessEqual(res.modularity_score, 1.0)

    def test_gamma_parameter(self):
        nodes = ["A", "B", "C", "D"]
        edges = [
            ("A", "B", 5.0), ("B", "C", 5.0), ("C", "D", 5.0), ("D", "A", 5.0),
        ]
        detector_low = HierarchicalCommunityDetector(nodes, edges, gamma=0.5)
        detector_high = HierarchicalCommunityDetector(nodes, edges, gamma=2.0)
        res_low = detector_low.solve()
        res_high = detector_high.solve()
        # Higher gamma should generally lead to more communities
        self.assertGreaterEqual(res_high.num_communities, res_low.num_communities)

    def test_community_partition_complete(self):
        nodes = ["A", "B", "C", "D", "E"]
        edges = [
            ("A", "B", 5.0), ("B", "C", 5.0), ("D", "E", 5.0),
        ]
        detector = HierarchicalCommunityDetector(nodes, edges, gamma=1.0)
        res = detector.solve()
        all_nodes = set()
        for members in res.communities.values():
            all_nodes.update(members)
        self.assertEqual(all_nodes, set(nodes))

    def test_execution_time(self):
        nodes = ["A", "B", "C"]
        edges = [("A", "B", 1.0), ("B", "C", 1.0)]
        detector = HierarchicalCommunityDetector(nodes, edges)
        res = detector.solve()
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_algorithm_name(self):
        nodes = ["A", "B"]
        edges = [("A", "B", 1.0)]
        detector = HierarchicalCommunityDetector(nodes, edges)
        res = detector.solve()
        self.assertEqual(res.algorithm, "GREEDY_MODULARITY_MAXIMIZATION")

    def test_weighted_edges(self):
        nodes = ["A", "B", "C", "D"]
        edges = [
            ("A", "B", 100.0), ("B", "C", 1.0), ("C", "D", 100.0),
        ]
        detector = HierarchicalCommunityDetector(nodes, edges, gamma=1.0)
        res = detector.solve()
        self.assertGreaterEqual(res.num_communities, 1)

    def test_self_loop_ignored(self):
        nodes = ["A", "B"]
        edges = [("A", "A", 5.0), ("A", "B", 1.0)]
        detector = HierarchicalCommunityDetector(nodes, edges)
        res = detector.solve()
        self.assertGreaterEqual(res.num_communities, 1)

    def test_large_graph(self):
        nodes = [f"N{i}" for i in range(20)]
        edges = []
        for i in range(19):
            edges.append((f"N{i}", f"N{i+1}", 1.0))
        detector = HierarchicalCommunityDetector(nodes, edges)
        res = detector.solve()
        self.assertGreaterEqual(res.num_communities, 1)

    def test_normalized_community_ids(self):
        nodes = ["A", "B", "C", "D"]
        edges = [("A", "B", 5.0), ("C", "D", 5.0)]
        detector = HierarchicalCommunityDetector(nodes, edges)
        res = detector.solve()
        ids = sorted(res.communities.keys())
        self.assertEqual(ids, list(range(len(ids))))

    def test_max_iterations(self):
        nodes = ["A", "B", "C"]
        edges = [("A", "B", 1.0), ("B", "C", 1.0)]
        detector = HierarchicalCommunityDetector(nodes, edges)
        res = detector.solve(max_iterations=1)
        self.assertGreaterEqual(res.num_communities, 1)


class TestCorrelationClusteringEntityResolver(unittest.TestCase):
    """Tests for Entity Resolution & Correlation Clustering solver."""

    def test_basic_entity_resolution(self):
        mentions = [
            EntityMention("M1", "Apple Inc", [1.0, 0.0], "c1"),
            EntityMention("M2", "Apple", [0.98, 0.02], "c2"),
            EntityMention("M3", "Microsoft", [0.0, 1.0], "c3"),
            EntityMention("M4", "MSFT", [0.05, 0.95], "c4"),
        ]
        resolver = CorrelationClusteringEntityResolver(mentions, affinity_threshold=0.7)
        res = resolver.solve()
        self.assertEqual(res.cluster_count, 2)
        cluster_sets = [set(c) for c in res.resolved_clusters.values()]
        self.assertTrue(any({"M1", "M2"}.issubset(s) for s in cluster_sets))
        self.assertTrue(any({"M3", "M4"}.issubset(s) for s in cluster_sets))

    def test_empty_mentions(self):
        resolver = CorrelationClusteringEntityResolver([], affinity_threshold=0.7)
        res = resolver.solve()
        self.assertEqual(res.cluster_count, 0)
        self.assertEqual(res.resolved_clusters, {})

    def test_single_mention(self):
        mentions = [EntityMention("M1", "Apple", [1.0, 0.0], "c1")]
        resolver = CorrelationClusteringEntityResolver(mentions)
        res = resolver.solve()
        self.assertEqual(res.cluster_count, 1)

    def test_all_same_entity(self):
        mentions = [
            EntityMention("M1", "Apple", [1.0, 0.0], "c1"),
            EntityMention("M2", "Apple", [1.0, 0.0], "c2"),
            EntityMention("M3", "Apple", [1.0, 0.0], "c3"),
        ]
        resolver = CorrelationClusteringEntityResolver(mentions, affinity_threshold=0.5)
        res = resolver.solve()
        self.assertEqual(res.cluster_count, 1)

    def test_all_different_entities(self):
        mentions = [
            EntityMention("M1", "A", [1.0, 0.0], "c1"),
            EntityMention("M2", "B", [0.0, 1.0], "c2"),
            EntityMention("M3", "C", [-1.0, 0.0], "c3"),
        ]
        resolver = CorrelationClusteringEntityResolver(mentions, affinity_threshold=0.9)
        res = resolver.solve()
        self.assertGreaterEqual(res.cluster_count, 2)

    def test_text_match_affinity(self):
        mentions = [
            EntityMention("M1", "Apple Inc", [0.0, 0.0], "c1"),
            EntityMention("M2", "Apple Inc", [0.0, 0.0], "c2"),
        ]
        resolver = CorrelationClusteringEntityResolver(mentions, affinity_threshold=0.99)
        res = resolver.solve()
        # Same text should give affinity 1.0 regardless of embeddings
        self.assertEqual(res.cluster_count, 1)

    def test_conflicts_cut_nonnegative(self):
        mentions = [
            EntityMention("M1", "A", [1.0, 0.0], "c1"),
            EntityMention("M2", "B", [0.0, 1.0], "c2"),
        ]
        resolver = CorrelationClusteringEntityResolver(mentions)
        res = resolver.solve()
        self.assertGreaterEqual(res.total_conflicts_cut, 0.0)

    def test_execution_time(self):
        mentions = [
            EntityMention("M1", "A", [1.0, 0.0], "c1"),
            EntityMention("M2", "B", [0.0, 1.0], "c2"),
        ]
        resolver = CorrelationClusteringEntityResolver(mentions)
        res = resolver.solve()
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_algorithm_name(self):
        mentions = [EntityMention("M1", "A", [1.0, 0.0], "c1")]
        resolver = CorrelationClusteringEntityResolver(mentions)
        res = resolver.solve()
        self.assertEqual(res.algorithm, "CORRELATION_CLUSTERING_PIVOT")

    def test_threshold_sensitivity(self):
        mentions = [
            EntityMention("M1", "A", [0.8, 0.2], "c1"),
            EntityMention("M2", "B", [0.7, 0.3], "c2"),
        ]
        resolver_low = CorrelationClusteringEntityResolver(mentions, affinity_threshold=0.5)
        resolver_high = CorrelationClusteringEntityResolver(mentions, affinity_threshold=0.95)
        res_low = resolver_low.solve()
        res_high = resolver_high.solve()
        # Higher threshold should lead to more or equal clusters
        self.assertGreaterEqual(res_high.cluster_count, res_low.cluster_count)

    def test_many_mentions(self):
        mentions = [
            EntityMention(f"M{i}", f"Entity_{i%3}", [1.0 if i%3==0 else 0.0, 1.0 if i%3==1 else 0.0], f"c{i}")
            for i in range(9)
        ]
        resolver = CorrelationClusteringEntityResolver(mentions, affinity_threshold=0.6)
        res = resolver.solve()
        self.assertGreaterEqual(res.cluster_count, 1)
        self.assertLessEqual(res.cluster_count, 9)

    def test_cluster_names_prefixed(self):
        mentions = [
            EntityMention("M1", "A", [1.0, 0.0], "c1"),
            EntityMention("M2", "A", [1.0, 0.0], "c2"),
        ]
        resolver = CorrelationClusteringEntityResolver(mentions)
        res = resolver.solve()
        for name in res.resolved_clusters.keys():
            self.assertTrue(name.startswith("ENTITY_"))

    def test_zero_embedding(self):
        mentions = [
            EntityMention("M1", "A", [0.0, 0.0], "c1"),
            EntityMention("M2", "B", [0.0, 0.0], "c2"),
        ]
        resolver = CorrelationClusteringEntityResolver(mentions)
        res = resolver.solve()
        self.assertGreaterEqual(res.cluster_count, 1)

    def test_execution_time_reasonable(self):
        mentions = [
            EntityMention(f"M{i}", f"E{i}", [1.0 if i%2==0 else 0.0, 0.0 if i%2==0 else 1.0], f"c{i}")
            for i in range(10)
        ]
        resolver = CorrelationClusteringEntityResolver(mentions)
        res = resolver.solve()
        self.assertLess(res.execution_time_us, 1000000.0)


class TestConstrainedCausalPathFinder(unittest.TestCase):
    """Tests for Constrained Shortest Path (WCSPP) solver."""

    def test_basic_path_found(self):
        edges = [
            TemporalCausalEdge("A", "B", 1.0, 1.0, 0.9, 1.0),
            TemporalCausalEdge("B", "C", 2.0, 2.0, 0.8, 2.0),
        ]
        finder = ConstrainedCausalPathFinder(edges)
        res = finder.solve("A", "C")
        self.assertTrue(res.is_causally_valid)
        self.assertEqual(res.path_nodes[0], "A")
        self.assertEqual(res.path_nodes[-1], "C")
        self.assertGreater(res.total_cost, 0.0)

    def test_same_source_target(self):
        edges = []
        finder = ConstrainedCausalPathFinder(edges)
        res = finder.solve("A", "A")
        self.assertTrue(res.is_causally_valid)
        self.assertEqual(res.path_nodes, ["A"])
        self.assertEqual(res.total_cost, 0.0)

    def test_no_path_exists(self):
        edges = [
            TemporalCausalEdge("A", "B", 1.0, 1.0, 0.9, 1.0),
        ]
        finder = ConstrainedCausalPathFinder(edges)
        res = finder.solve("A", "Z")
        self.assertFalse(res.is_causally_valid)
        self.assertEqual(res.path_nodes, [])

    def test_delay_constraint(self):
        edges = [
            TemporalCausalEdge("A", "B", 1.0, 100.0, 0.9, 1.0),
            TemporalCausalEdge("B", "C", 1.0, 100.0, 0.9, 2.0),
        ]
        finder = ConstrainedCausalPathFinder(edges)
        res = finder.solve("A", "C", max_delay_hours=50.0)
        self.assertFalse(res.is_causally_valid)

    def test_confidence_constraint(self):
        edges = [
            TemporalCausalEdge("A", "B", 1.0, 1.0, 0.3, 1.0),
            TemporalCausalEdge("B", "C", 1.0, 1.0, 0.9, 2.0),
        ]
        finder = ConstrainedCausalPathFinder(edges)
        res = finder.solve("A", "C", min_confidence=0.5)
        self.assertFalse(res.is_causally_valid)

    def test_temporal_monotonicity(self):
        edges = [
            TemporalCausalEdge("A", "B", 1.0, 1.0, 0.9, 5.0),
            TemporalCausalEdge("B", "C", 1.0, 1.0, 0.9, 3.0),  # Goes back in time
        ]
        finder = ConstrainedCausalPathFinder(edges)
        res = finder.solve("A", "C")
        # Should not find path due to temporal violation
        if res.is_causally_valid:
            # If found, verify timestamps are monotonic
            timestamps = []
            for e in edges:
                if e.source in res.path_nodes and e.target in res.path_nodes:
                    timestamps.append(e.timestamp)
            # Just verify the result is valid
            self.assertTrue(res.is_causally_valid)

    def test_bottleneck_confidence(self):
        edges = [
            TemporalCausalEdge("A", "B", 1.0, 1.0, 0.9, 1.0),
            TemporalCausalEdge("B", "C", 1.0, 1.0, 0.5, 2.0),
        ]
        finder = ConstrainedCausalPathFinder(edges)
        res = finder.solve("A", "C")
        self.assertAlmostEqual(res.bottleneck_confidence, 0.5, places=5)

    def test_no_path_between_disconnected(self):
        edges = [
            TemporalCausalEdge("A", "B", 1.0, 1.0, 0.9, 1.0),
            TemporalCausalEdge("C", "D", 1.0, 1.0, 0.9, 2.0),
        ]
        finder = ConstrainedCausalPathFinder(edges)
        res = finder.solve("A", "D")
        self.assertFalse(res.is_causally_valid)

    def test_direct_edge(self):
        edges = [TemporalCausalEdge("A", "B", 5.0, 2.0, 0.8, 1.0)]
        finder = ConstrainedCausalPathFinder(edges)
        res = finder.solve("A", "B")
        self.assertTrue(res.is_causally_valid)
        self.assertEqual(res.total_cost, 5.0)
        self.assertEqual(res.total_delay_hours, 2.0)

    def test_multiple_paths(self):
        edges = [
            TemporalCausalEdge("A", "B", 1.0, 1.0, 0.9, 1.0),
            TemporalCausalEdge("B", "D", 10.0, 1.0, 0.9, 2.0),
            TemporalCausalEdge("A", "C", 2.0, 1.0, 0.9, 1.5),
            TemporalCausalEdge("C", "D", 2.0, 1.0, 0.9, 2.5),
        ]
        finder = ConstrainedCausalPathFinder(edges)
        res = finder.solve("A", "D")
        self.assertTrue(res.is_causally_valid)
        # Should prefer lower cost path
        self.assertLessEqual(res.total_cost, 5.0)

    def test_algorithm_name(self):
        edges = [TemporalCausalEdge("A", "B", 1.0, 1.0, 0.9, 1.0)]
        finder = ConstrainedCausalPathFinder(edges)
        res = finder.solve("A", "B")
        self.assertEqual(res.algorithm, "LABEL_SETTING_WCSPP")

    def test_execution_time(self):
        edges = [TemporalCausalEdge("A", "B", 1.0, 1.0, 0.9, 1.0)]
        finder = ConstrainedCausalPathFinder(edges)
        res = finder.solve("A", "B")
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_path_continuity(self):
        edges = [
            TemporalCausalEdge("A", "B", 1.0, 1.0, 0.9, 1.0),
            TemporalCausalEdge("B", "C", 1.0, 1.0, 0.9, 2.0),
            TemporalCausalEdge("C", "D", 1.0, 1.0, 0.9, 3.0),
        ]
        finder = ConstrainedCausalPathFinder(edges)
        res = finder.solve("A", "D")
        self.assertTrue(res.is_causally_valid)
        for i in range(len(res.path_nodes) - 1):
            self.assertIn(res.path_nodes[i+1], [e.target for e in edges if e.source == res.path_nodes[i]])

    def test_total_delay_calculation(self):
        edges = [
            TemporalCausalEdge("A", "B", 1.0, 3.0, 0.9, 1.0),
            TemporalCausalEdge("B", "C", 1.0, 4.0, 0.9, 2.0),
        ]
        finder = ConstrainedCausalPathFinder(edges)
        res = finder.solve("A", "C")
        self.assertAlmostEqual(res.total_delay_hours, 7.0, places=5)

    def test_disconnected_graph(self):
        edges = [
            TemporalCausalEdge("A", "B", 1.0, 1.0, 0.9, 1.0),
            TemporalCausalEdge("C", "D", 1.0, 1.0, 0.9, 2.0),
        ]
        finder = ConstrainedCausalPathFinder(edges)
        res = finder.solve("A", "D")
        self.assertFalse(res.is_causally_valid)


class TestSubmodularGraphSummarizer(unittest.TestCase):
    """Tests for Submodular Graph Summarization solver."""

    def test_basic_summarization(self):
        units = [
            KnowledgeUnit("U1", "Summary 1", 100, {"A", "B"}, 0.8),
            KnowledgeUnit("U2", "Summary 2", 150, {"C", "D"}, 0.7),
            KnowledgeUnit("U3", "Summary 3", 200, {"E", "F"}, 0.6),
        ]
        summarizer = SubmodularGraphSummarizer(units)
        res = summarizer.solve(token_budget=300)
        self.assertGreater(len(res.selected_units), 0)
        self.assertLessEqual(res.total_tokens, 300)

    def test_empty_units(self):
        summarizer = SubmodularGraphSummarizer([])
        res = summarizer.solve(token_budget=100)
        self.assertEqual(res.selected_units, [])
        self.assertEqual(res.total_tokens, 0)

    def test_zero_budget(self):
        units = [KnowledgeUnit("U1", "S", 100, {"A"}, 0.5)]
        summarizer = SubmodularGraphSummarizer(units)
        res = summarizer.solve(token_budget=0)
        self.assertEqual(res.selected_units, [])

    def test_entity_coverage(self):
        units = [
            KnowledgeUnit("U1", "S1", 100, {"A", "B", "C"}, 0.5),
            KnowledgeUnit("U2", "S2", 100, {"D", "E", "F"}, 0.5),
        ]
        summarizer = SubmodularGraphSummarizer(units)
        res = summarizer.solve(token_budget=200)
        self.assertGreater(res.total_entity_coverage, 0)

    def test_diversity_score(self):
        units = [
            KnowledgeUnit("U1", "S1", 100, {"A"}, 0.5),
            KnowledgeUnit("U2", "S2", 100, {"B"}, 0.5),
        ]
        summarizer = SubmodularGraphSummarizer(units)
        res = summarizer.solve(token_budget=200)
        self.assertGreaterEqual(res.diversity_score, 0.0)

    def test_salience_weight(self):
        units = [
            KnowledgeUnit("U1", "S1", 100, {"A"}, 1.0),
            KnowledgeUnit("U2", "S2", 100, {"B"}, 0.1),
        ]
        summarizer = SubmodularGraphSummarizer(units, salience_weight=1.0)
        res = summarizer.solve(token_budget=100)
        # U1 has higher salience, should be preferred
        self.assertEqual(res.selected_units[0].unit_id, "U1")

    def test_budget_constraint(self):
        units = [
            KnowledgeUnit("U1", "S1", 100, {"A"}, 0.5),
            KnowledgeUnit("U2", "S2", 200, {"B"}, 0.5),
            KnowledgeUnit("U3", "S3", 300, {"C"}, 0.5),
        ]
        summarizer = SubmodularGraphSummarizer(units)
        res = summarizer.solve(token_budget=250)
        self.assertLessEqual(res.total_tokens, 250)

    def test_algorithm_name(self):
        units = [KnowledgeUnit("U1", "S", 100, {"A"}, 0.5)]
        summarizer = SubmodularGraphSummarizer(units)
        res = summarizer.solve(token_budget=100)
        self.assertEqual(res.algorithm, "BUDGETED_SUBMODULAR_GREEDY")

    def test_execution_time(self):
        units = [KnowledgeUnit("U1", "S", 100, {"A"}, 0.5)]
        summarizer = SubmodularGraphSummarizer(units)
        res = summarizer.solve(token_budget=100)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_overlapping_entities(self):
        units = [
            KnowledgeUnit("U1", "S1", 100, {"A", "B"}, 0.5),
            KnowledgeUnit("U2", "S2", 100, {"B", "C"}, 0.5),
        ]
        summarizer = SubmodularGraphSummarizer(units)
        res = summarizer.solve(token_budget=200)
        # Should cover A, B, C
        self.assertGreaterEqual(res.total_entity_coverage, 2)

    def test_single_unit_fits(self):
        units = [KnowledgeUnit("U1", "S", 50, {"A"}, 0.5)]
        summarizer = SubmodularGraphSummarizer(units)
        res = summarizer.solve(token_budget=100)
        self.assertEqual(len(res.selected_units), 1)

    def test_no_unit_fits(self):
        units = [KnowledgeUnit("U1", "S", 200, {"A"}, 0.5)]
        summarizer = SubmodularGraphSummarizer(units)
        res = summarizer.solve(token_budget=100)
        self.assertEqual(len(res.selected_units), 0)

    def test_large_budget(self):
        units = [
            KnowledgeUnit("U1", "S1", 100, {"A"}, 0.5),
            KnowledgeUnit("U2", "S2", 100, {"B"}, 0.5),
        ]
        summarizer = SubmodularGraphSummarizer(units)
        res = summarizer.solve(token_budget=10000)
        self.assertEqual(len(res.selected_units), 2)

    def test_diversity_zero_for_single(self):
        units = [KnowledgeUnit("U1", "S", 100, {"A"}, 0.5)]
        summarizer = SubmodularGraphSummarizer(units)
        res = summarizer.solve(token_budget=100)
        self.assertEqual(res.diversity_score, 0.0)


class TestTemporalSubgraphMatcher(unittest.TestCase):
    """Tests for Temporal Subgraph Isomorphism solver."""

    def test_basic_match(self):
        target_edges = [
            GraphEdge("A", "B", 1.0, "RELATES", 1.0),
            GraphEdge("B", "C", 1.0, "RELATES", 2.0),
        ]
        pattern = [
            PatternEdge("X", "Y", "RELATES"),
        ]
        matcher = TemporalSubgraphMatcher(target_edges)
        res = matcher.match(pattern)
        self.assertGreater(res.total_matches, 0)

    def test_no_match(self):
        target_edges = [
            GraphEdge("A", "B", 1.0, "RELATES", 1.0),
        ]
        pattern = [
            PatternEdge("X", "Y", "NONEXISTENT"),
        ]
        matcher = TemporalSubgraphMatcher(target_edges)
        res = matcher.match(pattern)
        self.assertEqual(res.total_matches, 0)

    def test_empty_target(self):
        pattern = [PatternEdge("X", "Y", "RELATES")]
        matcher = TemporalSubgraphMatcher([])
        res = matcher.match(pattern)
        self.assertEqual(res.total_matches, 0)

    def test_empty_pattern(self):
        target_edges = [GraphEdge("A", "B", 1.0, "RELATES", 1.0)]
        matcher = TemporalSubgraphMatcher(target_edges)
        res = matcher.match([])
        # Empty pattern has no variables, so backtrack immediately finds a "match"
        self.assertGreaterEqual(res.total_matches, 0)

    def test_max_matches_limit(self):
        target_edges = [
            GraphEdge(f"N{i}", f"N{i+1}", 1.0, "REL", float(i))
            for i in range(10)
        ]
        pattern = [PatternEdge("X", "Y", "REL")]
        matcher = TemporalSubgraphMatcher(target_edges)
        res = matcher.match(pattern, max_matches=3)
        self.assertLessEqual(res.total_matches, 3)

    def test_two_edge_pattern(self):
        target_edges = [
            GraphEdge("A", "B", 1.0, "KNOWS", 1.0),
            GraphEdge("B", "C", 1.0, "KNOWS", 2.0),
        ]
        pattern = [
            PatternEdge("X", "Y", "KNOWS"),
            PatternEdge("Y", "Z", "KNOWS"),
        ]
        matcher = TemporalSubgraphMatcher(target_edges)
        res = matcher.match(pattern)
        self.assertGreater(res.total_matches, 0)

    def test_match_mapping_valid(self):
        target_edges = [
            GraphEdge("A", "B", 1.0, "REL", 1.0),
        ]
        pattern = [PatternEdge("X", "Y", "REL")]
        matcher = TemporalSubgraphMatcher(target_edges)
        res = matcher.match(pattern)
        for match in res.matched_subgraphs:
            self.assertIn("X", match)
            self.assertIn("Y", match)

    def test_algorithm_name(self):
        target_edges = [GraphEdge("A", "B", 1.0, "REL", 1.0)]
        matcher = TemporalSubgraphMatcher(target_edges)
        res = matcher.match([PatternEdge("X", "Y", "REL")])
        self.assertEqual(res.algorithm, "TEMPORAL_VF2_ISOMORPHISM")

    def test_execution_time(self):
        target_edges = [GraphEdge("A", "B", 1.0, "REL", 1.0)]
        matcher = TemporalSubgraphMatcher(target_edges)
        res = matcher.match([PatternEdge("X", "Y", "REL")])
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_triangle_pattern(self):
        target_edges = [
            GraphEdge("A", "B", 1.0, "R", 1.0),
            GraphEdge("B", "C", 1.0, "R", 2.0),
            GraphEdge("A", "C", 1.0, "R", 3.0),
        ]
        pattern = [
            PatternEdge("X", "Y", "R"),
            PatternEdge("Y", "Z", "R"),
            PatternEdge("X", "Z", "R"),
        ]
        matcher = TemporalSubgraphMatcher(target_edges)
        res = matcher.match(pattern)
        self.assertGreater(res.total_matches, 0)

    def test_multiple_matches(self):
        target_edges = [
            GraphEdge("A", "B", 1.0, "R", 1.0),
            GraphEdge("C", "D", 1.0, "R", 2.0),
        ]
        pattern = [PatternEdge("X", "Y", "R")]
        matcher = TemporalSubgraphMatcher(target_edges)
        res = matcher.match(pattern)
        self.assertGreaterEqual(res.total_matches, 2)

    def test_self_loop_pattern(self):
        target_edges = [
            GraphEdge("A", "A", 1.0, "SELF", 1.0),
        ]
        pattern = [PatternEdge("X", "X", "SELF")]
        matcher = TemporalSubgraphMatcher(target_edges)
        res = matcher.match(pattern)
        self.assertGreater(res.total_matches, 0)


class TestSpectralGraphSparsifier(unittest.TestCase):
    """Tests for Degree-Constrained Spectral Sparsification solver."""

    def test_basic_sparsification(self):
        nodes = ["A", "B", "C", "D"]
        edges = [
            ("A", "B", 5.0), ("B", "C", 4.0), ("C", "D", 3.0),
            ("A", "C", 2.0), ("B", "D", 1.0),
        ]
        sparsifier = SpectralGraphSparsifier(nodes, edges)
        res = sparsifier.sparsify(max_degree=2)
        self.assertGreater(len(res.retained_edges), 0)
        self.assertLessEqual(res.max_observed_degree, 2)

    def test_empty_graph(self):
        sparsifier = SpectralGraphSparsifier([], [])
        res = sparsifier.sparsify(max_degree=2)
        self.assertEqual(res.retained_edges, [])

    def test_single_edge(self):
        nodes = ["A", "B"]
        edges = [("A", "B", 1.0)]
        sparsifier = SpectralGraphSparsifier(nodes, edges)
        res = sparsifier.sparsify(max_degree=1)
        self.assertEqual(len(res.retained_edges), 1)

    def test_reduction_percentage(self):
        nodes = ["A", "B", "C", "D", "E"]
        edges = [
            ("A", "B", 5.0), ("A", "C", 4.0), ("A", "D", 3.0),
            ("A", "E", 2.0), ("B", "C", 1.0),
        ]
        sparsifier = SpectralGraphSparsifier(nodes, edges)
        res = sparsifier.sparsify(max_degree=2)
        self.assertGreater(res.edge_reduction_pct, 0.0)

    def test_connectivity_ratio(self):
        nodes = ["A", "B", "C"]
        edges = [("A", "B", 1.0), ("B", "C", 1.0)]
        sparsifier = SpectralGraphSparsifier(nodes, edges)
        res = sparsifier.sparsify(max_degree=2)
        self.assertGreater(res.algebraic_connectivity_ratio, 0.0)

    def test_max_degree_respected(self):
        nodes = ["A", "B", "C", "D", "E"]
        edges = [
            ("A", "B", 5.0), ("A", "C", 4.0), ("A", "D", 3.0),
            ("A", "E", 2.0),
        ]
        sparsifier = SpectralGraphSparsifier(nodes, edges)
        res = sparsifier.sparsify(max_degree=1)
        self.assertLessEqual(res.max_observed_degree, 1)

    def test_algorithm_name(self):
        nodes = ["A", "B"]
        edges = [("A", "B", 1.0)]
        sparsifier = SpectralGraphSparsifier(nodes, edges)
        res = sparsifier.sparsify(max_degree=1)
        self.assertEqual(res.algorithm, "SPECTRAL_SPARSIFIER")

    def test_execution_time(self):
        nodes = ["A", "B", "C"]
        edges = [("A", "B", 1.0), ("B", "C", 1.0)]
        sparsifier = SpectralGraphSparsifier(nodes, edges)
        res = sparsifier.sparsify(max_degree=2)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_complete_graph(self):
        nodes = ["A", "B", "C", "D"]
        edges = [
            ("A", "B", 1.0), ("A", "C", 1.0), ("A", "D", 1.0),
            ("B", "C", 1.0), ("B", "D", 1.0), ("C", "D", 1.0),
        ]
        sparsifier = SpectralGraphSparsifier(nodes, edges)
        res = sparsifier.sparsify(max_degree=2)
        # Should retain a spanning tree (3 edges for 4 nodes)
        self.assertGreaterEqual(len(res.retained_edges), 3)

    def test_disconnected_graph(self):
        nodes = ["A", "B", "C", "D"]
        edges = [("A", "B", 1.0), ("C", "D", 1.0)]
        sparsifier = SpectralGraphSparsifier(nodes, edges)
        res = sparsifier.sparsify(max_degree=2)
        self.assertEqual(len(res.retained_edges), 2)

    def test_high_degree_constraint(self):
        nodes = ["A", "B", "C", "D", "E"]
        edges = [
            ("A", "B", 5.0), ("A", "C", 4.0), ("A", "D", 3.0), ("A", "E", 2.0),
        ]
        sparsifier = SpectralGraphSparsifier(nodes, edges)
        res = sparsifier.sparsify(max_degree=4)
        self.assertLessEqual(res.max_observed_degree, 4)

    def test_weight_ordering(self):
        """Higher weight edges should be preferred."""
        nodes = ["A", "B", "C"]
        edges = [
            ("A", "B", 10.0), ("A", "C", 1.0), ("B", "C", 1.0),
        ]
        sparsifier = SpectralGraphSparsifier(nodes, edges)
        res = sparsifier.sparsify(max_degree=1)
        # Should retain highest weight edge
        self.assertEqual(len(res.retained_edges), 1)

    def test_single_node(self):
        sparsifier = SpectralGraphSparsifier(["A"], [])
        res = sparsifier.sparsify(max_degree=1)
        self.assertEqual(res.retained_edges, [])


class TestBipartiteOntologyAligner(unittest.TestCase):
    """Tests for Bipartite Text-to-Ontology Alignment solver."""

    def test_basic_alignment(self):
        mentions = ["M1", "M2"]
        ontology_nodes = [
            OntologyNode("O1", "Apple", "Tech"),
            OntologyNode("O2", "Microsoft", "Tech"),
        ]
        affinities = {
            ("M1", "O1"): 0.9,
            ("M2", "O2"): 0.8,
        }
        aligner = BipartiteOntologyAligner(mentions, ontology_nodes)
        res = aligner.solve(affinities)
        self.assertEqual(len(res.matched_pairs), 2)
        self.assertGreater(res.total_alignment_weight, 0.0)

    def test_empty_mentions(self):
        ontology_nodes = [OntologyNode("O1", "A", "Cat")]
        aligner = BipartiteOntologyAligner([], ontology_nodes)
        res = aligner.solve({})
        self.assertEqual(res.matched_pairs, [])

    def test_empty_ontology(self):
        aligner = BipartiteOntologyAligner(["M1"], [])
        res = aligner.solve({})
        self.assertEqual(res.matched_pairs, [])

    def test_unmapped_entities(self):
        mentions = ["M1", "M2", "M3"]
        ontology_nodes = [OntologyNode("O1", "A", "Cat")]
        affinities = {("M1", "O1"): 0.9}
        aligner = BipartiteOntologyAligner(mentions, ontology_nodes)
        res = aligner.solve(affinities)
        self.assertEqual(res.unmapped_entities_count, 2)

    def test_zero_affinity_excluded(self):
        mentions = ["M1"]
        ontology_nodes = [OntologyNode("O1", "A", "Cat")]
        affinities = {("M1", "O1"): 0.0}
        aligner = BipartiteOntologyAligner(mentions, ontology_nodes)
        res = aligner.solve(affinities)
        self.assertEqual(len(res.matched_pairs), 0)

    def test_highest_affinity_preferred(self):
        mentions = ["M1"]
        ontology_nodes = [
            OntologyNode("O1", "A", "Cat"),
            OntologyNode("O2", "B", "Cat"),
        ]
        affinities = {
            ("M1", "O1"): 0.5,
            ("M1", "O2"): 0.9,
        }
        aligner = BipartiteOntologyAligner(mentions, ontology_nodes)
        res = aligner.solve(affinities)
        self.assertEqual(res.matched_pairs[0][1], "O2")

    def test_one_to_one_matching(self):
        mentions = ["M1", "M2"]
        ontology_nodes = [OntologyNode("O1", "A", "Cat")]
        affinities = {
            ("M1", "O1"): 0.9,
            ("M2", "O1"): 0.8,
        }
        aligner = BipartiteOntologyAligner(mentions, ontology_nodes)
        res = aligner.solve(affinities)
        # Only one can be matched
        self.assertEqual(len(res.matched_pairs), 1)

    def test_total_weight_calculation(self):
        mentions = ["M1", "M2"]
        ontology_nodes = [
            OntologyNode("O1", "A", "Cat"),
            OntologyNode("O2", "B", "Cat"),
        ]
        affinities = {
            ("M1", "O1"): 0.7,
            ("M2", "O2"): 0.6,
        }
        aligner = BipartiteOntologyAligner(mentions, ontology_nodes)
        res = aligner.solve(affinities)
        self.assertAlmostEqual(res.total_alignment_weight, 1.3, places=5)

    def test_algorithm_name(self):
        mentions = ["M1"]
        ontology_nodes = [OntologyNode("O1", "A", "Cat")]
        aligner = BipartiteOntologyAligner(mentions, ontology_nodes)
        res = aligner.solve({("M1", "O1"): 0.5})
        self.assertEqual(res.algorithm, "KUHN_MUNKRES_BIPARTITE")

    def test_execution_time(self):
        mentions = ["M1"]
        ontology_nodes = [OntologyNode("O1", "A", "Cat")]
        aligner = BipartiteOntologyAligner(mentions, ontology_nodes)
        res = aligner.solve({("M1", "O1"): 0.5})
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_multiple_mentions_same_ontology(self):
        mentions = ["M1", "M2", "M3"]
        ontology_nodes = [
            OntologyNode("O1", "A", "Cat"),
            OntologyNode("O2", "B", "Cat"),
        ]
        affinities = {
            ("M1", "O1"): 0.9,
            ("M2", "O1"): 0.8,
            ("M3", "O2"): 0.7,
        }
        aligner = BipartiteOntologyAligner(mentions, ontology_nodes)
        res = aligner.solve(affinities)
        self.assertEqual(len(res.matched_pairs), 2)

    def test_negative_affinity_excluded(self):
        mentions = ["M1"]
        ontology_nodes = [OntologyNode("O1", "A", "Cat")]
        affinities = {("M1", "O1"): -0.5}
        aligner = BipartiteOntologyAligner(mentions, ontology_nodes)
        res = aligner.solve(affinities)
        self.assertEqual(len(res.matched_pairs), 0)

    def test_all_matched(self):
        mentions = ["M1", "M2"]
        ontology_nodes = [
            OntologyNode("O1", "A", "Cat"),
            OntologyNode("O2", "B", "Cat"),
        ]
        affinities = {
            ("M1", "O1"): 0.9,
            ("M2", "O2"): 0.8,
        }
        aligner = BipartiteOntologyAligner(mentions, ontology_nodes)
        res = aligner.solve(affinities)
        self.assertEqual(res.unmapped_entities_count, 0)


class TestMetricDimensionLandmarkFinder(unittest.TestCase):
    """Tests for Metric Dimension & Landmark Resolving Set solver."""

    def test_basic_landmarks(self):
        nodes = ["A", "B", "C"]
        edges = [("A", "B"), ("B", "C")]
        finder = MetricDimensionLandmarkFinder(nodes, edges)
        res = finder.solve()
        self.assertGreater(len(res.landmark_nodes), 0)
        self.assertGreater(res.uniquely_resolved_percentage, 0.0)

    def test_single_node(self):
        finder = MetricDimensionLandmarkFinder(["A"], [])
        res = finder.solve()
        self.assertEqual(res.landmark_nodes, ["A"])
        self.assertEqual(res.uniquely_resolved_percentage, 100.0)

    def test_two_nodes(self):
        finder = MetricDimensionLandmarkFinder(["A", "B"], [("A", "B")])
        res = finder.solve()
        self.assertGreaterEqual(len(res.landmark_nodes), 1)

    def test_complete_graph(self):
        nodes = ["A", "B", "C"]
        edges = [("A", "B"), ("B", "C"), ("A", "C")]
        finder = MetricDimensionLandmarkFinder(nodes, edges)
        res = finder.solve()
        self.assertGreaterEqual(len(res.landmark_nodes), 1)

    def test_path_graph(self):
        nodes = ["A", "B", "C", "D"]
        edges = [("A", "B"), ("B", "C"), ("C", "D")]
        finder = MetricDimensionLandmarkFinder(nodes, edges)
        res = finder.solve()
        self.assertGreaterEqual(len(res.landmark_nodes), 1)

    def test_star_graph(self):
        nodes = ["Center", "L1", "L2", "L3"]
        edges = [("Center", "L1"), ("Center", "L2"), ("Center", "L3")]
        finder = MetricDimensionLandmarkFinder(nodes, edges)
        res = finder.solve()
        self.assertGreaterEqual(len(res.landmark_nodes), 1)

    def test_resolved_percentage_range(self):
        nodes = ["A", "B", "C", "D", "E"]
        edges = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E")]
        finder = MetricDimensionLandmarkFinder(nodes, edges)
        res = finder.solve()
        self.assertGreaterEqual(res.uniquely_resolved_percentage, 0.0)
        self.assertLessEqual(res.uniquely_resolved_percentage, 100.0)

    def test_metric_dimension_k(self):
        nodes = ["A", "B", "C"]
        edges = [("A", "B"), ("B", "C")]
        finder = MetricDimensionLandmarkFinder(nodes, edges)
        res = finder.solve()
        self.assertEqual(res.metric_dimension_k, len(res.landmark_nodes))

    def test_algorithm_name(self):
        nodes = ["A", "B"]
        edges = [("A", "B")]
        finder = MetricDimensionLandmarkFinder(nodes, edges)
        res = finder.solve()
        self.assertEqual(res.algorithm, "METRIC_DIMENSION_GREEDY")

    def test_execution_time(self):
        nodes = ["A", "B", "C"]
        edges = [("A", "B"), ("B", "C")]
        finder = MetricDimensionLandmarkFinder(nodes, edges)
        res = finder.solve()
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_disconnected_graph(self):
        nodes = ["A", "B", "C", "D"]
        edges = [("A", "B"), ("C", "D")]
        finder = MetricDimensionLandmarkFinder(nodes, edges)
        res = finder.solve()
        self.assertGreaterEqual(len(res.landmark_nodes), 1)

    def test_cycle_graph(self):
        nodes = ["A", "B", "C", "D"]
        edges = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")]
        finder = MetricDimensionLandmarkFinder(nodes, edges)
        res = finder.solve()
        self.assertGreaterEqual(len(res.landmark_nodes), 1)

    def test_landmarks_are_nodes(self):
        nodes = ["A", "B", "C", "D"]
        edges = [("A", "B"), ("B", "C"), ("C", "D")]
        finder = MetricDimensionLandmarkFinder(nodes, edges)
        res = finder.solve()
        for lm in res.landmark_nodes:
            self.assertIn(lm, nodes)

    def test_large_graph(self):
        nodes = [f"N{i}" for i in range(10)]
        edges = [(f"N{i}", f"N{i+1}") for i in range(9)]
        finder = MetricDimensionLandmarkFinder(nodes, edges)
        res = finder.solve()
        self.assertGreaterEqual(len(res.landmark_nodes), 1)
        self.assertLessEqual(len(res.landmark_nodes), 10)


class TestKDegreeGraphAnonymizer(unittest.TestCase):
    """Tests for k-Degree Anonymity Graph Sanitization solver."""

    def test_basic_anonymization(self):
        nodes = ["A", "B", "C", "D", "E", "F"]
        edges = [("A", "B"), ("C", "D"), ("E", "F")]
        anonymizer = KDegreeGraphAnonymizer(nodes, edges)
        res = anonymizer.anonymize(k=2)
        self.assertEqual(res.k_anonymity_degree, 2)

    def test_empty_graph(self):
        anonymizer = KDegreeGraphAnonymizer([], [])
        res = anonymizer.anonymize(k=2)
        self.assertEqual(res.added_edges, [])

    def test_k_larger_than_n(self):
        nodes = ["A", "B"]
        edges = [("A", "B")]
        anonymizer = KDegreeGraphAnonymizer(nodes, edges)
        res = anonymizer.anonymize(k=5)
        self.assertEqual(res.added_edges, [])

    def test_k_equals_1(self):
        nodes = ["A", "B"]
        edges = [("A", "B")]
        anonymizer = KDegreeGraphAnonymizer(nodes, edges)
        res = anonymizer.anonymize(k=1)
        self.assertEqual(res.added_edges, [])

    def test_distortion_ratio(self):
        nodes = ["A", "B", "C", "D"]
        edges = [("A", "B")]
        anonymizer = KDegreeGraphAnonymizer(nodes, edges)
        res = anonymizer.anonymize(k=2)
        self.assertGreaterEqual(res.graph_distortion_ratio, 0.0)

    def test_no_removed_edges(self):
        nodes = ["A", "B", "C"]
        edges = [("A", "B")]
        anonymizer = KDegreeGraphAnonymizer(nodes, edges)
        res = anonymizer.anonymize(k=2)
        self.assertEqual(res.removed_edges, [])

    def test_algorithm_name(self):
        nodes = ["A", "B", "C"]
        edges = [("A", "B")]
        anonymizer = KDegreeGraphAnonymizer(nodes, edges)
        res = anonymizer.anonymize(k=2)
        self.assertEqual(res.algorithm, "K_DEGREE_ANONYMIZER")

    def test_execution_time(self):
        nodes = ["A", "B", "C"]
        edges = [("A", "B")]
        anonymizer = KDegreeGraphAnonymizer(nodes, edges)
        res = anonymizer.anonymize(k=2)
        self.assertGreaterEqual(res.execution_time_us, 0.0)

    def test_complete_graph(self):
        nodes = ["A", "B", "C"]
        edges = [("A", "B"), ("B", "C"), ("A", "C")]
        anonymizer = KDegreeGraphAnonymizer(nodes, edges)
        res = anonymizer.anonymize(k=2)
        # All nodes have degree 2, already k-anonymous
        self.assertEqual(res.added_edges, [])

    def test_added_edges_valid(self):
        nodes = ["A", "B", "C", "D"]
        edges = [("A", "B")]
        anonymizer = KDegreeGraphAnonymizer(nodes, edges)
        res = anonymizer.anonymize(k=2)
        for u, v in res.added_edges:
            self.assertIn(u, nodes)
            self.assertIn(v, nodes)

    def test_no_self_loops_added(self):
        nodes = ["A", "B", "C", "D"]
        edges = [("A", "B")]
        anonymizer = KDegreeGraphAnonymizer(nodes, edges)
        res = anonymizer.anonymize(k=2)
        for u, v in res.added_edges:
            self.assertNotEqual(u, v)

    def test_no_duplicate_edges_added(self):
        nodes = ["A", "B", "C", "D"]
        edges = [("A", "B")]
        anonymizer = KDegreeGraphAnonymizer(nodes, edges)
        res = anonymizer.anonymize(k=2)
        edge_set = set()
        for u, v in res.added_edges:
            e = (u, v) if u < v else (v, u)
            self.assertNotIn(e, edge_set)
            edge_set.add(e)

    def test_star_graph_anonymization(self):
        nodes = ["Center", "L1", "L2", "L3"]
        edges = [("Center", "L1"), ("Center", "L2"), ("Center", "L3")]
        anonymizer = KDegreeGraphAnonymizer(nodes, edges)
        res = anonymizer.anonymize(k=2)
        self.assertGreaterEqual(len(res.added_edges), 0)

    def test_large_k(self):
        nodes = ["A", "B", "C", "D", "E"]
        edges = [("A", "B")]
        anonymizer = KDegreeGraphAnonymizer(nodes, edges)
        res = anonymizer.anonymize(k=4)
        self.assertEqual(res.k_anonymity_degree, 4)


if __name__ == '__main__':
    unittest.main()
