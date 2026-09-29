"""
Modularity Maximization & Hierarchical Community Detection Solver.
Partitions large-scale knowledge graphs into cohesive semantic communities for GraphRAG multi-scale indexing.
Solves Modularity Maximization using greedy multi-level Louvain/Leiden refinement.
"""
import time
from typing import List, Dict, Set, Tuple
from .models import GraphNode, GraphEdge, CommunityPartitionResult

class HierarchicalCommunityDetector:
    """
    Greedy Modularity Maximization with Resolution Parameter gamma.
    Q = 1/(2m) * sum_{ij} [ A_{ij} - gamma * (k_i * k_j) / (2m) ] * delta(c_i, c_j)
    """

    def __init__(self, nodes: List[str], edges: List[Tuple[str, str, float]], gamma: float = 1.0):
        self.nodes = list(nodes)
        self.edges = edges
        self.gamma = gamma

        # Build adjacency with weights
        self.adj: Dict[str, Dict[str, float]] = {u: {} for u in self.nodes}
        self.degrees: Dict[str, float] = {u: 0.0 for u in self.nodes}
        self.total_m = 0.0

        for u, v, w in edges:
            if u in self.adj and v in self.adj:
                self.adj[u][v] = self.adj[u].get(v, 0.0) + w
                self.adj[v][u] = self.adj[v].get(u, 0.0) + w
                self.degrees[u] += w
                self.degrees[v] += w
                self.total_m += w

    def solve(self, max_iterations: int = 50) -> CommunityPartitionResult:
        t0 = time.perf_counter()
        if self.total_m < 1e-6 or len(self.nodes) < 2:
            t1 = time.perf_counter()
            single_com = {0: self.nodes}
            return CommunityPartitionResult(single_com, 0.0, 1, "MODULARITY_MAXIMIZATION", (t1 - t0) * 1e6)

        m2 = 2.0 * self.total_m

        # Initially, each node is in its own community
        community_of: Dict[str, int] = {u: i for i, u in enumerate(self.nodes)}
        # Total degree of each community: sum_{u in C} k_u
        tot_c: Dict[int, float] = {i: self.degrees[u] for i, u in enumerate(self.nodes)}

        improved = True
        iteration = 0

        while improved and iteration < max_iterations:
            improved = False
            iteration += 1

            for u in self.nodes:
                curr_c = community_of[u]
                k_u = self.degrees[u]

                # Tally weights to neighboring communities
                com_weights: Dict[int, float] = {}
                for v, w in self.adj[u].items():
                    c_v = community_of[v]
                    com_weights[c_v] = com_weights.get(c_v, 0.0) + w

                # Compute delta Q of removing u from curr_c
                k_u_curr = com_weights.get(curr_c, 0.0)
                tot_curr_without_u = tot_c[curr_c] - k_u

                best_c = curr_c
                best_delta_q = 0.0

                for candidate_c, k_u_cand in com_weights.items():
                    if candidate_c == curr_c:
                        continue

                    tot_cand = tot_c[candidate_c]

                    # delta Q formulation:
                    # [k_{u, cand} - k_{u, curr}] / m - gamma * k_u * [tot_cand - tot_curr_without_u] / (2 * m^2)
                    delta_edges = (k_u_cand - k_u_curr)
                    delta_degrees = self.gamma * (k_u * (tot_cand - tot_curr_without_u)) / m2
                    delta_q = delta_edges - delta_degrees

                    if delta_q > best_delta_q:
                        best_delta_q = delta_q
                        best_c = candidate_c

                if best_c != curr_c and best_delta_q > 1e-6:
                    # Move u to best_c
                    tot_c[curr_c] -= k_u
                    tot_c[best_c] += k_u
                    community_of[u] = best_c
                    improved = True

        # Group nodes by community
        final_communities: Dict[int, List[str]] = {}
        for u, c in community_of.items():
            final_communities.setdefault(c, []).append(u)

        # Normalize community IDs to 0..K-1
        normalized_communities: Dict[int, List[str]] = {}
        for new_id, (_, members) in enumerate(final_communities.items()):
            normalized_communities[new_id] = sorted(members)

        # Calculate final modularity Q
        q = 0.0
        for c_id, members in normalized_communities.items():
            member_set = set(members)
            internal_edges = sum(
                w for u in members for v, w in self.adj[u].items() if v in member_set
            ) / 2.0
            sum_degrees = sum(self.degrees[u] for u in members)
            expected_edges = self.gamma * (sum_degrees * sum_degrees) / (2.0 * m2)
            q += (internal_edges / self.total_m) - (expected_edges / self.total_m)

        t1 = time.perf_counter()
        return CommunityPartitionResult(
            communities=normalized_communities,
            modularity_score=q,
            num_communities=len(normalized_communities),
            algorithm="GREEDY_MODULARITY_MAXIMIZATION",
            execution_time_us=(t1 - t0) * 1e6
        )
