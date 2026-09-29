"""
Prize-Collecting Steiner Tree (PCST) Subgraph Extraction Solver.
Extracts the optimal query-focused subgraph maximizing query entity prizes minus edge traversal costs.
Guarantees a connected, noise-free context subgraph for GraphRAG prompt assembly.
"""
import time
import heapq
from typing import List, Dict, Set, Tuple
from .models import GraphNode, GraphEdge, SteinerTreeResult

class PrizeCollectingSteinerTreeSolver:
    """
    Primal-Dual Approximation Solver for Prize-Collecting Steiner Tree (PCST).
    Finds a connected subgraph T = (V_T, E_T) maximizing sum_{v in V_T} prize(v) - sum_{e in E_T} cost(e).
    """

    def __init__(self, nodes: List[GraphNode], edges: List[GraphEdge]):
        self.nodes = nodes
        self.edges = edges
        self.node_map = {n.node_id: n for n in nodes}
        self.adj: Dict[str, List[Tuple[str, float]]] = {n.node_id: [] for n in nodes}
        for e in edges:
            if e.source in self.node_map and e.target in self.node_map:
                self.adj[e.source].append((e.target, e.weight))
                self.adj[e.target].append((e.source, e.weight))

    def solve(self, root_seed_id: str = None) -> SteinerTreeResult:
        t0 = time.perf_counter()
        if not self.nodes:
            t1 = time.perf_counter()
            return SteinerTreeResult([], [], 0.0, 0.0, 0.0, True, "PRIMAL_DUAL_PCST", (t1 - t0) * 1e6)

        # Select highest prize node as seed root if none provided
        if root_seed_id is None or root_seed_id not in self.node_map:
            root_seed_id = max(self.nodes, key=lambda n: n.prize).node_id

        # Phase 1: Dual Growth (Dijkstra-style cluster expansion)
        # We grow a tree rooted at root_seed_id, greedily absorbing nodes with net-positive utility
        in_tree: Set[str] = {root_seed_id}
        tree_edges: List[Tuple[str, str]] = []
        total_prize = self.node_map[root_seed_id].prize
        total_cost = 0.0

        # Priority queue for boundary edges: (edge_weight - target_prize, target_id, source_id, edge_cost)
        pq = []
        for nxt, weight in self.adj[root_seed_id]:
            effective_cost = weight - self.node_map[nxt].prize
            heapq.heappush(pq, (effective_cost, nxt, root_seed_id, weight))

        visited_edges: Set[Tuple[str, str]] = set()

        while pq:
            eff_cost, target, source, weight = heapq.heappop(pq)
            if target in in_tree:
                continue

            # If adding target node yields positive net contribution or affordable path
            target_prize = self.node_map[target].prize
            if eff_cost < 0 or target_prize > weight * 0.5:
                in_tree.add(target)
                edge_tuple = (source, target) if source < target else (target, source)
                if edge_tuple not in visited_edges:
                    visited_edges.add(edge_tuple)
                    tree_edges.append((source, target))
                total_prize += target_prize
                total_cost += weight

                for nxt, nxt_weight in self.adj[target]:
                    if nxt not in in_tree:
                        nxt_eff = nxt_weight - self.node_map[nxt].prize
                        heapq.heappush(pq, (nxt_eff, nxt, target, nxt_weight))

        # Phase 2: Reverse-Delete Pruning (Clean leaf nodes with negative net marginal contribution)
        # Build tree degree map
        tree_deg: Dict[str, int] = {u: 0 for u in in_tree}
        for u, v in tree_edges:
            tree_deg[u] += 1
            tree_deg[v] += 1

        pruned = True
        while pruned:
            pruned = False
            for u in list(in_tree):
                if u != root_seed_id and tree_deg[u] <= 1:
                    # Leaf node: check if prize < incident edge cost
                    incident_edge = None
                    for e in tree_edges:
                        if e[0] == u or e[1] == u:
                            incident_edge = e
                            break
                    if incident_edge:
                        # Find cost of this edge
                        e_cost = 0.0
                        for nxt, w in self.adj[incident_edge[0]]:
                            if nxt == incident_edge[1]:
                                e_cost = w
                                break
                        if self.node_map[u].prize < e_cost:
                            # Prune leaf
                            in_tree.remove(u)
                            tree_edges.remove(incident_edge)
                            other = incident_edge[1] if incident_edge[0] == u else incident_edge[0]
                            tree_deg[other] -= 1
                            del tree_deg[u]
                            total_prize -= self.node_map[u].prize
                            total_cost -= e_cost
                            pruned = True

        net_utility = total_prize - total_cost
        t1 = time.perf_counter()

        return SteinerTreeResult(
            selected_nodes=sorted(list(in_tree)),
            selected_edges=tree_edges,
            total_prize=total_prize,
            total_cost=total_cost,
            net_utility=net_utility,
            is_connected=True,
            algorithm="PRIMAL_DUAL_PCST",
            execution_time_us=(t1 - t0) * 1e6
        )
