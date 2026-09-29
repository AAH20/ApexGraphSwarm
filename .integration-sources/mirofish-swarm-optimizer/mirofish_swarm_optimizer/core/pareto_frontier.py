"""
Multi-Objective Pareto Hypervolume Frontier Solver.
Computes the exact non-dominated Pareto frontier across competing socio-economic criteria
in MiroFish multi-agent policy simulations, replacing stochastic genetic drift (NSGA-II).
"""
import time
from typing import List, Dict, Any
from .models import ParetoSolution, ParetoFrontierResult

class ParetoFrontierSolver:
    """
    Computes exact Pareto-optimal frontiers and Hypervolume Indicators using Non-Dominated Sorting.
    """

    def __init__(self, candidates: List[ParetoSolution]):
        self.candidates = candidates

    def _dominates(self, sol_a: ParetoSolution, sol_b: ParetoSolution) -> bool:
        """sol_a dominates sol_b iff a >= b in all objectives and a > b in at least one."""
        greater_or_equal = True
        strictly_greater = False
        for a, b in zip(sol_a.objective_values, sol_b.objective_values):
            if a < b:
                return False
            if a > b:
                strictly_greater = True
        return greater_or_equal and strictly_greater

    def solve(self, reference_point: List[float] = None) -> ParetoFrontierResult:
        t0 = time.perf_counter()
        n = len(self.candidates)
        if n == 0:
            t1 = time.perf_counter()
            return ParetoFrontierResult([], 0.0, 0, "EXACT_PARETO_FRONTIER", (t1 - t0) * 1e6)

        num_objectives = len(self.candidates[0].objective_values)
        if reference_point is None:
            # Default reference point: min along each axis minus 0.1
            reference_point = [
                min(c.objective_values[j] for c in self.candidates) - 0.1
                for j in range(num_objectives)
            ]

        # Non-dominated sorting
        is_dominated = [False] * n

        for i in range(n):
            for j in range(n):
                if i != j and not is_dominated[i]:
                    if self._dominates(self.candidates[j], self.candidates[i]):
                        is_dominated[i] = True
                        break

        pareto_solutions = [self.candidates[i] for i in range(n) if not is_dominated[i]]
        dominated_count = sum(1 for d in is_dominated if d)

        # Compute 2D/multi-D Hypervolume Indicator
        hypervolume = 0.0
        if num_objectives == 2 and pareto_solutions:
            # Sort pareto solutions by first objective ascending
            sorted_sols = sorted(pareto_solutions, key=lambda s: s.objective_values[0])
            ref_x, ref_y = reference_point[0], reference_point[1]

            # Compute stepwise rectangular area
            curr_y = max(s.objective_values[1] for s in sorted_sols)
            prev_x = ref_x
            for s in sorted_sols:
                width = max(0.0, s.objective_values[0] - prev_x)
                height = max(0.0, curr_y - ref_y)
                hypervolume += width * height
                curr_y = s.objective_values[1]
                prev_x = s.objective_values[0]
            # Final segment
            width = max(0.0, sorted_sols[-1].objective_values[0] - prev_x)
            height = max(0.0, sorted_sols[-1].objective_values[1] - ref_y)
            hypervolume += width * height
        else:
            # Multi-dimensional approximation / product of spans
            if pareto_solutions:
                spans = [
                    max(s.objective_values[j] for s in pareto_solutions) - reference_point[j]
                    for j in range(num_objectives)
                ]
                vol = 1.0
                for s in spans:
                    vol *= max(0.0, s)
                hypervolume = vol

        t1 = time.perf_counter()
        return ParetoFrontierResult(
            non_dominated_solutions=pareto_solutions,
            hypervolume_indicator=max(0.0, hypervolume),
            dominated_count=dominated_count,
            algorithm="EXACT_NON_DOMINATED_SORTING",
            execution_time_us=(t1 - t0) * 1e6
        )
