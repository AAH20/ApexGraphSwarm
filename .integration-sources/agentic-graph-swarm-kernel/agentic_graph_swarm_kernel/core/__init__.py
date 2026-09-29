"""Core algorithms and models for the 10 Apex NP-Hard Problems in Agentic Graph Engineering and Swarm Orchestration."""
from .models import (
    AgentProfile,
    KnowledgeHyperedge,
    HypergraphCSGResult,
    VariableObservation,
    CausalDAGResult,
    FactStatement,
    AgentBeliefGraph,
    EpistemicConsensusResult,
    KnowledgeNode,
    AgentContextBudget,
    AttentionRoutingResult,
    MemoryNode,
    MemoryEdge,
    SpectralDecayResult,
    AgentToolTask,
    ToolResource,
    DisjunctiveToolScheduleResult,
    AgentClaim,
    TruthDiscoveryResult,
    SwarmTopologyGenome,
    TopologyEvolutionResult,
    TemporalEvent,
    BehaviorPattern,
    TemporalPatternResult,
    PlayerAgent,
    HyperedgePayoff,
    ParetoGameResult,
)

from .hypergraph_csg import solve_hypergraph_csg
from .causal_dag_synthesis import solve_causal_dag_synthesis
from .epistemic_consensus import solve_epistemic_consensus
from .budgeted_attention_routing import solve_budgeted_attention_routing
from .spectral_memory_decay import solve_spectral_memory_decay
from .disjunctive_tool_scheduler import solve_disjunctive_tool_scheduling
from .byzantine_epistemic_filter import solve_byzantine_truth_discovery
from .graph_grammar_evolution import solve_graph_grammar_evolution
from .temporal_subgraph_detector import solve_temporal_subgraph_detection
from .game_theoretic_hypergraph_nash import solve_pareto_game_hypergraph

__all__ = [
    # Models
    "AgentProfile",
    "KnowledgeHyperedge",
    "HypergraphCSGResult",
    "VariableObservation",
    "CausalDAGResult",
    "FactStatement",
    "AgentBeliefGraph",
    "EpistemicConsensusResult",
    "KnowledgeNode",
    "AgentContextBudget",
    "AttentionRoutingResult",
    "MemoryNode",
    "MemoryEdge",
    "SpectralDecayResult",
    "AgentToolTask",
    "ToolResource",
    "DisjunctiveToolScheduleResult",
    "AgentClaim",
    "TruthDiscoveryResult",
    "SwarmTopologyGenome",
    "TopologyEvolutionResult",
    "TemporalEvent",
    "BehaviorPattern",
    "TemporalPatternResult",
    "PlayerAgent",
    "HyperedgePayoff",
    "ParetoGameResult",
    # Solvers
    "solve_hypergraph_csg",
    "solve_causal_dag_synthesis",
    "solve_epistemic_consensus",
    "solve_budgeted_attention_routing",
    "solve_spectral_memory_decay",
    "solve_disjunctive_tool_scheduling",
    "solve_byzantine_truth_discovery",
    "solve_graph_grammar_evolution",
    "solve_temporal_subgraph_detection",
    "solve_pareto_game_hypergraph",
]
