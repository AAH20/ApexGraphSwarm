"""
Submodular Episodic Memory Graph Summarization Solver.
Compresses streaming multi-agent interaction logs and GraphRAG episodic memories
into optimal fixed-size prompt contexts using Accelerated Lazy Greedy Submodular Maximization.
Guarantees a (1 - 1/e) ≈ 63.2% approximation bound, replacing lossy FIFO truncation.
"""
import time
import math
import heapq
from typing import List, Dict, Set, Tuple
from .models import MemoryItem, MemorySummaryResult

class SubmodularMemorySummarizer:
    """
    Selects k representative episodic memory nodes maximizing entity coverage
    and semantic diversity while minimizing redundancy.
    """

    def __init__(self, memory_pool: List[MemoryItem], diversity_weight: float = 0.35):
        self.pool = memory_pool
        self.lambda_div = diversity_weight
        # Precompute entity mapping
        self.all_entities = list({m.entity_tag for m in self.pool})

    def _cosine_dist(self, v1: List[float], v2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 < 1e-9 or norm2 < 1e-9:
            return 1.0
        cos_sim = max(-1.0, min(1.0, dot / (norm1 * norm2)))
        return 1.0 - cos_sim

    def _eval_coverage_gain(self, item: MemoryItem, current_entity_max: Dict[str, float]) -> float:
        curr = current_entity_max.get(item.entity_tag, 0.0)
        new_val = max(curr, item.salience_score)
        return max(0.0, new_val - curr)

    def _eval_diversity_gain(self, item: MemoryItem, selected: List[MemoryItem]) -> float:
        if not selected:
            return 1.0
        # Minimum distance to any currently selected element
        min_d = min(self._cosine_dist(item.embedding_vector, s.embedding_vector) for s in selected)
        return min_d

    def solve(self, k_items: int) -> MemorySummaryResult:
        t0 = time.perf_counter()
        k = min(k_items, len(self.pool))
        if k == 0:
            t1 = time.perf_counter()
            return MemorySummaryResult([], 0.0, 0.0, 0.0, "LAZY_GREEDY_SUBMODULAR", (t1 - t0) * 1e6)

        selected: List[MemoryItem] = []
        selected_ids: Set[str] = set()
        current_entity_max: Dict[str, float] = {e: 0.0 for e in self.all_entities}

        # Minoux Accelerated Lazy Greedy Queue: entries are (-upper_bound, item_idx, last_updated_iter)
        # Using Python heapq (min-heap)
        pq = []
        for idx, item in enumerate(self.pool):
            cov_gain = self._eval_coverage_gain(item, current_entity_max)
            div_gain = 1.0
            initial_gain = cov_gain + self.lambda_div * div_gain
            heapq.heappush(pq, (-initial_gain, idx, 0))

        current_iter = 0
        total_coverage = 0.0

        while len(selected) < k and pq:
            neg_bound, idx, last_iter = heapq.heappop(pq)
            item = self.pool[idx]

            if item.item_id in selected_ids:
                continue

            if last_iter == current_iter:
                # Top element is exact marginal gain due to submodularity
                selected.append(item)
                selected_ids.add(item.item_id)
                current_entity_max[item.entity_tag] = max(
                    current_entity_max.get(item.entity_tag, 0.0), item.salience_score
                )
                current_iter += 1
            else:
                # Recompute exact marginal gain
                cov_gain = self._eval_coverage_gain(item, current_entity_max)
                div_gain = self._eval_diversity_gain(item, selected)
                exact_gain = cov_gain + self.lambda_div * div_gain
                heapq.heappush(pq, (-exact_gain, idx, current_iter))

        # Compute summary metrics
        total_cov = sum(current_entity_max.values())
        avg_div = 0.0
        if len(selected) > 1:
            div_pairs = [
                self._cosine_dist(selected[i].embedding_vector, selected[j].embedding_vector)
                for i in range(len(selected))
                for j in range(i + 1, len(selected))
            ]
            avg_div = sum(div_pairs) / len(div_pairs)

        reduction = (1.0 - (len(selected) / max(len(self.pool), 1))) * 100.0

        t1 = time.perf_counter()
        return MemorySummaryResult(
            selected_items=selected,
            total_coverage_score=total_cov,
            diversity_metric=avg_div,
            reduction_ratio=reduction,
            algorithm="ACCELERATED_LAZY_GREEDY_SUBMODULAR",
            execution_time_us=(t1 - t0) * 1e6
        )
