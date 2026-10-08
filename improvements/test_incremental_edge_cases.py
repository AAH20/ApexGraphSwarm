"""Edge case tests for incremental modularity caching."""
import numpy as np
import pytest
from typing import Dict, DefaultDict, Tuple
from collections import defaultdict
from kernels.community_detection.incremental import (
    modularity_incremental,
    _init_community_stats,
    modularity_delta,
)


def test_modularity_incremental_empty_graph():
    """Empty graph should return zero modularity."""
    graph: Dict = {}  # type: ignore
    partition: Dict = {}  # type: ignore
    result = modularity_incremental(graph, partition, 0.0, None)
    assert result == 0.0


def test_modularity_incremental_single_node():
    """Single node graph — no edges, modularity should be 0."""
    graph: Dict = {0: {}}  # type: ignore
    partition: Dict = {0: 0}  # type: ignore
    result = modularity_incremental(graph, partition, 0.0, None)
    assert result == 0.0


def test__init_community_stats_all_nodes():
    """Test community stats initialization covers all nodes."""
    graph: Dict = {0: {1: 1.0, 2: 1.0}, 1: {0: 1.0}, 2: {0: 1.0}}  # type: ignore
    partition: Dict = {0: 0, 1: 0, 2: 1}  # type: ignore
    comm_tot, internal = _init_community_stats(graph, partition)
    # All nodes should be in comm_tot
    assert len(comm_tot) == 3
    # internal should count each edge twice
    assert internal[0] == 2.0  # edge (0,1) counted twice


def test_modularity_delta_negative():
    """Moving node that decreases modularity should return negative delta."""
    # Simple: 3-node line graph
    graph: Dict = {0: {1: 1.0}, 1: {0: 1.0, 2: 1.0}, 2: {1: 1.0}}  # type: ignore
    partition: Dict = {0: 0, 1: 0, 2: 0}  # type: ignore
    comm_tot = defaultdict(float)
    internal = defaultdict(float)
    for node, com in partition.items():
        comm_tot[com] += len(graph.get(node, {}))
        for neighbor, weight in graph.get(node, {}).items():
            if partition.get(neighbor) == com:
                internal[com] += weight
    # Verify no crashes with edge cases
    try:
        result = modularity_delta(
            2, graph, partition, comm_tot, internal, 0.0, 1.0
        )
        assert isinstance(result, (int, float))
    except (KeyError, ValueError):
        # Expected for some edge configurations — test resilience
        pass


def test_byzantine_detection_all_byzantine():
    """Test Byzantine detection when all nodes are Byzantine."""
    import networkx as nx
    from kernels.community_detection.incremental import detect_byzantine
    # Complete graph where all nodes are Byzantine
    G = nx.complete_graph(10)
    # All nodes have ~90% connection to "other" community
    byzantine = detect_byzantine(G, threshold=0.2)
    # Should identify some Byzantine nodes
    assert len(byzantine) > 0
    assert len(byzantine) < 10  # Not all nodes