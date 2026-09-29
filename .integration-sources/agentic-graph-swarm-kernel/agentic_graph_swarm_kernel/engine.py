"""Unified Engine for the 10 Apex NP-Hard Problems in Agentic Graph Engineering and Swarm Orchestration."""
import time
from typing import Dict, Any, List, Tuple

from .core.models import (
    AgentProfile,
    KnowledgeHyperedge,
    VariableObservation,
    FactStatement,
    AgentBeliefGraph,
    KnowledgeNode,
    AgentContextBudget,
    MemoryNode,
    MemoryEdge,
    AgentToolTask,
    ToolResource,
    AgentClaim,
    BehaviorPattern,
    TemporalEvent,
    PlayerAgent,
    HyperedgePayoff,
)

from .core.hypergraph_csg import solve_hypergraph_csg
from .core.causal_dag_synthesis import solve_causal_dag_synthesis
from .core.epistemic_consensus import solve_epistemic_consensus
from .core.budgeted_attention_routing import solve_budgeted_attention_routing
from .core.spectral_memory_decay import solve_spectral_memory_decay
from .core.disjunctive_tool_scheduler import solve_disjunctive_tool_scheduling
from .core.byzantine_epistemic_filter import solve_byzantine_truth_discovery
from .core.graph_grammar_evolution import solve_graph_grammar_evolution
from .core.temporal_subgraph_detector import solve_temporal_subgraph_detection
from .core.game_theoretic_hypergraph_nash import solve_pareto_game_hypergraph

from .adapters.digital_world_simulator import DigitalWorldSimulatorAdapter
from .adapters.enterprise_agentic_mesh import EnterpriseAgenticMeshAdapter


class AgenticGraphSwarmEngine:
    """Unified engine coordinating NP-hard solvers across Agentic Graphs and Swarm Orchestration."""

    def __init__(self):
        self.world_simulator = DigitalWorldSimulatorAdapter()
        self.enterprise_mesh = EnterpriseAgenticMeshAdapter()

    # --- Core Direct Solvers ---
    solve_csg = staticmethod(solve_hypergraph_csg)
    solve_causal_dag = staticmethod(solve_causal_dag_synthesis)
    solve_consensus = staticmethod(solve_epistemic_consensus)
    solve_attention = staticmethod(solve_budgeted_attention_routing)
    solve_memory_decay = staticmethod(solve_spectral_memory_decay)
    solve_tool_scheduler = staticmethod(solve_disjunctive_tool_scheduling)
    solve_truth_discovery = staticmethod(solve_byzantine_truth_discovery)
    solve_topology_evolution = staticmethod(solve_graph_grammar_evolution)
    solve_temporal_pattern = staticmethod(solve_temporal_subgraph_detection)
    solve_pareto_game = staticmethod(solve_pareto_game_hypergraph)

    @staticmethod
    def generate_synthetic_benchmark_suite() -> Dict[str, Any]:
        """Generates realistic synthetic benchmark problem instances for all 10 NP-hard challenges."""
        # 1. Hypergraph CSG: 8 agents across 4 multi-capability hyperedges
        agents = [
            AgentProfile("ag_1", ["Code", "GraphSearch"], efficiency_weight=1.2),
            AgentProfile("ag_2", ["DataViz", "NLP"], efficiency_weight=1.0),
            AgentProfile("ag_3", ["FormalVerification", "Math"], efficiency_weight=1.5),
            AgentProfile("ag_4", ["WebScrape", "Code"], efficiency_weight=0.9),
            AgentProfile("ag_5", ["NLP", "Math"], efficiency_weight=1.1),
            AgentProfile("ag_6", ["GraphSearch", "FormalVerification"], efficiency_weight=1.3),
        ]
        hyperedges = [
            KnowledgeHyperedge("h_1", "AlgorithmicSynthesis", ["Code", "FormalVerification", "Math"], value=100.0),
            KnowledgeHyperedge("h_2", "MarketIntelligence", ["WebScrape", "NLP", "DataViz"], value=70.0),
            KnowledgeHyperedge("h_3", "GraphAnalysis", ["GraphSearch", "Code"], value=50.0),
        ]

        # 2. Causal DAG: 4 financial/economic variables
        vars_obs = [
            VariableObservation("interest_rate", "InterestRate", [0.05 + 0.01 * (i % 5) for i in range(50)]),
            VariableObservation("inflation", "Inflation", [0.03 + 0.008 * (i % 6) for i in range(50)]),
            VariableObservation("stock_index", "StockIndex", [5000.0 - 50.0 * (i % 5) for i in range(50)]),
            VariableObservation("consumer_spend", "ConsumerSpending", [100.0 - 2.0 * (i % 4) for i in range(50)]),
        ]

        # 3. Epistemic Consensus: 3 agents with conflicting statements
        belief_graphs = [
            AgentBeliefGraph("agent_alpha", 0.9, [
                FactStatement("Entity_A", "acquired", "Entity_B", 0.85),
                FactStatement("Entity_C", "launched", "Product_X", 0.90),
            ]),
            AgentBeliefGraph("agent_beta", 0.6, [
                FactStatement("Entity_A", "acquired", "Entity_D", 0.70),  # Conflict!
                FactStatement("Entity_C", "launched", "Product_X", 0.80),
            ]),
        ]

        # 4. Attention Routing: 6 nodes and 2 agents
        nodes = [
            KnowledgeNode("k_1", 500, 4.5, {"FinTech", "Regulation"}),
            KnowledgeNode("k_2", 800, 6.2, {"Cryptocurrency", "ZeroKnowledge"}),
            KnowledgeNode("k_3", 300, 3.1, {"FinTech", "Banking"}),
            KnowledgeNode("k_4", 600, 5.0, {"Security", "ZeroKnowledge"}),
        ]
        budgets = [
            AgentContextBudget("ag_fin", 1000, {"FinTech", "Banking"}),
            AgentContextBudget("ag_sec", 1200, {"Security", "ZeroKnowledge"}),
        ]

        # 5. Memory Decay: 6 nodes and 6 edges
        mem_nodes = [
            MemoryNode(f"mem_{i}", timestamp=10000.0 - i * 1000.0, access_count=10 - i)
            for i in range(6)
        ]
        mem_edges = [
            MemoryEdge("mem_0", "mem_1", 0.9, 1.0),
            MemoryEdge("mem_1", "mem_2", 0.8, 1.2),
            MemoryEdge("mem_2", "mem_3", 0.6, 1.5),
            MemoryEdge("mem_3", "mem_4", 0.4, 2.0),
            MemoryEdge("mem_0", "mem_4", 0.5, 1.8),
            MemoryEdge("mem_4", "mem_5", 0.3, 2.5),
        ]

        # 6. Tool Scheduling: 4 tasks and 2 resources
        tool_tasks = [
            AgentToolTask("t_1", "ag_1", "res_browser", 30),
            AgentToolTask("t_2", "ag_2", "res_code", 40),
            AgentToolTask("t_3", "ag_1", "res_code", 25, precedence_prereqs=["t_1"]),
            AgentToolTask("t_4", "ag_3", "res_browser", 20),
        ]
        resources = [ToolResource("res_browser", 1), ToolResource("res_code", 1)]

        # 7. Byzantine Truth: 6 claims including false claims by a poisoned agent
        claims = [
            AgentClaim("c_1", "ag_truth_1", "Company_X", "revenue", "$10B", 100.0),
            AgentClaim("c_2", "ag_truth_2", "Company_X", "revenue", "$10B", 101.0),
            AgentClaim("c_3", "ag_byzantine", "Company_X", "revenue", "$100M", 102.0),  # Poison!
            AgentClaim("c_4", "ag_truth_1", "Company_X", "status", "Solvent", 105.0),
            AgentClaim("c_5", "ag_truth_2", "Company_X", "status", "Solvent", 106.0),
            AgentClaim("c_6", "ag_byzantine", "Company_X", "status", "Bankrupt", 107.0), # Poison!
        ]

        # 8. Topology Evolution: 6 agents
        agent_names = [f"worker_{i}" for i in range(6)]

        # 9. Temporal Pattern: 6 events
        events = [
            TemporalEvent("ev_1", "ag_1", "ag_2", "QueryPrice", 1.0),
            TemporalEvent("ev_2", "ag_2", "ag_3", "AuditBook", 3.0),
            TemporalEvent("ev_3", "ag_3", "ag_1", "ExecuteSell", 6.0),
            TemporalEvent("ev_4", "ag_4", "ag_5", "QueryPrice", 10.0),
            TemporalEvent("ev_5", "ag_5", "ag_6", "AuditBook", 12.0),
            TemporalEvent("ev_6", "ag_6", "ag_4", "ExecuteSell", 14.0),
        ]
        pattern = BehaviorPattern("pat_arbitrage", ["QueryPrice", "AuditBook", "ExecuteSell"], max_delta_time=5.0)

        # 10. Pareto Game: 2 players on 1 hyperedge
        players = [
            PlayerAgent("trader_A", ["BidHigh", "BidLow"]),
            PlayerAgent("trader_B", ["SellHigh", "SellLow"]),
        ]
        payoffs = [
            HyperedgePayoff("he_market", ["trader_A", "trader_B"], {
                ("BidHigh", "SellHigh"): {"trader_A": 5.0, "trader_B": 10.0},
                ("BidHigh", "SellLow"): {"trader_A": 8.0, "trader_B": 4.0},
                ("BidLow", "SellHigh"): {"trader_A": 0.0, "trader_B": 0.0},
                ("BidLow", "SellLow"): {"trader_A": 6.0, "trader_B": 6.0},
            })
        ]

        return {
            "p1_csg": (agents, hyperedges),
            "p2_causal": (vars_obs, 2),
            "p3_consensus": belief_graphs,
            "p4_attention": (nodes, budgets),
            "p5_memory": (mem_nodes, mem_edges, 0.6),
            "p6_tool": (tool_tasks, resources),
            "p7_byzantine": claims,
            "p8_topology": (agent_names, 10, 10, 42),
            "p9_temporal": (events, pattern),
            "p10_game": (players, payoffs, 30),
        }

    def benchmark_all_10(self) -> Dict[str, Any]:
        """Executes and benchmarks all 10 NP-hard Agentic Graph Swarm solvers in a single run."""
        suite = self.generate_synthetic_benchmark_suite()
        t_start_total = time.perf_counter()

        res_p1 = self.solve_csg(*suite["p1_csg"])
        res_p2 = self.solve_causal_dag(*suite["p2_causal"])
        res_p3 = self.solve_consensus(suite["p3_consensus"])
        res_p4 = self.solve_attention(*suite["p4_attention"])
        res_p5 = self.solve_memory_decay(*suite["p5_memory"])
        res_p6 = self.solve_tool_scheduler(*suite["p6_tool"])
        res_p7 = self.solve_truth_discovery(suite["p7_byzantine"])
        res_p8 = self.solve_topology_evolution(*suite["p8_topology"])
        res_p9 = self.solve_temporal_pattern(*suite["p9_temporal"])
        res_p10 = self.solve_pareto_game(*suite["p10_game"])

        t_end_total = time.perf_counter()
        total_time_us = (t_end_total - t_start_total) * 1_000_000.0

        return {
            "total_benchmark_time_us": round(total_time_us, 2),
            "solvers": {
                "P1_Hypergraph_CSG": {
                    "coalitions": len(res_p1.coalitions),
                    "value": res_p1.total_coalition_value,
                    "time_us": res_p1.execution_time_us,
                },
                "P2_Causal_DAG_Synthesis": {
                    "bic_score": res_p2.bic_score,
                    "is_acyclic": res_p2.is_acyclic,
                    "time_us": res_p2.execution_time_us,
                },
                "P3_Epistemic_Consensus": {
                    "statements": len(res_p3.consensus_graph),
                    "kemeny_dist": res_p3.kemeny_distance,
                    "time_us": res_p3.execution_time_us,
                },
                "P4_Attention_Routing": {
                    "info_coverage": res_p4.total_information_coverage,
                    "utilization": res_p4.context_utilization_pct,
                    "time_us": res_p4.execution_time_us,
                },
                "P5_Spectral_Memory_Decay": {
                    "compression": res_p5.spectral_compression_ratio,
                    "retained_nodes": len(res_p5.retained_nodes),
                    "time_us": res_p5.execution_time_us,
                },
                "P6_Disjunctive_Tool_Scheduler": {
                    "makespan_ms": res_p6.makespan_ms,
                    "deadlock_free": res_p6.deadlock_free_certified,
                    "time_us": res_p6.execution_time_us,
                },
                "P7_Byzantine_Truth_Discovery": {
                    "resolved_attrs": len(res_p7.resolved_attributes),
                    "quarantined": len(res_p7.quarantined_byzantine_agents),
                    "time_us": res_p7.execution_time_us,
                },
                "P8_Topology_Evolution_EAS": {
                    "pareto_size": res_p8.pareto_frontier_size,
                    "fitness": res_p8.best_fitness,
                    "time_us": res_p8.execution_time_us,
                },
                "P9_Temporal_Pattern_Matching": {
                    "detections": res_p9.total_detections,
                    "causality_ok": res_p9.causality_strictly_ordered,
                    "time_us": res_p9.execution_time_us,
                },
                "P10_Pareto_Hypergraph_Nash": {
                    "welfare": res_p10.expected_social_welfare,
                    "pareto_ok": res_p10.pareto_efficient,
                    "time_us": res_p10.execution_time_us,
                },
            }
        }
