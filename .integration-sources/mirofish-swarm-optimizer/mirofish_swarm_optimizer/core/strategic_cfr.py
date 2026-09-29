"""
Counterfactual Regret Matching (CFR) Strategic Policy Equilibrium Solver.
Solves imperfect-information game theoretic equilibria in MiroFish multi-agent simulations,
replacing heuristic/evolutionary drift with provably convergent Nash/Correlated equilibria.
"""
import time
from typing import List, Dict, Tuple
from .models import CFRResult

class StrategicCFRSolver:
    """
    Implements Counterfactual Regret Matching+ (CFR+) for strategic multi-agent bargaining,
    crises, and market manipulation simulations.
    """

    def __init__(
        self,
        player_a_name: str,
        player_b_name: str,
        actions_a: List[str],
        actions_b: List[str],
        payoff_matrix: Dict[Tuple[str, str], Tuple[float, float]]
    ):
        self.player_a = player_a_name
        self.player_b = player_b_name
        self.actions_a = actions_a
        self.actions_b = actions_b
        self.payoffs = payoff_matrix  # (act_a, act_b) -> (u_a, u_b)

        # Regret sum and strategy sum tables
        self.regret_sum_a = {a: 0.0 for a in actions_a}
        self.regret_sum_b = {b: 0.0 for b in actions_b}
        self.strategy_sum_a = {a: 0.0 for a in actions_a}
        self.strategy_sum_b = {b: 0.0 for b in actions_b}

    def _get_current_strategy(self, regret_sum: Dict[str, float], actions: List[str]) -> Dict[str, float]:
        positive_regrets = {a: max(regret_sum[a], 0.0) for a in actions}
        sum_pos = sum(positive_regrets.values())
        if sum_pos > 1e-12:
            return {a: positive_regrets[a] / sum_pos for a in actions}
        else:
            uniform = 1.0 / len(actions)
            return {a: uniform for a in actions}

    def solve(self, iterations: int = 1000) -> CFRResult:
        t0 = time.perf_counter()

        for t in range(1, iterations + 1):
            strat_a = self._get_current_strategy(self.regret_sum_a, self.actions_a)
            strat_b = self._get_current_strategy(self.regret_sum_b, self.actions_b)

            # Accumulate strategy sum
            for a in self.actions_a:
                self.strategy_sum_a[a] += strat_a[a]
            for b in self.actions_b:
                self.strategy_sum_b[b] += strat_b[b]

            # Compute expected utilities of pure actions against opponent's current strategy
            util_a_pure = {}
            for a in self.actions_a:
                u_a = sum(strat_b[b] * self.payoffs[(a, b)][0] for b in self.actions_b)
                util_a_pure[a] = u_a

            expected_u_a = sum(strat_a[a] * util_a_pure[a] for a in self.actions_a)

            util_b_pure = {}
            for b in self.actions_b:
                u_b = sum(strat_a[a] * self.payoffs[(a, b)][1] for a in self.actions_a)
                util_b_pure[b] = u_b

            expected_u_b = sum(strat_b[b] * util_b_pure[b] for b in self.actions_b)

            # Update regrets with CFR+ non-negative floor
            for a in self.actions_a:
                immediate_regret = util_a_pure[a] - expected_u_a
                self.regret_sum_a[a] = max(0.0, self.regret_sum_a[a] + immediate_regret)

            for b in self.actions_b:
                immediate_regret = util_b_pure[b] - expected_u_b
                self.regret_sum_b[b] = max(0.0, self.regret_sum_b[b] + immediate_regret)

        # Compute average strategy profile (Nash/CCE)
        tot_a = sum(self.strategy_sum_a.values())
        avg_strat_a = {a: (self.strategy_sum_a[a] / tot_a) for a in self.actions_a}

        tot_b = sum(self.strategy_sum_b.values())
        avg_strat_b = {b: (self.strategy_sum_b[b] / tot_b) for b in self.actions_b}

        # Calculate final expected payoffs
        payoff_a = 0.0
        payoff_b = 0.0
        for a in self.actions_a:
            for b in self.actions_b:
                joint_prob = avg_strat_a[a] * avg_strat_b[b]
                payoff_a += joint_prob * self.payoffs[(a, b)][0]
                payoff_b += joint_prob * self.payoffs[(a, b)][1]

        # Calculate exploitability (gap to best response)
        best_response_a = max(
            sum(avg_strat_b[b] * self.payoffs[(a, b)][0] for b in self.actions_b)
            for a in self.actions_a
        )
        best_response_b = max(
            sum(avg_strat_a[a] * self.payoffs[(a, b)][1] for a in self.actions_a)
            for b in self.actions_b
        )
        exploitability = (best_response_a - payoff_a) + (best_response_b - payoff_b)

        t1 = time.perf_counter()
        return CFRResult(
            equilibrium_strategies={
                self.player_a: avg_strat_a,
                self.player_b: avg_strat_b
            },
            expected_payoffs={
                self.player_a: payoff_a,
                self.player_b: payoff_b
            },
            iterations=iterations,
            exploitability=max(0.0, exploitability),
            algorithm="CFR_PLUS_STRATEGIC",
            execution_time_us=(t1 - t0) * 1e6
        )
