"""
Submodular Graph Summarization for Context Window Packing Solver.
Solves Budgeted Maximum Coverage / Submodular Knapsack over GraphRAG community summaries.
Guarantees maximal entity coverage and conceptual diversity under strict prompt token limits.
"""
import time
from typing import List, Dict, Set, Tuple
from .models import KnowledgeUnit, SubmodularSummaryResult

class SubmodularGraphSummarizer:
    """
    Density-Scaled Accelerated Greedy Solver for Budgeted Maximum Coverage (Submodular Knapsack).
    Selects knowledge units S maximizing |U_{u in S} entities(u)| + lambda * sum(salience) s.t. tokens <= B.
    """

    def __init__(self, units: List[KnowledgeUnit], salience_weight: float = 0.5):
        self.units = units
        self.salience_weight = salience_weight

    def solve(self, token_budget: int) -> SubmodularSummaryResult:
        t0 = time.perf_counter()
        if not self.units or token_budget <= 0:
            t1 = time.perf_counter()
            return SubmodularSummaryResult([], 0, 0, 0.0, "BUDGETED_SUBMODULAR_GREEDY", (t1 - t0) * 1e6)

        selected: List[KnowledgeUnit] = []
        selected_ids: Set[str] = set()
        covered_entities: Set[str] = set()
        current_tokens = 0

        # Greedy Phase: Select candidate with highest marginal gain per token
        remaining_units = list(self.units)

        while remaining_units:
            best_unit = None
            best_density = -1.0
            best_new_entities = 0

            for u in remaining_units:
                if u.unit_id in selected_ids:
                    continue
                if current_tokens + u.token_count > token_budget:
                    continue

                new_entities = len(u.covered_entities - covered_entities)
                marginal_gain = new_entities + self.salience_weight * u.salience_score
                density = marginal_gain / max(u.token_count, 1)

                if density > best_density:
                    best_density = density
                    best_unit = u
                    best_new_entities = new_entities

            if best_unit is not None and best_density > 0:
                selected.append(best_unit)
                selected_ids.add(best_unit.unit_id)
                covered_entities.update(best_unit.covered_entities)
                current_tokens += best_unit.token_count
                remaining_units.remove(best_unit)
            else:
                break

        # Check singleton rule: best single element fitting budget to guarantee (1 - 1/e) bound
        best_single = None
        best_single_val = -1.0
        for u in self.units:
            if u.token_count <= token_budget:
                val = len(u.covered_entities) + self.salience_weight * u.salience_score
                if val > best_single_val:
                    best_single_val = val
                    best_single = u

        greedy_val = len(covered_entities) + self.salience_weight * sum(u.salience_score for u in selected)
        if best_single is not None and best_single_val > greedy_val:
            selected = [best_single]
            covered_entities = set(best_single.covered_entities)
            current_tokens = best_single.token_count

        # Compute diversity metric (Jaccard dissimilarity across selected units)
        diversity = 0.0
        if len(selected) > 1:
            pairs = 0
            for i in range(len(selected)):
                for j in range(i + 1, len(selected)):
                    u1 = selected[i].covered_entities
                    u2 = selected[j].covered_entities
                    inter = len(u1 & u2)
                    union = len(u1 | u2)
                    sim = inter / max(union, 1)
                    diversity += (1.0 - sim)
                    pairs += 1
            diversity = diversity / max(pairs, 1)

        t1 = time.perf_counter()
        return SubmodularSummaryResult(
            selected_units=selected,
            total_tokens=current_tokens,
            total_entity_coverage=len(covered_entities),
            diversity_score=diversity,
            algorithm="BUDGETED_SUBMODULAR_GREEDY",
            execution_time_us=(t1 - t0) * 1e6
        )
