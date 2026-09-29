"""
Financial Fraud & Ultimate Beneficial Ownership (UBO) Hypergraph Adapter.
Demonstrates money laundering circular cycle detection, shell company coreference resolution,
and privacy-preserving GraphRAG querying for AML/CFT investigations.
"""
from typing import List, Dict, Any
from ..core.models import (
    GraphNode, GraphEdge, EntityMention, TemporalCausalEdge,
    KnowledgeUnit, PatternEdge, OntologyNode
)
from ..core.subgraph_extraction import PrizeCollectingSteinerTreeSolver
from ..core.community_detection import HierarchicalCommunityDetector
from ..core.entity_resolution import CorrelationClusteringEntityResolver
from ..core.constrained_path import ConstrainedCausalPathFinder
from ..core.submodular_graph_summary import SubmodularGraphSummarizer
from ..core.temporal_subgraph_isomorphism import TemporalSubgraphMatcher
from ..core.spectral_sparsifier import SpectralGraphSparsifier
from ..core.bipartite_alignment import BipartiteOntologyAligner
from ..core.metric_dimension import MetricDimensionLandmarkFinder
from ..core.graph_anonymizer import KDegreeGraphAnonymizer

def run_financial_fraud_benchmark() -> Dict[str, Any]:
    # 1. PCST Subgraph Extraction for Sanctions Evasion Network
    nodes = [
        GraphNode("Sanctioned_Oligarch", "Entity", 100.0),
        GraphNode("Offshore_Trust_BVI", "Trust", 90.0),
        GraphNode("Front_Company_Cyprus", "Company", 85.0),
        GraphNode("Real_Estate_Holding_London", "Asset", 95.0),
        GraphNode("Legitimate_Bank_CH", "Bank", 40.0),
        GraphNode("Retail_Jewelry_Store", "Merchant", 10.0),
    ]
    edges = [
        GraphEdge("Sanctioned_Oligarch", "Offshore_Trust_BVI", 5.0),
        GraphEdge("Offshore_Trust_BVI", "Front_Company_Cyprus", 8.0),
        GraphEdge("Front_Company_Cyprus", "Real_Estate_Holding_London", 12.0),
        GraphEdge("Front_Company_Cyprus", "Legitimate_Bank_CH", 30.0),
        GraphEdge("Legitimate_Bank_CH", "Retail_Jewelry_Store", 45.0),
    ]
    pcst_solver = PrizeCollectingSteinerTreeSolver(nodes, edges)
    pcst_res = pcst_solver.solve("Sanctioned_Oligarch")

    # 2. Community Detection on Smurfing Laundering Ring
    ring_nodes = ["Smurf_1", "Smurf_2", "Smurf_3", "Aggregator_Account", "Layering_LLC_1", "Layering_LLC_2"]
    ring_edges = [
        ("Smurf_1", "Aggregator_Account", 10.0),
        ("Smurf_2", "Aggregator_Account", 12.0),
        ("Smurf_3", "Aggregator_Account", 11.0),
        ("Aggregator_Account", "Layering_LLC_1", 25.0),
        ("Aggregator_Account", "Layering_LLC_2", 20.0),
    ]
    comm_detector = HierarchicalCommunityDetector(ring_nodes, ring_edges, gamma=1.0)
    comm_res = comm_detector.solve()

    # 3. Entity Resolution on Shell Company Aliases
    mentions = [
        EntityMention("M1", "Apex Maritime Ltd", [0.91, 0.2, 0.1], "panama_leak"),
        EntityMention("M2", "Apex Maritime BVI", [0.90, 0.21, 0.08], "paradise_leak"),
        EntityMention("M3", "Apex Shipping Corp", [0.89, 0.22, 0.12], "finclist"),
        EntityMention("M4", "Omega Capital LLC", [0.1, 0.85, 0.3], "ofac_log"),
    ]
    resolver = CorrelationClusteringEntityResolver(mentions, affinity_threshold=0.7)
    resolv_res = resolver.solve()

    # 4. Constrained Path for Swift Transaction Flow
    tx_edges = [
        TemporalCausalEdge("Account_A", "Account_B", 2.0, 1.0, 0.99, 1000.0),
        TemporalCausalEdge("Account_B", "Account_C", 3.0, 2.0, 0.95, 1005.0),
        TemporalCausalEdge("Account_C", "Beneficiary_D", 4.0, 1.0, 0.92, 1010.0),
    ]
    path_finder = ConstrainedCausalPathFinder(tx_edges)
    path_res = path_finder.solve("Account_A", "Beneficiary_D", max_delay_hours=24.0)

    # 5. Submodular Graph Summary for SAR (Suspicious Activity Report)
    units = [
        KnowledgeUnit("SAR_1", "Rapid layering of $4.2M wire transfers through BVI shell accounts", 120, {"Apex Maritime", "BVI", "Layering"}, 0.95),
        KnowledgeUnit("SAR_2", "Ultimate beneficial owner obscured via nominee directors in Cyprus", 110, {"Apex Maritime", "Nominee", "UBO"}, 0.90),
        KnowledgeUnit("SAR_3", "Real estate acquisition in Mayfair without commercial rationale", 130, {"London_Asset", "Real_Estate"}, 0.85),
        KnowledgeUnit("SAR_4", "Routine payroll disbursements for local office staff", 90, {"Payroll", "Staff"}, 0.15),
    ]
    summarizer = SubmodularGraphSummarizer(units)
    summary_res = summarizer.solve(token_budget=250)

    # 6. Temporal Subgraph Isomorphism for Circular Round-Tripping Motif
    pattern = [
        PatternEdge("Node_A", "Node_B", "WIRES_TO"),
        PatternEdge("Node_B", "Node_C", "WIRES_TO"),
        PatternEdge("Node_C", "Node_A", "WIRES_TO"),
    ]
    target_edges = [
        GraphEdge("Account_1", "Account_2", 1.0, "WIRES_TO", 10.0),
        GraphEdge("Account_2", "Account_3", 1.0, "WIRES_TO", 20.0),
        GraphEdge("Account_3", "Account_1", 1.0, "WIRES_TO", 30.0),
        GraphEdge("Account_1", "Legit_Vendor", 1.0, "WIRES_TO", 15.0),
    ]
    matcher = TemporalSubgraphMatcher(target_edges)
    match_res = matcher.match(pattern)

    # 7. Spectral Sparsification of Transaction Graph
    sparse_res = SpectralGraphSparsifier(ring_nodes, ring_edges).sparsify(max_degree=3)

    # 8. Bipartite Alignment to FIBO Ontology
    onto_nodes = [
        OntologyNode("fibo:NaturalPerson", "Natural Person", "LegalEntity"),
        OntologyNode("fibo:Trustee", "Trustee", "Fiduciary"),
        OntologyNode("fibo:PrivateLimitedCompany", "Private Limited Company", "Corporation"),
    ]
    aligner = BipartiteOntologyAligner(["entity_oligarch", "entity_shell_co"], onto_nodes)
    align_affinities = {
        ("entity_oligarch", "fibo:NaturalPerson"): 0.96,
        ("entity_shell_co", "fibo:PrivateLimitedCompany"): 0.98,
    }
    align_res = aligner.solve(align_affinities)

    # 9. Metric Dimension Landmarks
    metric_res = MetricDimensionLandmarkFinder(
        ["Account_1", "Account_2", "Account_3", "Legit_Vendor"],
        [("Account_1", "Account_2"), ("Account_2", "Account_3"), ("Account_3", "Account_1"), ("Account_1", "Legit_Vendor")]
    ).solve()

    # 10. k-Degree Anonymization for Regulatory Export
    anon_res = KDegreeGraphAnonymizer(
        ["Bank_A", "Bank_B", "Bank_C", "Broker_1", "Broker_2", "Broker_3"],
        [("Bank_A", "Bank_B"), ("Bank_B", "Bank_C"), ("Broker_1", "Broker_2")]
    ).anonymize(k=2)

    return {
        "pcst_subgraph": pcst_res,
        "community_detection": comm_res,
        "entity_resolution": resolv_res,
        "causal_path": path_res,
        "submodular_summary": summary_res,
        "subgraph_isomorphism": match_res,
        "spectral_sparsification": sparse_res,
        "bipartite_alignment": align_res,
        "metric_dimension": metric_res,
        "graph_anonymization": anon_res,
    }
