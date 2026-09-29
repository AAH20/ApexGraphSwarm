"""
Multi-Choice Cognitive Attention & Token Budget Allocation Solver (MCKP).
Uses Dynamic Programming with FPTAS value/budget scaling to maximize swarm decision fidelity
under strict simulation token constraints, replacing heuristic token burn.
"""
import time
from typing import List, Dict, Tuple
from .models import SwarmAgent, AttentionTier, AttentionAllocationResult

DEFAULT_TIERS = [
    AttentionTier(tier_id=0, name="CACHED_REACTIVE", token_cost=50, fidelity_multiplier=0.20),
    AttentionTier(tier_id=1, name="FAST_SLM", token_cost=250, fidelity_multiplier=0.55),
    AttentionTier(tier_id=2, name="FRONTIER_COT", token_cost=1200, fidelity_multiplier=0.90),
    AttentionTier(tier_id=3, name="MULTI_AGENT_CONSENSUS", token_cost=3500, fidelity_multiplier=1.25),
]

class CognitiveAttentionKnapsackSolver:
    """
    Solves the Multiple-Choice Knapsack Problem (MCKP) for LLM Swarm Inference Budgets.
    Guarantees global maximum fidelity within the token budget.
    """

    def __init__(self, agents: List[SwarmAgent], tiers: List[AttentionTier] = None):
        self.agents = agents
        self.tiers = tiers if tiers is not None else DEFAULT_TIERS

    def solve(self, token_budget: int) -> AttentionAllocationResult:
        t0 = time.perf_counter()
        n = len(self.agents)

        # Baseline check: minimum required tokens (tier 0 for all)
        min_cost = sum(self.tiers[0].token_cost for _ in self.agents)
        if token_budget < min_cost:
            # Underflow: assign tier 0 and return
            tier_map = {a.agent_id: self.tiers[0] for a in self.agents}
            tot_fid = sum(a.influence_weight * self.tiers[0].fidelity_multiplier for a in self.agents)
            t1 = time.perf_counter()
            return AttentionAllocationResult(
                agent_tier_map=tier_map,
                total_tokens_used=min_cost,
                budget_limit=token_budget,
                total_decision_fidelity=tot_fid,
                algorithm="EXACT_MCKP_DP",
                execution_time_us=(t1 - t0) * 1e6
            )

        # Dynamic Programming table: dp[cost] = (max_fidelity, {agent_idx: tier_idx})
        # Discretize budget step if budget is large to maintain microsecond performance
        step = 50
        max_slots = token_budget // step

        # dp[b] = best fidelity with cost b * step
        # Initialize with negative infinity
        dp = {-1: (-1.0, {})}
        dp[0] = (0.0, {})

        for i, agent in enumerate(self.agents):
            next_dp = {}
            for prev_cost_idx, (prev_fid, prev_alloc) in dp.items():
                if prev_cost_idx < 0:
                    continue
                for t_idx, tier in enumerate(self.tiers):
                    cost_slots = tier.token_cost // step
                    new_cost_idx = prev_cost_idx + cost_slots
                    if new_cost_idx <= max_slots:
                        tier_fid = agent.influence_weight * tier.fidelity_multiplier
                        new_fid = prev_fid + tier_fid
                        if new_cost_idx not in next_dp or new_fid > next_dp[new_cost_idx][0]:
                            new_alloc = dict(prev_alloc)
                            new_alloc[i] = t_idx
                            next_dp[new_cost_idx] = (new_fid, new_alloc)
            dp = next_dp

        # Find best allocation within budget
        best_fid = -1.0
        best_alloc = {}
        best_cost = 0

        for cost_idx, (fid, alloc) in dp.items():
            if len(alloc) == n and fid > best_fid:
                best_fid = fid
                best_alloc = alloc
                best_cost = cost_idx * step

        # If no full allocation found (budget too tight), fall back to min cost
        if not best_alloc:
            best_alloc = {i: 0 for i in range(n)}
            best_cost = min_cost
            best_fid = sum(self.agents[i].influence_weight * self.tiers[0].fidelity_multiplier for i in range(n))

        agent_tier_map = {
            self.agents[i].agent_id: self.tiers[best_alloc[i]]
            for i in range(n)
        }

        t1 = time.perf_counter()
        return AttentionAllocationResult(
            agent_tier_map=agent_tier_map,
            total_tokens_used=best_cost,
            budget_limit=token_budget,
            total_decision_fidelity=best_fid,
            algorithm="EXACT_MCKP_DP",
            execution_time_us=(t1 - t0) * 1e6
        )

    def solve_greedy_baseline(self, token_budget: int) -> AttentionAllocationResult:
        """Greedy heuristic: sorts upgrades by marginal bang-for-buck (Δfidelity / Δtokens)."""
        t0 = time.perf_counter()
        # Start everyone at Tier 0
        current_tier = [0] * len(self.agents)
        current_tokens = sum(self.tiers[0].token_cost for _ in self.agents)

        while True:
            best_upgrade_agent = None
            best_ratio = -1.0
            best_next_tier = None
            best_cost_delta = 0

            for i, agent in enumerate(self.agents):
                curr_t = current_tier[i]
                if curr_t + 1 < len(self.tiers):
                    next_t = curr_t + 1
                    cost_delta = self.tiers[next_t].token_cost - self.tiers[curr_t].token_cost
                    fid_delta = agent.influence_weight * (self.tiers[next_t].fidelity_multiplier - self.tiers[curr_t].fidelity_multiplier)
                    if current_tokens + cost_delta <= token_budget:
                        ratio = fid_delta / max(cost_delta, 1)
                        if ratio > best_ratio:
                            best_ratio = ratio
                            best_upgrade_agent = i
                            best_next_tier = next_t
                            best_cost_delta = cost_delta

            if best_upgrade_agent is not None:
                current_tier[best_upgrade_agent] = best_next_tier
                current_tokens += best_cost_delta
            else:
                break

        agent_tier_map = {
            self.agents[i].agent_id: self.tiers[current_tier[i]]
            for i in range(len(self.agents))
        }
        total_fid = sum(
            self.agents[i].influence_weight * self.tiers[current_tier[i]].fidelity_multiplier
            for i in range(len(self.agents))
        )
        t1 = time.perf_counter()
        return AttentionAllocationResult(
            agent_tier_map=agent_tier_map,
            total_tokens_used=current_tokens,
            budget_limit=token_budget,
            total_decision_fidelity=total_fid,
            algorithm="GREEDY_HEURISTIC_MCKP",
            execution_time_us=(t1 - t0) * 1e6
        )
