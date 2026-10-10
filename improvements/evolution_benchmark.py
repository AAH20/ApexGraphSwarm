"""Multi-objective evolutionary benchmark for ApexGraphSwarm.

Evaluates modularity quality, speed, and stability across graph sizes
with evolutionary parameter configuration (damping, decay_rate).
"""

import numpy as np
import time
from typing import Dict, List, Tuple, Optional


def multi_objective_benchmark(
    graph_sizes: List[int] = [200, 500, 1000],
    n_passes: int = 10,
    n_runs: int = 3,
    damping: float = 0.95,
    decay_rate: float = 0.99,
) -> dict:
    """Run multi-objective evolutionary benchmark with evaluation parameters.

    Optimizes: modularity quality + speed + stability
    Evaluates: convergence, adaptation, robustness
    """
    import networkx as nx
    import random

    results = {}

    for n in graph_sizes:
        print(f"Benchmarking n={n}...")

        # Generate graph with ground-truth communities
        np.random.seed(42)
        G = nx.random_partition_graph(
            [n // 4] * 4, p_in=0.3, p_out=0.05
        )

        # Ground-truth assignment
        true_assignment = {}
        node_list = list(G.nodes())
        for i, com_size in enumerate([n // 4] * 4):
            com_nodes = node_list[:com_size]
            for node in com_nodes:
                true_assignment[node] = i
                node_list = node_list[1:]

        # Run evolutionary modularity cache
        from improvements.rapids_port import AdaptiveModularityCache

        run_results = []

        for run in range(n_runs):
            # Shuffle assignment slightly for diversity
            assignment = dict(true_assignment)
            for _ in range(int(n * 0.1)):
                if len(assignment) >= 2:
                    nodes = list(assignment.keys())
                    # Python 3.9 compatible: use random.sample instead of choice with replace=False
                    n1, n2 = random.sample(nodes, 2)
                    comm1, comm2 = assignment[n1], assignment[n2]
                    if comm1 != comm2:
                        assignment[n1], assignment[n2] = comm2, comm1

            # Initialize adaptive cache
            cache = AdaptiveModularityCache(G, assignment, damping, decay_rate)

            # Run multi-pass evolution
            start = time.time()

            for pass_num in range(n_passes):
                move_node = random.choice(list(assignment.keys()))
                old_comm = assignment[move_node]
                possible_comms = [c for c in set(assignment.values()) if c != old_comm]
                if possible_comms:
                    new_comm = random.choice(possible_comms)
                else:
                    new_comm = old_comm

                delta_q = cache.update_pass(move_node, old_comm, new_comm)
                assignment[move_node] = new_comm

            elapsed = time.time() - start

            # Compute evaluation metrics
            final_metrics = cache.get_evolution_metrics()

            # Compute quality vs ground truth
            true_modularity = _compute_true_modularity(G, assignment, n)

            run_results.append({
                "run": run,
                "elapsed_ms": round(elapsed * 1000, 2),
                "final_modularity": final_metrics["mean_delta_q"],
                "convergence": final_metrics["convergence"],
                "trend": final_metrics["trend"],
                "true_modularity": true_modularity,
                "quality_gap": true_modularity - final_metrics["mean_delta_q"],
            })

        # Aggregate results
        run_elapsed = [r["elapsed_ms"] for r in run_results]
        final_mods = [r["final_modularity"] for r in run_results]
        convergences = [r["convergence"] for r in run_results]
        quality_gaps = [r["quality_gap"] for r in run_results]

        results[n] = {
            "graph_size": n,
            "runs": n_runs,
            "passes": n_passes,
            "damping": damping,
            "decay_rate": decay_rate,
            "mean_elapsed_ms": round(sum(run_elapsed) / len(run_elapsed), 2),
            "mean_final_modularity": round(sum(final_mods) / len(final_mods), 6),
            "mean_convergence": round(sum(convergences) / len(convergences), 4),
            "mean_quality_gap": round(sum(quality_gaps) / len(quality_gaps), 6),
            "elapsed_range_ms": [min(run_elapsed), max(run_elapsed)],
            "modularity_range": [min(final_mods), max(final_mods)],
            "convergence_range": [min(convergences), max(convergences)],
            "quality_gap_range": [min(quality_gaps), max(quality_gaps)],
        }

    return results


def _compute_true_modularity(G, assignment, n: int) -> float:
    """Compute modularity against ground-truth communities."""
    import networkx as nx

    m = G.number_of_edges()
    if m == 0:
        return 0.0

    communities = {}
    for node, com in assignment.items():
        communities.setdefault(com, []).append(node)

    q = 0.0
    for com, nodes in communities.items():
        internal = sum(G.has_edge(u, v) for u in nodes for v in nodes if u < v)
        deg_sum = sum(G.degree(n) for n in nodes)

        if deg_sum > 0 and m > 0:
            q += (internal / m) - (deg_sum / (2 * m)) ** 2

    return q / 2.0


def generate_evolution_report() -> str:
    """Generate evolutionary benchmark report text."""
    results = multi_objective_benchmark()

    lines = [
        "=" * 70,
        "APEXGRAPHSWARM — Multi-Objective Evolutionary Benchmark",
        "=" * 70,
    ]

    for n, r in results.items():
        lines.append(f"\nn={n} (runs={r['runs']}, passes={r['passes']}):")
        lines.append(f"  Mean time:     {r['mean_elapsed_ms']:.1f}ms (range: {r['elapsed_range_ms'][0]}-{r['elapsed_range_ms'][1]}ms)")
        lines.append(f"  Mean modularity:    {r['mean_final_modularity']:.6f} (range: {r['modularity_range'][0]:.6f}-{r['modularity_range'][1]:.6f})")
        lines.append(f"  Mean convergence:  {r['mean_convergence']:.4f} (range: {r['convergence_range'][0]:.4f}-{r['convergence_range'][1]:.4f})")
        lines.append(f"  Mean quality gap:  {r['mean_quality_gap']:.6f} (range: {r['quality_gap_range'][0]:.6f}-{r['quality_gap_range'][1]:.6f})")
        lines.append(f"  Config: damping={r['damping']}, decay_rate={r['decay_rate']}")

    lines.append("\n" + "=" * 70)
    lines.append("Evolutionary Parameter Optimization:")
    lines.append("  - damping: Temporal persistence (0.9-0.99 typical)")
    lines.append("  - decay_rate: Cache staleness control (0.99 = slow evolution)")
    lines.append("  - Tradeoff: higher damping = more stable, slower convergence")
    lines.append("  - Tradeoff: higher decay_rate = faster cache freshening, noisier ΔQ")
    lines.append("=" * 70)

    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_evolution_report())