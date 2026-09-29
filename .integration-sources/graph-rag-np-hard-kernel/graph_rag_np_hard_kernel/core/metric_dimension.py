"""
Metric Dimension & Landmark Resolving Set Solver.
Finds the minimal subset of landmark nodes W subset V whose distance vectors uniquely identify all graph entities.
Enables distortion-free topological graph indexing and ultra-fast GraphRAG distance queries.
"""
import time
from typing import List, Dict, Set, Tuple
from collections import deque
from .models import MetricDimensionResult

class MetricDimensionLandmarkFinder:
    """
    Greedy Information-Theoretic Solver for Minimum Metric Dimension.
    Every pair u, v in V must be distinguished by at least one landmark w in W: d(u, w) != d(v, w).
    """

    def __init__(self, nodes: List[str], edges: List[Tuple[str, str]]):
        self.nodes = list(nodes)
        self.edges = edges
        self.n = len(nodes)
        self.node_idx = {u: i for i, u in enumerate(self.nodes)}

        # Precompute unweighted all-pairs shortest path distances via BFS
        self.dist: List[List[int]] = [[999999] * self.n for _ in range(self.n)]
        adj: Dict[int, List[int]] = {i: [] for i in range(self.n)}
        for u, v in edges:
            if u in self.node_idx and v in self.node_idx:
                ui, vi = self.node_idx[u], self.node_idx[v]
                adj[ui].append(vi)
                adj[vi].append(ui)

        for i in range(self.n):
            self.dist[i][i] = 0
            q = deque([i])
            while q:
                curr = q.popleft()
                d = self.dist[i][curr]
                for nxt in adj[curr]:
                    if self.dist[i][nxt] > d + 1:
                        self.dist[i][nxt] = d + 1
                        q.append(nxt)

    def solve(self) -> MetricDimensionResult:
        t0 = time.perf_counter()
        n = self.n
        if n < 2:
            t1 = time.perf_counter()
            return MetricDimensionResult(self.nodes, len(self.nodes), 100.0, "METRIC_DIMENSION_GREEDY", (t1 - t0) * 1e6)

        # All undistinguished node pairs (i, j) with i < j
        undistinguished = set((i, j) for i in range(n) for j in range(i + 1, n))
        total_pairs = len(undistinguished)
        landmarks: List[int] = []

        # Greedy choice: pick node w that distinguishes the maximum number of currently undistinguished pairs
        while undistinguished:
            best_w = None
            best_distinguished_count = -1

            for w in range(n):
                if w in landmarks:
                    continue
                # Count pairs (i, j) where dist(i, w) != dist(j, w)
                dist_count = sum(1 for (i, j) in undistinguished if self.dist[i][w] != self.dist[j][w])
                if dist_count > best_distinguished_count:
                    best_distinguished_count = dist_count
                    best_w = w

            if best_w is None or best_distinguished_count == 0:
                break

            landmarks.append(best_w)
            # Remove distinguished pairs
            new_undist = set((i, j) for (i, j) in undistinguished if self.dist[i][best_w] == self.dist[j][best_w])
            undistinguished = new_undist

        resolved_pct = (1.0 - (len(undistinguished) / max(total_pairs, 1))) * 100.0
        landmark_node_ids = [self.nodes[w] for w in landmarks]

        t1 = time.perf_counter()
        return MetricDimensionResult(
            landmark_nodes=landmark_node_ids,
            metric_dimension_k=len(landmarks),
            uniquely_resolved_percentage=resolved_pct,
            algorithm="METRIC_DIMENSION_GREEDY",
            execution_time_us=(t1 - t0) * 1e6
        )
