"""Geopolitical Crisis & Multilateral Alliance Prediction Adapter."""
from typing import List, Dict, Tuple, Any
from ..core.models import SwarmAgent, AgentFaction
from ..core.coalition_structure import OptimalCoalitionStructureSolver
from ..core.influence_maximizer import InfluenceMaximizer
from ..core.kemeny_consensus import KemenyConsensusSolver
from ..core.topology_sparsifier import TopologySparsifier
from ..core.evolutionary_baselines import GeneticAlgorithmCSG, ParticleSwarmInfluenceMaximizer

def build_geopolitical_agents() -> List[SwarmAgent]:
    """10 Geopolitical Actors with 3D stance: [Security Autonomy, Green Transition, Market Openness]."""
    return [
        SwarmAgent("STATE-US", "United States", AgentFaction.SOVEREIGN_STATE, 9.5, [0.8, 0.4, 0.9]),
        SwarmAgent("STATE-EU", "European Union", AgentFaction.SOVEREIGN_STATE, 8.8, [0.3, 0.9, 0.7]),
        SwarmAgent("STATE-CN", "China", AgentFaction.SOVEREIGN_STATE, 9.2, [0.9, 0.6, -0.2]),
        SwarmAgent("STATE-IN", "India", AgentFaction.SOVEREIGN_STATE, 7.8, [0.7, 0.3, 0.3]),
        SwarmAgent("STATE-BR", "Brazil", AgentFaction.SOVEREIGN_STATE, 6.0, [0.2, 0.7, 0.4]),
        SwarmAgent("ENERGY-OPEC", "OPEC Bloc", AgentFaction.INSTITUTIONAL_CAPITAL, 7.5, [0.5, -0.8, 0.2]),
        SwarmAgent("TECH-HEGEMON", "Global Tech Consortium", AgentFaction.INSTITUTIONAL_CAPITAL, 8.2, [-0.4, 0.5, 0.95]),
        SwarmAgent("PUBLIC-MEDIA", "Global Media Syndicate", AgentFaction.MEDIA_INFLUENCER, 6.5, [-0.2, 0.8, 0.6]),
        SwarmAgent("REG-UN", "UN Treaty Secretariat", AgentFaction.REGULATORY_BODY, 5.0, [-0.1, 0.9, 0.1]),
        SwarmAgent("SWING-GULF", "Gulf Sovereign Funds", AgentFaction.INSTITUTIONAL_CAPITAL, 7.0, [0.4, -0.2, 0.85]),
    ]

def build_geopolitical_influence_network() -> Dict[str, List[Tuple[str, float]]]:
    """Diplomatic backchannels and bilateral influence probabilities."""
    return {
        "STATE-US": [("STATE-EU", 0.75), ("TECH-HEGEMON", 0.80), ("SWING-GULF", 0.65), ("PUBLIC-MEDIA", 0.60)],
        "STATE-EU": [("STATE-US", 0.70), ("REG-UN", 0.85), ("PUBLIC-MEDIA", 0.75), ("STATE-BR", 0.50)],
        "STATE-CN": [("ENERGY-OPEC", 0.80), ("STATE-IN", 0.40), ("STATE-BR", 0.70), ("SWING-GULF", 0.60)],
        "STATE-IN": [("STATE-US", 0.55), ("STATE-CN", 0.45), ("ENERGY-OPEC", 0.60)],
        "STATE-BR": [("STATE-EU", 0.55), ("STATE-CN", 0.65), ("REG-UN", 0.50)],
        "ENERGY-OPEC": [("SWING-GULF", 0.90), ("STATE-CN", 0.70), ("STATE-IN", 0.65)],
        "TECH-HEGEMON": [("STATE-US", 0.75), ("PUBLIC-MEDIA", 0.85), ("STATE-EU", 0.60)],
        "PUBLIC-MEDIA": [("STATE-EU", 0.70), ("STATE-US", 0.65), ("REG-UN", 0.60)],
        "REG-UN": [("STATE-EU", 0.70), ("STATE-BR", 0.60)],
        "SWING-GULF": [("STATE-US", 0.65), ("STATE-CN", 0.65), ("ENERGY-OPEC", 0.85)]
    }

def run_geopolitical_benchmark() -> Dict[str, Any]:
    agents = build_geopolitical_agents()
    network = build_geopolitical_influence_network()

    # 1. Coalition Structure Generation Benchmark: Exact IDP vs Genetic Algorithm
    csg_solver = OptimalCoalitionStructureSolver(agents)
    res_csg_exact = csg_solver.solve()

    ga_solver = GeneticAlgorithmCSG(agents, population_size=40, generations=60)
    res_csg_ga = ga_solver.solve()

    # 2. Influence Maximization Benchmark: Martingale RR-Sketch vs PSO
    inf_solver = InfluenceMaximizer(agents, network)
    res_inf_exact = inf_solver.solve(k_seeds=2, num_samples=1500)

    pso_solver = ParticleSwarmInfluenceMaximizer(agents, network, swarm_size=25, iterations=35)
    res_inf_pso = pso_solver.solve(k_seeds=2)

    # 3. Kemeny Consensus on 4 Treaty Outcomes:
    outcomes = ["TREATY-CARBON-TAX", "TREATY-STATUS-QUO", "TREATY-TARIFF-WALL", "TREATY-MINILATERAL-TECH"]
    # Agent preferences
    preferences = [
        ["TREATY-MINILATERAL-TECH", "TREATY-STATUS-QUO", "TREATY-CARBON-TAX", "TREATY-TARIFF-WALL"], # US
        ["TREATY-CARBON-TAX", "TREATY-MINILATERAL-TECH", "TREATY-STATUS-QUO", "TREATY-TARIFF-WALL"], # EU
        ["TREATY-STATUS-QUO", "TREATY-TARIFF-WALL", "TREATY-MINILATERAL-TECH", "TREATY-CARBON-TAX"], # CN
        ["TREATY-STATUS-QUO", "TREATY-MINILATERAL-TECH", "TREATY-CARBON-TAX", "TREATY-TARIFF-WALL"], # IN
        ["TREATY-CARBON-TAX", "TREATY-STATUS-QUO", "TREATY-TARIFF-WALL", "TREATY-MINILATERAL-TECH"], # BR
        ["TREATY-STATUS-QUO", "TREATY-TARIFF-WALL", "TREATY-MINILATERAL-TECH", "TREATY-CARBON-TAX"], # OPEC
        ["TREATY-MINILATERAL-TECH", "TREATY-CARBON-TAX", "TREATY-STATUS-QUO", "TREATY-TARIFF-WALL"], # TECH
        ["TREATY-CARBON-TAX", "TREATY-MINILATERAL-TECH", "TREATY-STATUS-QUO", "TREATY-TARIFF-WALL"], # MEDIA
        ["TREATY-CARBON-TAX", "TREATY-STATUS-QUO", "TREATY-MINILATERAL-TECH", "TREATY-TARIFF-WALL"], # UN
        ["TREATY-MINILATERAL-TECH", "TREATY-STATUS-QUO", "TREATY-TARIFF-WALL", "TREATY-CARBON-TAX"], # GULF
    ]
    kemeny_solver = KemenyConsensusSolver(outcomes)
    res_kemeny = kemeny_solver.solve(preferences)

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
