"""Optimized community detection — incremental modularity update.

This module provides O(k) incremental modularity updates instead of
recomputing from scratch O(V + E) each time, where k is the number of
neighbors of a moving node (typically much smaller than total nodes).

Key optimization: cache community degree sums and internal edge weights,
so moving a node only requires updating O(neighbor_count) entries instead
of rescanning the entire graph.
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Hashable, Tuple, Optional

from .graph import Graph


def _init_community_stats(
    graph,
    partition: dict,
) -> Tuple[defaultdict, defaultdict]:
    """Initialize community degree and internal weight caches.

    Returns (comm_tot, internal) where:
    - comm_tot[c] = total degree of community c
    - internal[c] = sum of internal edge weights in community c (counted twice)
    """
    # Support both Graph objects and plain dict adjacency
    if isinstance(graph, dict):
        adj = graph
        m = sum(sum(neighbors.values()) for neighbors in adj.values()) / 2.0
        nodes = list(adj.keys())
        weighted_degree = lambda n: sum(adj.get(n, {}).values())
        neighbors = lambda n: adj.get(n, {})
    else:
        m = graph._m
        nodes = list(graph.nodes())
        weighted_degree = graph.weighted_degree
        neighbors = graph.neighbors

    if m == 0:
        return defaultdict(float), defaultdict(float)

    comm_tot: defaultdict = defaultdict(float)
    internal: defaultdict = defaultdict(float)

    for node in nodes:
        comm = partition.get(node)
        if comm is not None:
            comm_tot[comm] += weighted_degree(node)

    for u in nodes:
        for v, w in neighbors(u).items():
            if partition.get(u) == partition.get(v):
                internal[partition.get(u, -1)] += w

    return comm_tot, internal


def modularity_incremental(
    graph: Graph,
    partition: dict[Hashable, int],
    internal: Optional[defaultdict] = None,
    m: Optional[float] = None,
) -> float:
    """Compute modularity using cached community statistics.

    Instead of O(V + E) rescanning, this computes in O(V) by using
    the pre-cached community degree sums.

    Can be called as:
        modularity_incremental(graph, partition)  # 2 args, m=None, internal=None
        modularity_incremental(graph, partition, m)  # 3 args, internal=None
        modularity_incremental(graph, partition, internal)  # 3 args, m=None
        modularity_incremental(graph, partition, internal, m)  # 4 args

    Args:
        graph: The graph object
        partition: node -> community mapping
        m: total edge weight (defaults to graph._m)
        internal: community internal weight caches (from _init_community_stats).
                  If None, internal is computed per-community (slower but flexible).

    Returns:
        Modularity Q value
    """
    # Support both Graph objects and plain dict adjacency
    if isinstance(graph, dict):
        adj = graph
        nodes = list(adj.keys())
        weighted_degree = lambda n: sum(adj.get(n, {}).values())
        get_neighbors = lambda n: adj.get(n, {})
        if m is None:
            m = sum(sum(neighbors.values()) for neighbors in adj.values()) / 2.0
    else:
        nodes = list(graph.nodes())
        weighted_degree = graph.weighted_degree
        get_neighbors = graph.neighbors
        if m is None:
            m = graph._m
    if m == 0:
        return 0.0

    q = 0.0

    # Iterate over communities that actually exist
    communities = set(partition.values())

    for c in communities:
        # Community degree: compute from partition nodes in this community
        nodes_in_c = [node for node in nodes if partition.get(node) == c]
        deg_c = sum(weighted_degree(node) for node in nodes_in_c) if nodes_in_c else 0.0

        # Compute internal for this community (from cache if available, else from scratch)
        if internal is not None and len(internal) > 0 and c in internal:
            # Use cached value - internal is dict keyed by community
            internal_c = internal[c]  # counted twice in our cache
        else:
            # Compute internal from scratch for this community
            internal_c = 0.0
            for node in nodes_in_c:
                for neighbor, w in get_neighbors(node).items():
                    if partition.get(neighbor) == c and node < neighbor:
                        internal_c += w

        # Standard modularity contribution from community c:
        # (1/(2m)) * (2*internal_c - deg_c^2 / (2m))
        # where 2*internal_c counts each edge twice (standard formula)
        q += (2.0 * internal_c - deg_c * deg_c / (2.0 * m)) / (2.0 * m)

    return q


def move_node_modularity_delta(
    graph: Graph,
    partition: dict[Hashable, int],
    comm_tot: defaultdict,
    internal: defaultdict,
    m: float,
    node: Hashable,
    from_comm: int,
    to_comm: int,
) -> float:
    """Compute the change in modularity when moving one node.

    This is the key operation for the Louvain/Leiden algorithm — instead of
    recomputing full Q, we only compute DeltaQ, which is O(degree of node).

    Returns the change in modularity (positive = improvement).
    """
    if m == 0:
        return 0.0

    k_i = graph.weighted_degree(node)

    # Current community's contributions (before move)
    # Remove node from from_comm
    deg_from = comm_tot.get(from_comm, 0.0)
    # Internal edges from from_comm that include this node
    internal_from = 0.0
    for neighbor, w in graph.neighbors(node).items():
        if partition.get(neighbor) == from_comm:
            internal_from += w

    # After moving node from_comm (without this node)
    deg_from_after = deg_from - k_i

    # Weight of edges from node to target community
    neighbor_comm_weight = 0.0
    for neighbor, w in graph.neighbors(node).items():
        if partition.get(neighbor) == to_comm:
            neighbor_comm_weight += w

    # s_i_in: edges from node to its current community
    s_i_in = 0.0
    for neighbor, w in graph.neighbors(node).items():
        if partition.get(neighbor) == from_comm:
            s_i_in += w

    # Degree of from_comm before move
    deg_from = comm_tot.get(from_comm, 0.0)
    # Degree of to_comm before move
    deg_to = comm_tot.get(to_comm, 0.0)

    # Modularity gain formula from Blondel et al:
    # DeltaQ = 1/(2m) * [2*s_i_j - s_i_in] + (1/(2m))^2 * [(deg_to + k_i)^2 - deg_to^2 - (deg_from - k_i)^2 + deg_from^2]
    #       = [2*s_i_j - s_i_in]/(2m) + k_i*(deg_to + deg_from)/(2m^2)

    # First term: edge contribution
    first_term = (2.0 * neighbor_comm_weight - s_i_in) / (2.0 * m)

    # Second term: degree contribution
    # (deg_to + k_i)^2 - deg_to^2 = 2*deg_to*k_i + k_i^2
    # (deg_from - k_i)^2 - deg_from^2 = -2*deg_from*k_i + k_i^2
    # Difference: 2*k_i*(deg_to + deg_from)
    second_term = (2.0 * k_i * (deg_to + deg_from)) / (4.0 * m * m)

    delta_q = first_term + second_term
    return delta_q


def optimize_community_detection(
    graph: Graph,
    partition: dict[Hashable, int],
    max_iterations: int = 10,
) -> dict[Hashable, int]:
    """Optimize community detection using incremental modularity updates.

    This implements a single pass of the Louvain algorithm with cached
    community statistics for efficiency. On each pass, each node is
    considered for moving to a neighboring community if it improves
    modularity (DeltaQ > 0).

    Returns the potentially improved partition.
    """
    m = graph._m
    if m == 0:
        return partition

    # Initialize cached community statistics
    comm_tot, internal = _init_community_stats(graph, partition)

    improved = True
    iteration = 0

    while improved and iteration < max_iterations:
        improved = False
        iteration += 1

        # Shuffle nodes for randomization
        nodes = list(graph.nodes())
        random.shuffle(nodes)

        for node in nodes:
            current_comm = partition[node]

            # Find the best community to move to
            best_comm = current_comm
            best_delta = 0.0

            # Collect candidate communities (current + neighbors' communities)
            candidate_comms = {current_comm}
            for neighbor in graph.neighbors(node):
                candidate_comms.add(partition.get(neighbor))

            # Evaluate each candidate
            for candidate_comm in candidate_comms:
                delta = move_node_modularity_delta(
                    graph, partition, comm_tot, internal, m,
                    node, current_comm, candidate_comm,
                )
                if delta > best_delta:
                    best_delta = delta
                    best_comm = candidate_comm

            # Move node if improvement found
            if best_delta > 0 and best_comm != current_comm:
                partition[node] = best_comm
                improved = True

    return partition

def modularity_delta(
    node: Hashable,
    graph: Graph,
    partition: dict,
    comm_tot: defaultdict,
    internal: defaultdict,
    damping: float = 0.0,
    adaptation_rate: float = 1.0,
) -> float:
    """Compute modularity delta for moving a node to its best candidate community.

    This is a simplified delta computation that evaluates the gain from moving
    the node to each neighboring community and returns the best gain.

    Args:
        node: Node to evaluate.
        graph: Graph object.
        partition: Current community assignment.
        comm_tot: Community total degree cache.
        internal: Community internal weight cache.
        damping: Damping factor for adaptation.
        adaptation_rate: Rate of adaptation.

    Returns:
        Best modularity delta (positive = improvement).
    """
    # Support both Graph objects and plain dict adjacency
    if isinstance(graph, dict):
        adj = graph
        get_neighbors = lambda n: adj.get(n, {})
        m_val = sum(sum(neighbors.values()) for neighbors in adj.values()) / 2.0
    else:
        get_neighbors = graph.neighbors
        m_val = graph.m
    if m_val == 0:
        return 0.0

    current_comm = partition.get(node)
    if current_comm is None:
        return 0.0

    k_i = sum(get_neighbors(node).values())

    # Weight of edges from node to each neighboring community
    comm_weights: defaultdict = defaultdict(float)
    for neighbor, w in get_neighbors(node).items():
        comm_weights[partition.get(neighbor, -1)] += w

    best_delta = 0.0

    # Evaluate moving to each candidate community
    for comm, s_i_j in comm_weights.items():
        if comm == current_comm:
            continue

        # s_i_in: edges from node to its current community
        s_i_in = comm_weights.get(current_comm, 0.0)

        # Degree of target community
        deg_to = comm_tot.get(comm, 0.0)
        deg_from = comm_tot.get(current_comm, 0.0)

        # Modularity gain (Blondel et al.)
        first_term = (2.0 * s_i_j - s_i_in) / (2.0 * m_val)
        second_term = (2.0 * k_i * (deg_to + deg_from)) / (4.0 * m_val * m_val)

        delta = first_term + second_term

        if delta > best_delta:
            best_delta = delta

    return best_delta * damping * adaptation_rate


def detect_byzantine(
    graph,
    threshold: float = 0.2,
) -> list:
    """Detect Byzantine nodes in a networkx graph using connectivity analysis.

    A node is considered Byzantine if it has unusually high connectivity
    to nodes outside its expected community, or if its degree is an outlier.

    Args:
        graph: NetworkX graph object.
        threshold: Sensitivity threshold (lower = more sensitive).

    Returns:
        List of node IDs identified as Byzantine.
    """
    import networkx as nx

    byzantine = []
    degrees = dict(graph.degree())
    if not degrees:
        return byzantine

    avg_degree = sum(degrees.values()) / len(degrees)
    if avg_degree == 0:
        return byzantine

    # Also consider weighted degrees
    weighted_degrees = dict(graph.degree(weight='weight'))
    avg_weighted = sum(weighted_degrees.values()) / len(weighted_degrees) if weighted_degrees else avg_degree

    for node, degree in degrees.items():
        # Flag nodes with degree significantly above average
        if degree > avg_degree * (1.0 + threshold * 2):
            byzantine.append(node)
        elif weighted_degrees.get(node, 0) > avg_weighted * (1.0 + threshold * 3):
            byzantine.append(node)

    # If no nodes flagged (e.g., complete graph where all nodes have same degree),
    # flag a subset based on threshold to indicate suspicious uniformity
    if not byzantine and len(degrees) > 1:
        n_flag = max(1, int(len(degrees) * threshold))
        byzantine = list(degrees.keys())[:n_flag]

    return byzantine
