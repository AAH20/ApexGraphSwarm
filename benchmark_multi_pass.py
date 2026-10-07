"""Multi-pass Louvain optimization with Byzantine detection for ApexGraphSwarm."""

import time
import json
import random
import sys
from collections import defaultdict
from typing import Hashable, Optional

sys.path.insert(0, '/Users/ahmedhassan/ApexGraphSwarm')
from kernels.community_detection.graph import Graph
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
                w = float(random.randint(1, max_weight))
                g.add_edge(nodes[i], nodes[j], w)
    return g


def random_partition(graph: Graph, k: int = 10) -> dict:
    """Create a random partition into k communities."""
    return {node: random.randrange(0, k) for node in graph.nodes()}


def benchmark_single_pass(n: int, k: int = 10, trials: int = 3) -> dict:
    """Benchmark single-pass Louvain optimization."""
    g = make_graph(n)
    partition = random_partition(g, k)

    # Initialize cached stats
    comm_tot, internal = _init_community_stats(g, partition)

    times = []
    modularities = []

    for trial in range(trials):
        start = time.time()
        # Single pass optimization
        partition_result = optimize_community_detection(g, partition, max_iterations=1)
        elapsed = time.time() - start
        times.append(elapsed)

        # Compute modularity - use internal cache if available
        if internal is not None and len(internal) > 0:
            q = modularity_incremental(g, partition_result, internal=internal)
        else:
            q = modularity_incremental(g, partition_result, comm_tot, g._m)
        modularities.append(q)

    return {
        "n": n,
        "avg_time": sum(times) / len(times),
        "avg_modularity": sum(modularities) / len(modularities),
        "times": times,
        "modularities": modularities,
    }


def benchmark_multi_pass(n: int, k: int = 10, trials: int = 3) -> dict:
    """Benchmark multi-pass Louvain optimization (repeated passes until no improvement)."""
    g = make_graph(n)
    partition = random_partition(g, k)

    # Initialize cached stats
    comm_tot, internal = _init_community_stats(g, partition)

    times = []
    modularities = []
    byzantine_counts = []

    for trial in range(trials):
        # Reset partition
        partition = random_partition(g, k)
        comm_tot, internal = _init_community_stats(g, partition)

        start = time.time()
        # Multi-pass optimization
        partition_result = optimize_community_multi_pass(g, partition, max_iterations=10)
        elapsed = time.time() - start
        times.append(elapsed)

        # Compute modularity - strip _byzantine key before passing to modularity_incremental
        part_for_q = {k: v for k, v in partition_result.items() if k != "_byzantine"}
        if internal is not None and len(internal) > 0:
            q = modularity_incremental(g, part_for_q, internal=internal)
        else:
            q = modularity_incremental(g, part_for_q, comm_tot, g._m)
        modularities.append(q)

        byzantine_counts.append(len(getattr(partition_result, "_byzantine", set())) if not isinstance(partition_result, dict) else len(partition_result.get("_byzantine", [])))

    return {
        "n": n,
        "avg_time": sum(times) / len(times),
        "avg_modularity": sum(modularities) / len(modularities),
        "times": times,
        "modularities": modularities,
        "byzantine_counts": byzantine_counts,
    }


def optimize_community_multi_pass(
    graph: Graph,
    partition: dict[Hashable, int],
    max_iterations: int = 10,
) -> dict[Hashable, int]:
    """Multi-pass Louvain optimization with Byzantine detection.
    
    Runs multiple passes of community detection, each pass improving on the
    previous partition. Includes Byzantine detection to identify and handle
    nodes that consistently reduce modularity.
    """
    m = graph._m
    if m == 0:
        return partition
    
    best_partition = dict(partition)
    best_modularity = float('-inf')
    all_byzantine = set()
    
    for pass_num in range(max_iterations):
        # Initialize cached stats for this pass
        comm_tot, internal = _init_community_stats(graph, best_partition)
        
        improved = True
        iteration = 0
        
        while improved and iteration < 5:  # inner iterations per pass
            improved = False
            iteration += 1
            
            # Shuffle nodes for randomization
            nodes = list(graph.nodes())
            random.shuffle(nodes)
            
            for node in nodes:
                current_comm = best_partition[node]
                
                # Collect candidate communities (current + neighbors' communities)
                candidate_comms = {current_comm}
                for neighbor in graph.neighbors(node):
                    candidate_comms.add(best_partition.get(neighbor))
                
                # Evaluate each candidate using delta computation
                best_comm = current_comm
                best_delta = 0.0
                
                for candidate_comm in candidate_comms:
                    delta = move_node_modularity_delta(
                        graph, partition, comm_tot, internal, m, node, current_comm, candidate_comm
                    )
                    
                    if delta > best_delta:
                        best_delta = delta
                        best_comm = candidate_comm
                
                # Move node if improvement found AND not Byzantine
                if best_delta > 0 and best_comm != current_comm:
                    if _is_likely_byzantine(graph, best_partition, node, best_comm):
                        all_byzantine.add(node)
                        continue  # Don't move Byzantine nodes
                    
                    best_partition[node] = best_comm
                    improved = True
        
        # Compute modularity after this pass
        comm_tot_pass, internal_pass = _init_community_stats(graph, best_partition)
        current_q = modularity_incremental(graph, best_partition, internal=internal_pass)
        
        # Check if this is the best we've seen
        if current_q > best_modularity:
            best_modularity = current_q
        else:
            # No improvement over best - we're done
            break
    
    # Final modularity computation
    final_comm_tot, final_internal = _init_community_stats(graph, best_partition)
    final_q = modularity_incremental(graph, best_partition, internal=final_internal)
    
    # Store byzantine nodes on the result for tracking
    # result is a dict, so we add _byzantine as a key
    result = dict(best_partition)
    result["_byzantine"] = list(all_byzantine)
    result["_best_modularity"] = final_q
    
    return result


def _is_likely_byzantine(
    graph: Graph,
    partition: dict[Hashable, int],
    node: Hashable,
    target_comm: int,
) -> bool:
    """Heuristic Byzantine detection: nodes that consistently reduce modularity."""
    k_i = graph.weighted_degree(node)
    current_comm = partition.get(node)
    
    if current_comm is None:
        return False
    
    # Check if node has very few connections within its community
    neighbor_comm_weight = 0.0
    for neighbor, w in graph.neighbors(node).items():
        if partition.get(neighbor) == target_comm:
            neighbor_comm_weight += w
    
    # If node connects very weakly to target community but strongly to others,
    # it might be Byzantine (intentionally disruptive)
    total_weight = k_i
    if total_weight == 0:
        return False
    
    connect_ratio = neighbor_comm_weight / total_weight if total_weight > 0 else 0
    
    # Node connects < 20% to target community - suspicious
    if connect_ratio < 0.2 and target_comm != current_comm:
        # Further check: does this node's home community improve when it leaves?
        # If removing the node improves its home community's modularity, it's likely Byzantine
        comm_nodes = [n for n in graph.nodes() if partition.get(n) == current_comm]
        if len(comm_nodes) > 1:
            # Try computing modularity without this node
            test_partition = dict(partition)
            test_partition.pop(node, None)
            test_comm_tot, test_internal = _init_community_stats(graph, test_partition)
            q_without = modularity_incremental(graph, test_partition, test_comm_tot, graph._m)
            
            # Compare with modularity including the node
            orig_comm_tot, orig_internal = _init_community_stats(graph, partition)
            q_with = modularity_incremental(graph, partition, internal=orig_internal)
            
            if q_without > q_with:
                return True
    
    # Check for extreme degree disparity within community
    comm_degrees = [graph.weighted_degree(n) for n in graph.nodes() if partition.get(n) == current_comm]
    if len(comm_degrees) > 1:
        avg_deg = sum(comm_degrees) / len(comm_degrees)
        std_deg = (sum((d - avg_deg) ** 2 for d in comm_degrees) / len(comm_degrees)) ** 0.5
        node_deg = graph.weighted_degree(node)
        if std_deg > 0 and abs(node_deg - avg_deg) > 2 * std_deg:
            # Node is an outlier in its community
            return connect_ratio < 0.3
    
    return False


def benchmark_multi_pass_vs_single(n: int, k: int = 10, trials: int = 2) -> dict:
    """Compare multi-pass vs single-pass optimization."""
    single = benchmark_single_pass(n, k, trials)
    multi = benchmark_multi_pass(n, k, trials)
    
    speedup = single["avg_time"] / multi["avg_time"] if multi["avg_time"] > 0 else float('inf')
    
    return {
        "n": n,
        "single_pass": {
            "avg_time": single["avg_time"],
            "avg_modularity": single["avg_modularity"],
        },
        "multi_pass": {
            "avg_time": multi["avg_time"],
            "avg_modularity": multi["avg_modularity"],
            "modularity_gain": multi["avg_modularity"] - single["avg_modularity"],
            "byzantine_counts": multi.get("byzantine_counts", []),
        },
        "speedup": speedup,
        "byzantine_detected": any(c > 0 for c in multi.get("byzantine_counts", [])),
    }


if __name__ == "__main__":
    results = []
    for n in [200, 500, 1000]:
        print(f"Benchmarking n={n}...")
        result = benchmark_multi_pass_vs_single(n, k=10, trials=2)
        results.append(result)
        print(f"  n={n}: single={result['single_pass']['avg_time']:.4f}s, "
                f"multi={result['multi_pass']['avg_time']:.4f}s, "
                f"speedup={result['speedup']:.1f}x, "
                f"mod_gain={result['multi_pass']['modularity_gain']:.6f}, "
                f"byzantine={result['byzantine_detected']}")
    
    # Save results
    with open('/Users/ahmedhassan/ApexGraphSwarm/benchmark_multi_pass.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nMulti-pass benchmark complete.")