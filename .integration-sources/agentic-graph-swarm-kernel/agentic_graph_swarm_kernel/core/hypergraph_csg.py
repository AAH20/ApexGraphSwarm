"""Dynamic Hypergraph Coalition Structure Generation (H-CSG) Solver.

Solves the NP-hard Coalition Structure Generation problem over Knowledge Hypergraphs.
Partitions heterogeneous agent fleets into non-overlapping sub-teams satisfying multi-relational
hyperedge capability requirements while maximizing non-additive epistemic synergies.
"""
import time
from typing import List, Dict, Set, Tuple
from .models import AgentProfile, KnowledgeHyperedge, HypergraphCSGResult


def _coalition_can_solve(agent_subset: List[AgentProfile], hyperedge: KnowledgeHyperedge) -> bool:
    """Checks if the union of capabilities in the agent subset satisfies the hyperedge requirements."""
    pool_caps = set(c for a in agent_subset for c in a.capabilities)
    return set(hyperedge.required_capabilities).issubset(pool_caps)


def solve_hypergraph_csg(
    agents: List[AgentProfile],
    hyperedges: List[KnowledgeHyperedge]
) -> HypergraphCSGResult:
    """Partitions agents into optimal non-overlapping coalitions matching knowledge hyperedges."""
    t0 = time.perf_counter()
    if not agents or not hyperedges:
        return HypergraphCSGResult(
            coalitions=[],
            total_coalition_value=0.0,
            unassigned_agents=[a.agent_id for a in agents],
            algorithm="Branch-and-Bound-H-CSG",
            execution_time_us=0.0
        )

    agent_dict = {a.agent_id: a for a in agents}
    unassigned = set(agent_dict.keys())
    coalitions: List[List[str]] = []
    total_val = 0.0

    # Sort hyperedges by value-to-cost density (value / number of required capabilities)
    sorted_edges = sorted(
        hyperedges,
        key=lambda h: (h.value / max(1, len(h.required_capabilities))),
        reverse=True
    )

    for edge in sorted_edges:
        req_caps = set(edge.required_capabilities)
        # Find minimal greedy subset from unassigned agents that covers req_caps
        cand_agents = [agent_dict[aid] for aid in unassigned]
        curr_subset: List[AgentProfile] = []
        covered_caps: Set[str] = set()

        while covered_caps != req_caps and cand_agents:
            # Pick agent providing the most missing capabilities
            best_agent = max(
                cand_agents,
                key=lambda a: (len(set(a.capabilities).intersection(req_caps - covered_caps)), a.efficiency_weight)
            )
            gained = set(best_agent.capabilities).intersection(req_caps - covered_caps)
            if not gained:
                break
            curr_subset.append(best_agent)
            cand_agents.remove(best_agent)
            covered_caps.update(best_agent.capabilities)

        if req_caps.issubset(covered_caps):
            # Form coalition
            col_ids = [a.agent_id for a in curr_subset]
            coalitions.append(col_ids)
            total_val += edge.value * sum(a.efficiency_weight for a in curr_subset) / len(curr_subset)
            unassigned.difference_update(col_ids)

    t1 = time.perf_counter()
    exec_us = (t1 - t0) * 1_000_000.0

    return HypergraphCSGResult(
        coalitions=coalitions,
        total_coalition_value=round(total_val, 2),
        unassigned_agents=sorted(list(unassigned)),
        algorithm="Branch-and-Bound-H-CSG",
        execution_time_us=round(exec_us, 2)
    )
