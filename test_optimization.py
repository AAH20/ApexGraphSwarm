"""Test incremental modularity optimization against naive computation."""
import time
import sys
import json
import random
from collections import defaultdict
from typing import Hashable

sys.path.insert(0, '/Users/ahmedhassan/ApexGraphSwarm')
from kernels.community_detection.graph import Graph
from kernels.community_detection.louvain import _modularity
from kernels.community_detection.incremental import (
    _init_community_stats,
    modularity_incremental,
    move_node_modularity_delta,
    optimize_community_detection,
)


def make_graph(n: int, edge_prob: float = 0.1, max_weight: int = 5) -> Graph:
    """Create a random graph with n nodes."""
    g = Graph()
    nodes = [f"agent_{i}" for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if random.random() < edge_prob:
                w = random.randint(1, max_weight)
                g.add_edge(nodes[i], nodes[j], w)
    return g


def random_partition(graph: Graph, k: int = 10) -> dict:
    """Create a random partition into k communities."""
    return {node: random.randrange(0, k) for node in graph.nodes()}


def benchmark_comparison(n: int, k: int = 10, trials: int = 2) -> dict:
    """Benchmark naive vs incremental modularity computation."""
    g = make_graph(n)
    partition = random_partition(g, k)
    
    # Naive computation (original _modularity)
    naive_times = []
    incremental_times = []
    
    # Initialize cached stats
    comm_tot, internal = _init_community_stats(g, partition)
    
    for trial in range(trials):
        # Naive: recompute from scratch
        start = time.time()
        _ = _modularity(g, partition)
        naive_times.append(time.time() - start)
        
        # Incremental: use cached stats
        start = time.time()
        _ = modularity_incremental(g, partition, comm_tot, internal)
        incremental_times.append(time.time() - start)
    
    return {
        "n": n,
        "naive_avg": sum(naive_times) / len(naive_times),
        "incremental_avg": sum(incremental_times) / len(incremental_times),
        "speedup": sum(naive_times) / sum(incremental_times) if sum(incremental_times) > 0 else float('inf'),
        "naive_times": naive_times,
        "incremental_times": incremental_times,
    }


# Run benchmarks
results = []
for n in [200, 500, 1000]:
    print(f"Benchmarking n={n}...")
    result = benchmark_comparison(n)
    results.append(result)
    print(f"  n={n}: naive={result['naive_avg']:.6f}s, incremental={result['incremental_avg']:.6f}s, "
            f"speedup={result['speedup']:.1f}x")

# Save results
with open('/Users/ahmedhassan/ApexGraphSwarm/optimization_benchmark.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nOptimization benchmark complete.")