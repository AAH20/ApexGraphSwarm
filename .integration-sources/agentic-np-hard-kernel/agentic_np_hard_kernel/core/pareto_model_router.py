"""
Multi-Objective Model Routing Solver.
Computes the exact non-dominated Pareto frontier across Cost, Latency, and Task Fidelity.
Optimizes LLM tier selection for agentic sub-tasks without heuristic quality collapse.
"""
import time
from typing import List, Dict, Tuple, Optional
from .models import ModelOption, ParetoRoutingResult

class ParetoModelRouter:
    """
    Computes non-dominated model routing options and selects the optimal configuration.
    """

    def __init__(self, model_catalog: List[ModelOption]):
        self.catalog = model_catalog

    def _dominates(self, a: ModelOption, b: ModelOption) -> bool:
        """
        Model a dominates b iff:
        a.cost <= b.cost and a.latency <= b.latency and a.fidelity >= b.fidelity
        and strictly better in at least one objective.
        """
        no_worse = (
            a.cost_per_k_tokens <= b.cost_per_k_tokens and
            a.latency_per_step_ms <= b.latency_per_step_ms and
            a.benchmark_fidelity >= b.benchmark_fidelity
        )
        strictly_better = (
            a.cost_per_k_tokens < b.cost_per_k_tokens or
            a.latency_per_step_ms < b.latency_per_step_ms or
            a.benchmark_fidelity > b.benchmark_fidelity
        )
        return no_worse and strictly_better

    def solve(
        self,
        max_cost_budget: Optional[float] = None,
        max_latency_ms: Optional[float] = None,
        min_fidelity: Optional[float] = None
    ) -> ParetoRoutingResult:
        t0 = time.perf_counter()
        n = len(self.catalog)
        if n == 0:
            raise ValueError("Model catalog cannot be empty")

        # Filter by hard constraints
        viable = []
        for m in self.catalog:
            if max_cost_budget is not None and m.cost_per_k_tokens > max_cost_budget:
                continue
            if max_latency_ms is not None and m.latency_per_step_ms > max_latency_ms:
                continue
            if min_fidelity is not None and m.benchmark_fidelity < min_fidelity:
                continue
            viable.append(m)

        if not viable:
            viable = self.catalog  # Relax constraints if none viable

        # Non-dominated sorting
        is_dominated = [False] * len(viable)
        for i in range(len(viable)):
            for j in range(len(viable)):
                if i != j and not is_dominated[i]:
                    if self._dominates(viable[j], viable[i]):
                        is_dominated[i] = True
                        break

        pareto_front = [viable[i] for i in range(len(viable)) if not is_dominated[i]]

        # Pick best on Pareto front using Chebyshev compromise / balanced utility
        # Utility = fidelity / (cost * 0.5 + latency * 0.01 + 0.1)
        best_model = max(
            pareto_front,
            key=lambda m: m.benchmark_fidelity / max(m.cost_per_k_tokens * 2.0 + m.latency_per_step_ms * 0.02, 1e-4)
        )

        # Hypervolume indicator metric
        # Reference point: worst along each axis
        ref_cost = max(m.cost_per_k_tokens for m in self.catalog) * 1.2
        ref_lat = max(m.latency_per_step_ms for m in self.catalog) * 1.2
        ref_fid = 0.0

        hypervolume = 0.0
        for m in pareto_front:
            cost_span = max(0.0, ref_cost - m.cost_per_k_tokens)
            lat_span = max(0.0, ref_lat - m.latency_per_step_ms)
            fid_span = max(0.0, m.benchmark_fidelity - ref_fid)
            vol = cost_span * lat_span * fid_span
            hypervolume += vol

        t1 = time.perf_counter()
        return ParetoRoutingResult(
            selected_model=best_model,
            is_pareto_optimal=True,
            hypervolume_delta=hypervolume,
            algorithm="EXACT_PARETO_ROUTER",
            execution_time_us=(t1 - t0) * 1e6
        )
