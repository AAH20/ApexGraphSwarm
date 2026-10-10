"""Test ΔQ computation performance — the key optimization for Louvain/Leiden."""
import time
import sys
import json
import random
from collections import defaultdict
from typing import Hashable

sys.path.insert(0, '/Users/ahmedhassan/ApexGraphSwarm')
from kernels.community_detection.graph import Graph
from kernels.community_detection.incremental import (
    _init_community_stats,
    move_node_modularity_delta,
    modularity_incremental,
)


def make_graph(n: int, edge_prob: float = 0.1, max_weight: int = 5) -> Graph:
    g = Graph()
    nodes = [f"agent_{i}" for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if random.random() < edge_prob:
                w = random.randint(1, max_weight)
                g.add_edge(nodes[i], nodes[j], w)
    return g


def random_partition(graph: Graph, k: int = 10) -> dict:
    return {node: random.randrange(0, k) for node in graph.nodes()}


def benchmark_delta_computation(n: int, trials: int = 3) -> dict:
    """Benchmark ΔQ computation for moving each node once."""
    g = make_graph(n)
    partition = random_partition(g)
    k = max(partition.values()) + 1
    
    # Initialize cached stats
    comm_tot, internal = _init_community_stats(g, partition)
    m = g._m
    
    # Benchmark ΔQ for each node
    delta_times = []
    
    for node in g.nodes():
        from_comm = partition[node]
        
        # Collect candidate communities (current + neighbors' communities)
        candidate_comms = {from_comm}
        for neighbor in g.neighbors(node):
            candidate_comms.add(partition.get(neighbor))
        
        # Compute ΔQ for each candidate
        start = time.time()
        for candidate_comm in candidate_comms:
            _ = move_node_modularity_delta(
                g, partition, comm_tot, internal, m,
                node, from_comm, candidate_comm
            )
        elapsed = time.time() - start
        delta_times.append(elapsed)
    
    avg_delta_time = sum(delta_times) / len(delta_times)
    
    return {
        "n": n,
        "avg_delta_time_total": avg_delta_time,
        "avg_delta_time_per_node": avg_delta_time / n if n > 0 else float('inf'),
        "candidate_comms_avg": sum(len(g.neighbors(node)) for node in g.nodes()) / n,
    }


# Run benchmarks
results = []
for n in [100, 500, 1000, 2000]:
    print(f"Benchmarking ΔQ computation n={n}...")
    result = benchmark_delta_computation(n)
    results.append(result)
    print(f"  n={n}: {result['avg_delta_time_per_node']*1000:.2f}ms per node, "
            f"{result['candidate_comms_avg']:.0f} candidates avg")

with open('/Users/ahmedhassan/ApexGraphSwarm/delta_benchmark.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nΔQ computation benchmark complete.")