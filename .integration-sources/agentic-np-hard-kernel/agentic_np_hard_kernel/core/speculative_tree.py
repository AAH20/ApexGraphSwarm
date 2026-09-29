"""
Speculative Multi-Branch Agent Rollout & Verification Tree Search Solver.
Solves the Budgeted Tree Search Problem over non-stationary multi-agent action trajectories.
Finds the highest-verification rollout path while pruning suboptimal paths under token budget B.
"""
import time
import heapq
from typing import List, Dict, Optional, Tuple
from .models import SpeculativeActionNode, SpeculativeTreeResult

class SpeculativeTreeSearchSolver:
    """
    Best-First Search with Invariant Verification Bounding and Branch-and-Bound pruning.
    """

    def __init__(self, nodes: List[SpeculativeActionNode], token_budget: int = 10000):
        self.nodes = nodes
        self.node_map = {n.node_id: n for n in nodes}
        self.budget = token_budget

        # Build tree child relationships
        self.children: Dict[str, List[str]] = {n.node_id: [] for n in nodes}
        self.roots: List[str] = []
        for n in nodes:
            if n.parent_id is None or n.parent_id not in self.node_map:
                self.roots.append(n.node_id)
            else:
                self.children[n.parent_id].append(n.node_id)

    def solve(self) -> SpeculativeTreeResult:
        t0 = time.perf_counter()

        # Priority queue for best-first exploration: (-priority, node_id, cumulative_tokens, [path])
        # Priority = verification_score / (cumulative_cost + 1)
        pq = []
        for r_id in self.roots:
            r = self.node_map[r_id]
            if r.cumulative_cost <= self.budget:
                score = r.verification_score
                heapq.heappush(pq, (-score, r_id, r.cumulative_cost, [r_id]))

        best_score = -1.0
        best_path: List[str] = []
        best_cost = 0
        pruned_count = 0
        visited_count = 0

        while pq:
            neg_score, curr_id, curr_cost, curr_path = heapq.heappop(pq)
            visited_count += 1
            node = self.node_map[curr_id]

            if node.is_terminal or not self.children[curr_id]:
                if node.verification_score > best_score:
                    best_score = node.verification_score
                    best_path = curr_path
                    best_cost = curr_cost
                continue

            # Expand children
            for child_id in self.children[curr_id]:
                child = self.node_map[child_id]
                new_cost = curr_cost + child.cumulative_cost

                # Prune if over budget
                if new_cost > self.budget:
                    pruned_count += 1
                    continue

                # Prune if upper-bound verification cannot beat current best
                # Assume optimistic child verification cannot exceed 1.0
                if child.verification_score < best_score * 0.4:
                    pruned_count += 1
                    continue

                heapq.heappush(pq, (-child.verification_score, child_id, new_cost, curr_path + [child_id]))

        if not best_path and self.roots:
            best_path = [self.roots[0]]
            best_score = self.node_map[self.roots[0]].verification_score
            best_cost = self.node_map[self.roots[0]].cumulative_cost

        t1 = time.perf_counter()
        return SpeculativeTreeResult(
            optimal_path=best_path,
            total_tokens_spent=best_cost,
            highest_verification_score=max(0.0, best_score),
            nodes_pruned=pruned_count,
            algorithm="BEST_FIRST_SPECULATIVE_BNB",
            execution_time_us=(t1 - t0) * 1e6
        )
