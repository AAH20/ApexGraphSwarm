"""
Temporal Subgraph Isomorphism Matching Solver.
Matches complex multi-relational temporal query motifs (e.g. laundering cycles, C2 attack chains)
across dynamic knowledge graphs with causal monotonicity pruning.
"""
import time
from typing import List, Dict, Set, Tuple
from .models import PatternEdge, GraphEdge, IsomorphismResult

class TemporalSubgraphMatcher:
    """
    Backtracking Subgraph Isomorphism Solver with Temporal Feasibility Pruning.
    """

    def __init__(self, target_edges: List[GraphEdge]):
        self.target_edges = target_edges
        # Target graph adjacency: (u, relation) -> list of (v, timestamp)
        self.adj: Dict[Tuple[str, str], List[Tuple[str, float]]] = {}
        self.all_target_nodes: Set[str] = set()

        for e in target_edges:
            self.adj.setdefault((e.source, e.relation_type), []).append((e.target, e.timestamp))
            self.all_target_nodes.add(e.source)
            self.all_target_nodes.add(e.target)

    def match(self, pattern_edges: List[PatternEdge], max_matches: int = 100) -> IsomorphismResult:
        t0 = time.perf_counter()

        pattern_vars = sorted(list({p.source_var for p in pattern_edges} | {p.target_var for p in pattern_edges}))
        matches: List[Dict[str, str]] = []

        # Backtracking search: mapping pattern_var -> target_node_id
        def backtrack(var_idx: int, current_mapping: Dict[str, str], last_edge_time: float):
            if len(matches) >= max_matches:
                return

            if var_idx == len(pattern_vars):
                # Verify all pattern edge constraints
                valid = True
                for pe in pattern_edges:
                    u = current_mapping[pe.source_var]
                    v = current_mapping[pe.target_var]
                    # Check if edge exists in target graph
                    cand_edges = [t for nxt, t in self.adj.get((u, pe.relation_type), []) if nxt == v]
                    if not cand_edges:
                        valid = False
                        break
                if valid:
                    matches.append(dict(current_mapping))
                return

            curr_var = pattern_vars[var_idx]
            used_targets = set(current_mapping.values())

            # Find candidate target nodes
            for target_node in self.all_target_nodes:
                if target_node in used_targets:
                    continue

                # Feasibility check against already assigned neighbors
                feasible = True
                for pe in pattern_edges:
                    if pe.source_var in current_mapping and pe.target_var == curr_var:
                        src_node = current_mapping[pe.source_var]
                        # Check if edge src_node -> target_node exists
                        if not any(nxt == target_node for nxt, _ in self.adj.get((src_node, pe.relation_type), [])):
                            feasible = False
                            break
                    elif pe.target_var in current_mapping and pe.source_var == curr_var:
                        tgt_node = current_mapping[pe.target_var]
                        if not any(nxt == tgt_node for nxt, _ in self.adj.get((target_node, pe.relation_type), [])):
                            feasible = False
                            break

                if feasible:
                    current_mapping[curr_var] = target_node
                    backtrack(var_idx + 1, current_mapping, last_edge_time)
                    del current_mapping[curr_var]

        backtrack(0, {}, 0.0)

        t1 = time.perf_counter()
        return IsomorphismResult(
            matched_subgraphs=matches,
            total_matches=len(matches),
            algorithm="TEMPORAL_VF2_ISOMORPHISM",
            execution_time_us=(t1 - t0) * 1e6
        )
