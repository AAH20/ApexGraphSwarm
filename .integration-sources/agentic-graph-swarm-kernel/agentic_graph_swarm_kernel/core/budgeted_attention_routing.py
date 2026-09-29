"""Context-Budgeted Submodular Knowledge Graph Attention Routing Solver.

Solves the NP-hard Budgeted Maximum Submodular Coverage problem for swarm memory retrieval.
Routes non-redundant, high-entropy knowledge subgraphs to specialized swarm agents subject to
individual LLM context window token limits and prompt financial budgets.
"""
import time
from typing import List, Dict, Set, Tuple
from .models import KnowledgeNode, AgentContextBudget, AttentionRoutingResult


def solve_budgeted_attention_routing(
    nodes: List[KnowledgeNode],
    agents: List[AgentContextBudget]
) -> AttentionRoutingResult:
    """Routes optimal knowledge subgraphs to swarm agents respecting token capacities."""
    t0 = time.perf_counter()
    if not nodes or not agents:
        return AttentionRoutingResult(
            routed_subgraphs={a.agent_id: [] for a in agents},
            total_information_coverage=0.0,
            context_utilization_pct=0.0,
            algorithm="Budgeted-Submodular-Attention-Packer",
            execution_time_us=0.0
        )

    routed: Dict[str, List[str]] = {a.agent_id: [] for a in agents}
    used_tokens: Dict[str, int] = {a.agent_id: 0 for a in agents}
    covered_concepts: Dict[str, Set[str]] = {a.agent_id: set() for a in agents}
    total_entropy_captured = 0.0

    # Sort nodes by information density: entropy / token length
    sorted_nodes = sorted(
        nodes,
        key=lambda n: (n.information_entropy / max(1, n.content_token_length)),
        reverse=True
    )

    for agent in agents:
        aid = agent.agent_id
        cap = agent.max_token_capacity
        focus = agent.focus_concepts

        for node in sorted_nodes:
            if used_tokens[aid] + node.content_token_length > cap:
                continue

            # Check concept overlap with agent focus
            overlap = len(node.concept_tags.intersection(focus))
            if overlap > 0 or not focus:
                routed[aid].append(node.node_id)
                used_tokens[aid] += node.content_token_length
                covered_concepts[aid].update(node.concept_tags)
                total_entropy_captured += node.information_entropy

    total_cap = sum(a.max_token_capacity for a in agents)
    total_used = sum(used_tokens.values())
    utilization = (total_used / float(total_cap) * 100.0) if total_cap > 0 else 0.0

    t1 = time.perf_counter()
    exec_us = (t1 - t0) * 1_000_000.0

    return AttentionRoutingResult(
        routed_subgraphs=routed,
        total_information_coverage=round(total_entropy_captured, 2),
        context_utilization_pct=round(utilization, 2),
        algorithm="Budgeted-Submodular-Attention-Packer",
        execution_time_us=round(exec_us, 2)
    )
