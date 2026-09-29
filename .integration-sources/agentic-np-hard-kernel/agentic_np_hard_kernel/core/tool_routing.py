"""
Combinatorial Tool Routing & Selection Solver.
Solves the Multi-Dimensional Knapsack with Dependency Precedence Constraints (0-1 MKP-PC).
Selects the optimal subset of agent tools maximizing task utility under strict latency and token limits.
"""
import time
from typing import List, Dict, Set, Tuple
from .models import ToolDefinition, ToolRoutingResult

class CombinatorialToolRouter:
    """
    Branch-and-Bound solver for optimal tool selection under multi-resource limits and dependencies.
    """

    def __init__(self, tool_inventory: List[ToolDefinition]):
        self.tools = tool_inventory
        self.tool_map = {t.tool_id: t for t in tool_inventory}

    def solve(self, max_latency_ms: float, max_token_budget: int) -> ToolRoutingResult:
        t0 = time.perf_counter()
        n = len(self.tools)

        # Precompute transitive dependencies for each tool
        closure: Dict[str, Set[str]] = {}
        for t in self.tools:
            visited = set()
            stack = list(t.required_prerequisites)
            while stack:
                curr = stack.pop()
                if curr not in visited and curr in self.tool_map:
                    visited.add(curr)
                    stack.extend(self.tool_map[curr].required_prerequisites)
            closure[t.tool_id] = visited

        # Sort tools by efficiency heuristic: utility / (latency + token_ratio)
        sorted_indices = sorted(
            range(n),
            key=lambda idx: self.tools[idx].expected_utility / max(
                self.tools[idx].latency_ms + self.tools[idx].token_cost * 0.05, 1e-4
            ),
            reverse=True
        )

        best_utility = -1.0
        best_selection: Set[str] = set()
        best_latency = 0.0
        best_tokens = 0

        # Branch and Bound search
        def search(idx: int, current_selected: Set[str], curr_util: float, curr_lat: float, curr_tok: int):
            nonlocal best_utility, best_selection, best_latency, best_tokens

            # Feasibility check
            if curr_lat > max_latency_ms or curr_tok > max_token_budget:
                return

            if curr_util > best_utility:
                best_utility = curr_util
                best_selection = set(current_selected)
                best_latency = curr_lat
                best_tokens = curr_tok

            if idx >= n:
                return

            # Upper bound on remaining possible utility
            rem_util = sum(self.tools[sorted_indices[i]].expected_utility for i in range(idx, n))
            if curr_util + rem_util <= best_utility:
                return  # Prune branch

            candidate_idx = sorted_indices[idx]
            cand = self.tools[candidate_idx]

            # Branch 1: Try including candidate (along with its closure)
            needed = {cand.tool_id} | closure[cand.tool_id]
            new_items = needed - current_selected

            add_util = sum(self.tool_map[tid].expected_utility for tid in new_items)
            add_lat = sum(self.tool_map[tid].latency_ms for tid in new_items)
            add_tok = sum(self.tool_map[tid].token_cost for tid in new_items)

            if curr_lat + add_lat <= max_latency_ms and curr_tok + add_tok <= max_token_budget:
                search(
                    idx + 1,
                    current_selected | needed,
                    curr_util + add_util,
                    curr_lat + add_lat,
                    curr_tok + add_tok
                )

            # Branch 2: Exclude candidate
            search(idx + 1, current_selected, curr_util, curr_lat, curr_tok)

        search(0, set(), 0.0, 0.0, 0)

        selected_tool_objs = [self.tool_map[tid] for tid in best_selection]
        t1 = time.perf_counter()

        return ToolRoutingResult(
            selected_tools=selected_tool_objs,
            total_utility=best_utility if best_utility > 0 else 0.0,
            total_latency_ms=best_latency,
            total_token_cost=best_tokens,
            algorithm="BRANCH_AND_BOUND_MKP_PC",
            execution_time_us=(t1 - t0) * 1e6
        )

    def solve_greedy_baseline(self, max_latency_ms: float, max_token_budget: int) -> ToolRoutingResult:
        """Greedy heuristic: greedily pick tool with highest utility density."""
        t0 = time.perf_counter()
        selected: Set[str] = set()
        curr_lat = 0.0
        curr_tok = 0
        curr_util = 0.0

        sorted_tools = sorted(
            self.tools,
            key=lambda t: t.expected_utility / max(t.latency_ms + t.token_cost * 0.05, 1e-4),
            reverse=True
        )

        for t in sorted_tools:
            if t.tool_id in selected:
                continue
            # Check prerequisites
            prereqs_met = all(p in selected for p in t.required_prerequisites)
            if prereqs_met:
                if curr_lat + t.latency_ms <= max_latency_ms and curr_tok + t.token_cost <= max_token_budget:
                    selected.add(t.tool_id)
                    curr_lat += t.latency_ms
                    curr_tok += t.token_cost
                    curr_util += t.expected_utility

        selected_objs = [self.tool_map[tid] for tid in selected]
        t1 = time.perf_counter()
        return ToolRoutingResult(
            selected_tools=selected_objs,
            total_utility=curr_util,
            total_latency_ms=curr_lat,
            total_token_cost=curr_tok,
            algorithm="GREEDY_HEURISTIC",
            execution_time_us=(t1 - t0) * 1e6
        )
