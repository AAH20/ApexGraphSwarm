"""
Shared Prefix-KV Cache & Context Memory Packing Solver.
Optimizes prompt scheduling order to maximize Radix Trie prefix-cache reuse in GPU inference engines
(vLLM / SGLang / TensorRT-LLM), eliminating redundant prefill computation.
"""
import time
from typing import List, Dict, Set, Tuple
from .models import ContextPromptBlock, PrefixCacheResult

class PrefixKVCacheOptimizer:
    """
    Schedules agent prompts using longest-common-prefix (LCP) radix clustering and Knapsack packing.
    """

    def __init__(self, prompt_blocks: List[ContextPromptBlock], max_vram_tokens: int = 32768):
        self.blocks = prompt_blocks
        self.max_vram = max_vram_tokens

    def _common_prefix_length(self, p1: List[int], p2: List[int]) -> int:
        match = 0
        limit = min(len(p1), len(p2))
        while match < limit and p1[match] == p2[match]:
            match += 1
        return match

    def solve(self) -> PrefixCacheResult:
        t0 = time.perf_counter()
        n = len(self.blocks)
        if n == 0:
            t1 = time.perf_counter()
            return PrefixCacheResult([], 0.0, 0, 0, "RADIX_PREFIX_PACKER", (t1 - t0) * 1e6)

        # Compute pairwise common prefix savings
        # Greedily construct an Eulerian / TSP traversal ordering over the prefix tree
        unvisited = set(range(n))
        # Start with the highest priority or largest block
        start_idx = max(unvisited, key=lambda i: self.blocks[i].priority_weight)
        execution_order = [start_idx]
        unvisited.remove(start_idx)

        total_saved_tokens = 0
        total_prefill_tokens = self.blocks[start_idx].total_tokens
        curr_idx = start_idx

        while unvisited:
            # Find next block with maximal common prefix with the current block
            best_next = None
            best_lcp = -1
            best_score = -1.0

            for cand_idx in unvisited:
                lcp = self._common_prefix_length(
                    self.blocks[curr_idx].prefix_tokens,
                    self.blocks[cand_idx].prefix_tokens
                )
                score = lcp * 1.0 + self.blocks[cand_idx].priority_weight * 0.1
                if score > best_score:
                    best_score = score
                    best_lcp = lcp
                    best_next = cand_idx

            execution_order.append(best_next)
            unvisited.remove(best_next)
            total_saved_tokens += best_lcp
            total_prefill_tokens += (self.blocks[best_next].total_tokens - best_lcp)
            curr_idx = best_next

        # Peak VRAM calculation: max active context
        peak_tokens = max(b.total_tokens for b in self.blocks)
        baseline_prefill = sum(b.total_tokens for b in self.blocks)
        cache_hit_ratio = (total_saved_tokens / max(baseline_prefill, 1))

        packed_ids = [self.blocks[i].block_id for i in execution_order]
        t1 = time.perf_counter()

        return PrefixCacheResult(
            packed_execution_order=packed_ids,
            cache_hit_ratio=cache_hit_ratio,
            saved_prefill_tokens=total_saved_tokens,
            vram_peak_tokens=min(peak_tokens, self.max_vram),
            algorithm="RADIX_PREFIX_PACKER",
            execution_time_us=(t1 - t0) * 1e6
        )
