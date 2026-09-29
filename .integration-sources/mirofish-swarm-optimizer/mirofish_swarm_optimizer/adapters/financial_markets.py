"""Financial Market Microstructure & Emergent Price Discovery Adapter."""
from typing import List, Dict, Tuple, Any
from ..core.models import SwarmAgent, AgentFaction
from ..core.coalition_structure import OptimalCoalitionStructureSolver
from ..core.influence_maximizer import InfluenceMaximizer
from ..core.kemeny_consensus import KemenyConsensusSolver
from ..core.topology_sparsifier import TopologySparsifier
from ..core.evolutionary_baselines import GeneticAlgorithmCSG, ParticleSwarmInfluenceMaximizer

def build_financial_agents() -> List[SwarmAgent]:
    """8 Market Participants with 3D profile: [Risk Appetite, Time Horizon, Directional Bias]."""
    return [
        SwarmAgent("MM-CITADEL", "Primary Market Maker A", AgentFaction.INSTITUTIONAL_CAPITAL, 9.8, [-0.9, -0.95, 0.0]),
        SwarmAgent("MM-VIRTU", "Primary Market Maker B", AgentFaction.INSTITUTIONAL_CAPITAL, 9.5, [-0.85, -0.90, 0.05]),
        SwarmAgent("HF-QUANT", "Statistical Arbitrage Hedge Fund", AgentFaction.INSTITUTIONAL_CAPITAL, 8.5, [0.7, -0.6, 0.3]),
        SwarmAgent("CTA-MOMENTUM", "Trend Following Commodity Fund", AgentFaction.INSTITUTIONAL_CAPITAL, 7.8, [0.8, 0.4, 0.7]),
        SwarmAgent("PENSION-LONG", "Sovereign Pension Asset Manager", AgentFaction.INSTITUTIONAL_CAPITAL, 9.0, [-0.4, 0.95, 0.5]),
        SwarmAgent("RETAIL-SWARM", "Retail Momentum Social Swarm", AgentFaction.PUBLIC_OPINION_BLOC, 6.5, [0.95, -0.8, 0.9]),
        SwarmAgent("CENTRAL-BANK", "Central Bank Open Market Desk", AgentFaction.REGULATORY_BODY, 9.9, [-0.9, 0.5, -0.1]),
        SwarmAgent("CORP-HEDGER", "Multinational Corporate Hedger", AgentFaction.SOVEREIGN_STATE, 7.2, [-0.5, 0.6, -0.3]),
    ]

def build_financial_liquidity_network() -> Dict[str, List[Tuple[str, float]]]:
    """Inter-dealer liquidity routes and information spillover probabilities."""
    return {
        "MM-CITADEL": [("MM-VIRTU", 0.90), ("HF-QUANT", 0.75), ("RETAIL-SWARM", 0.85)],
        "MM-VIRTU": [("MM-CITADEL", 0.90), ("HF-QUANT", 0.70), ("CORP-HEDGER", 0.60)],
        "HF-QUANT": [("CTA-MOMENTUM", 0.65), ("MM-CITADEL", 0.70), ("RETAIL-SWARM", 0.60)],
        "CTA-MOMENTUM": [("RETAIL-SWARM", 0.80), ("HF-QUANT", 0.55)],
        "PENSION-LONG": [("CORP-HEDGER", 0.50), ("CENTRAL-BANK", 0.60), ("MM-CITADEL", 0.40)],
        "RETAIL-SWARM": [("CTA-MOMENTUM", 0.70), ("HF-QUANT", 0.50)],
        "CENTRAL-BANK": [("MM-CITADEL", 0.95), ("MM-VIRTU", 0.95), ("PENSION-LONG", 0.75)],
        "CORP-HEDGER": [("MM-CITADEL", 0.70), ("PENSION-LONG", 0.60)]
    }

def run_financial_benchmark() -> Dict[str, Any]:
    agents = build_financial_agents()
    network = build_financial_liquidity_network()

    # 1. Coalition Structure Generation: Market Maker Liquidity Syndicate
    csg_solver = OptimalCoalitionStructureSolver(agents)
    res_csg_exact = csg_solver.solve()

    ga_solver = GeneticAlgorithmCSG(agents, population_size=35, generations=50)
    res_csg_ga = ga_solver.solve()

    # 2. Influence Maximization: Critical Tipping Points for Liquidity Flash-Cracks
    inf_solver = InfluenceMaximizer(agents, network)
    res_inf_exact = inf_solver.solve(k_seeds=2, num_samples=1500)

    pso_solver = ParticleSwarmInfluenceMaximizer(agents, network, swarm_size=20, iterations=30)
    res_inf_pso = pso_solver.solve(k_seeds=2)

    # 3. Kemeny Consensus on 4 Asset Price Regimes
    regimes = ["REGIME-BULL-BREAKOUT", "REGIME-RANGEBOUND-CHOP", "REGIME-LIQUIDITY-SQUEEZE", "REGIME-FLASH-CORRECTION"]
    order_flow_rankings = [
        ["REGIME-RANGEBOUND-CHOP", "REGIME-BULL-BREAKOUT", "REGIME-LIQUIDITY-SQUEEZE", "REGIME-FLASH-CORRECTION"], # MM Citadel
        ["REGIME-RANGEBOUND-CHOP", "REGIME-BULL-BREAKOUT", "REGIME-FLASH-CORRECTION", "REGIME-LIQUIDITY-SQUEEZE"], # MM Virtu
        ["REGIME-LIQUIDITY-SQUEEZE", "REGIME-BULL-BREAKOUT", "REGIME-FLASH-CORRECTION", "REGIME-RANGEBOUND-CHOP"], # Quant
        ["REGIME-BULL-BREAKOUT", "REGIME-LIQUIDITY-SQUEEZE", "REGIME-RANGEBOUND-CHOP", "REGIME-FLASH-CORRECTION"], # CTA
        ["REGIME-BULL-BREAKOUT", "REGIME-RANGEBOUND-CHOP", "REGIME-FLASH-CORRECTION", "REGIME-LIQUIDITY-SQUEEZE"], # Pension
        ["REGIME-BULL-BREAKOUT", "REGIME-LIQUIDITY-SQUEEZE", "REGIME-RANGEBOUND-CHOP", "REGIME-FLASH-CORRECTION"], # Retail
        ["REGIME-RANGEBOUND-CHOP", "REGIME-BULL-BREAKOUT", "REGIME-FLASH-CORRECTION", "REGIME-LIQUIDITY-SQUEEZE"], # Central Bank
        ["REGIME-RANGEBOUND-CHOP", "REGIME-FLASH-CORRECTION", "REGIME-BULL-BREAKOUT", "REGIME-LIQUIDITY-SQUEEZE"], # Corp Hedger
    ]
    kemeny_solver = KemenyConsensusSolver(regimes)
    res_kemeny = kemeny_solver.solve(order_flow_rankings)

    # 4. Topology Sparsifier
    top_sparsifier = TopologySparsifier(agents)
    res_top = top_sparsifier.sparsify(max_degree=3)

    return {
        "csg_comparison": {
            "exact": res_csg_exact,
            "ga": res_csg_ga,
            "welfare_gain_pct": ((res_csg_exact.total_welfare - res_csg_ga.total_welfare) / res_csg_ga.total_welfare) * 100.0,
            "speedup_factor": res_csg_ga.execution_time_us / max(1.0, res_csg_exact.execution_time_us)
        },
        "influence_comparison": {
            "exact_sketch": res_inf_exact,
            "pso": res_inf_pso,
            "reach_advantage_pct": ((res_inf_exact.expected_reach - res_inf_pso.expected_reach) / max(0.1, res_inf_pso.expected_reach)) * 100.0,
            "speedup_factor": res_inf_pso.execution_time_us / max(1.0, res_inf_exact.execution_time_us)
        },
        "kemeny_consensus": res_kemeny,
        "topology_sparsification": res_top
    }
