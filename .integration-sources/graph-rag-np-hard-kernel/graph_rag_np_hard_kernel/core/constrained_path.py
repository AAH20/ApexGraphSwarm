"""
Constrained Shortest Path & Multi-Hop Causal Reasoning Solver.
Solves the Weight-Constrained Shortest Path Problem (WCSPP) over temporal knowledge graphs.
Finds causal reasoning chains minimizing semantic penalty subject to strict latency, delay, and confidence constraints.
"""
import time
import heapq
from typing import List, Dict, Set, Tuple, Optional
from .models import TemporalCausalEdge, ConstrainedPathResult

class ConstrainedCausalPathFinder:
    """
    Multi-Criteria Label-Setting Dynamic Programming for Constrained Shortest Paths.
    Enforces temporal causality: t_{k} >= t_{k-1}.
    """

    def __init__(self, edges: List[TemporalCausalEdge]):
        self.edges = edges
        self.adj: Dict[str, List[TemporalCausalEdge]] = {}
        self.all_nodes: Set[str] = set()

        for e in edges:
            self.adj.setdefault(e.source, []).append(e)
            self.all_nodes.add(e.source)
            self.all_nodes.add(e.target)

    def solve(
        self,
        source_node: str,
        target_node: str,
        max_delay_hours: float = 72.0,
        min_confidence: float = 0.50
    ) -> ConstrainedPathResult:
        t0 = time.perf_counter()

        if source_node == target_node:
            t1 = time.perf_counter()
            return ConstrainedPathResult([source_node], 0.0, 0.0, 1.0, True, "LABEL_SETTING_WCSPP", (t1 - t0) * 1e6)

        # Priority Queue state: (cost, cumulative_delay, min_conf, curr_node, last_timestamp, [path])
        pq = [(0.0, 0.0, 1.0, source_node, -float('inf'), [source_node])]

        # Pareto labels per node: list of (cost, delay) non-dominated pairs
        pareto_labels: Dict[str, List[Tuple[float, float]]] = {u: [] for u in self.all_nodes}

        best_path: Optional[List[str]] = None
        best_cost = float('inf')
        best_delay = 0.0
        best_conf = 0.0

        while pq:
            curr_cost, curr_delay, curr_conf, curr_u, last_t, path = heapq.heappop(pq)

            if curr_u == target_node:
                if curr_cost < best_cost:
                    best_cost = curr_cost
                    best_path = path
                    best_delay = curr_delay
                    best_conf = curr_conf
                continue

            # Check if current label is dominated at curr_u
            is_dominated = False
            for p_cost, p_delay in pareto_labels[curr_u]:
                if p_cost <= curr_cost and p_delay <= curr_delay:
                    is_dominated = True
                    break
            if is_dominated:
                continue

            pareto_labels[curr_u].append((curr_cost, curr_delay))

            # Expand neighbors
            for edge in self.adj.get(curr_u, []):
                # Filter by confidence constraint
                if edge.confidence < min_confidence:
                    continue

                # Filter by temporal monotonicity: causal event must not precede cause
                if edge.timestamp < last_t:
                    continue

                nxt_cost = curr_cost + edge.traversal_cost
                nxt_delay = curr_delay + edge.delay_hours
                nxt_conf = min(curr_conf, edge.confidence)

                # Filter by delay constraint
                if nxt_delay > max_delay_hours:
                    continue

                if nxt_cost < best_cost:
                    heapq.heappush(
                        pq,
                        (nxt_cost, nxt_delay, nxt_conf, edge.target, edge.timestamp, path + [edge.target])
                    )

        t1 = time.perf_counter()
        if best_path is not None:
            return ConstrainedPathResult(
                path_nodes=best_path,
                total_cost=best_cost,
                total_delay_hours=best_delay,
                bottleneck_confidence=best_conf,
                is_causally_valid=True,
                algorithm="LABEL_SETTING_WCSPP",
                execution_time_us=(t1 - t0) * 1e6
            )
        else:
            return ConstrainedPathResult(
                path_nodes=[],
                total_cost=float('inf'),
                total_delay_hours=0.0,
                bottleneck_confidence=0.0,
                is_causally_valid=False,
                algorithm="LABEL_SETTING_WCSPP",
                execution_time_us=(t1 - t0) * 1e6
            )
