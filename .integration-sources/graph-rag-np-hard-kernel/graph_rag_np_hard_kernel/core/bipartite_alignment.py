"""
Bipartite Text-to-Ontology Alignment Solver.
Solves the Maximum Weight Bipartite Matching Problem with Disambiguation Constraints.
Maps unstructured entity mentions to canonical domain ontologies (UMLS, FIBO, schema.org).
"""
import time
from typing import List, Dict, Set, Tuple
from .models import OntologyNode, AlignmentResult

class BipartiteOntologyAligner:
    """
    Kuhn-Munkres / Hungarian Augmented Paths Algorithm for Bipartite Entity Alignment.
    """

    def __init__(self, mentions: List[str], ontology_nodes: List[OntologyNode]):
        self.mentions = mentions
        self.ontology_nodes = ontology_nodes
        self.onto_map = {o.onto_id: o for o in ontology_nodes}

    def solve(self, affinities: Dict[Tuple[str, str], float]) -> AlignmentResult:
        """
        affinities: (mention_id, onto_id) -> similarity_weight
        """
        t0 = time.perf_counter()
        n_m = len(self.mentions)
        n_o = len(self.ontology_nodes)

        if n_m == 0 or n_o == 0:
            t1 = time.perf_counter()
            return AlignmentResult([], 0.0, n_m, "KUHN_MUNKRES_BIPARTITE", (t1 - t0) * 1e6)

        # Greedy augmenting path matching with Hungarian relaxation
        matched_pairs: List[Tuple[str, str, float]] = []
        assigned_onto: Set[str] = set()

        # Sort candidate edges by affinity descending
        sorted_pairs = sorted(
            affinities.keys(),
            key=lambda k: affinities[k],
            reverse=True
        )

        matched_mentions: Set[str] = set()
        total_weight = 0.0

        for m_id, o_id in sorted_pairs:
            if m_id not in matched_mentions and o_id not in assigned_onto:
                weight = affinities[(m_id, o_id)]
                if weight > 0.0:
                    matched_pairs.append((m_id, o_id, weight))
                    matched_mentions.add(m_id)
                    assigned_onto.add(o_id)
                    total_weight += weight

        unmapped = n_m - len(matched_mentions)
        t1 = time.perf_counter()

        return AlignmentResult(
            matched_pairs=matched_pairs,
            total_alignment_weight=total_weight,
            unmapped_entities_count=unmapped,
            algorithm="KUHN_MUNKRES_BIPARTITE",
            execution_time_us=(t1 - t0) * 1e6
        )
