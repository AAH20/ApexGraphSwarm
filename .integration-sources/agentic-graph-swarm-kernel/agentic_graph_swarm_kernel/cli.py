"""Command Line Interface for Agentic Graph Swarm Kernel."""
import argparse
import sys
from .engine import AgenticGraphSwarmEngine


def run_benchmark_all():
    engine = AgenticGraphSwarmEngine()
    print("=" * 85)
    print("  APEX AGENTIC GRAPH SWARM KERNEL: 10 APEX SOLVERS BENCHMARK")
    print("=" * 85)

    results = engine.benchmark_all_10()
    solvers = results["solvers"]

    print(f"\n{'Solver ID & Name':<35} | {'Key Metric':<25} | {'Latency':<12}")
    print("-" * 85)
    for s_name, data in solvers.items():
        time_str = f"{data['time_us']:.1f} µs"
        primary_metric = [f"{k}={v}" for k, v in data.items() if k != 'time_us'][0]
        print(f"{s_name:<35} | {primary_metric:<25} | {time_str:<12}")

    print("-" * 85)
    print(f"Total Combined Pipeline Benchmark Execution: {results['total_benchmark_time_us']:.1f} µs")
    print("=" * 85)
    return results


def run_world_sim_demo():
    engine = AgenticGraphSwarmEngine()
    print("=" * 85)
    print("  DIGITAL PARALLEL WORLD SIMULATOR HARNESS (BEYOND MIROFISH)")
    print("=" * 85)
    suite = engine.generate_synthetic_benchmark_suite()

    # 1. Causal DAG
    res_causal = engine.world_simulator.synthesize_macro_causality(*suite["p2_causal"])
    print(f"[1] Macro Causal DAG: vars={len(res_causal.adjacency_matrix)}, "
          f"bic_score={res_causal.bic_score}, acyclic={res_causal.is_acyclic} ({res_causal.execution_time_us} µs)")

    # 2. Coalition Partitioning
    res_csg = engine.world_simulator.partition_market_coalitions(*suite["p1_csg"])
    print(f"[2] Market Syndicates (H-CSG): coalitions={len(res_csg.coalitions)}, "
          f"captured_value={res_csg.total_coalition_value} ({res_csg.execution_time_us} µs)")

    # 3. Disinformation Filtering
    res_truth = engine.world_simulator.filter_disinformation_and_rumors(suite["p7_byzantine"])
    print(f"[3] Disinformation / Byzantine Filter: resolved={len(res_truth.resolved_attributes)}, "
          f"quarantined={res_truth.quarantined_byzantine_agents} ({res_truth.execution_time_us} µs)")

    # 4. Emergent Panic Detection
    res_panic = engine.world_simulator.detect_emergent_panics_and_runs(*suite["p9_temporal"])
    print(f"[4] Emergent Panic & Run Detector: matches={res_panic.total_detections}, "
          f"causality_ordered={res_panic.causality_strictly_ordered} ({res_panic.execution_time_us} µs)")

    # 5. Memory Sparsification
    res_decay = engine.world_simulator.compress_civilization_memory(*suite["p5_memory"])
    print(f"[5] Civilization Memory Decay: compression={res_decay.spectral_compression_ratio}, "
          f"retained_nodes={len(res_decay.retained_nodes)} ({res_decay.execution_time_us} µs)")
    print("=" * 85)


def run_enterprise_mesh_demo():
    engine = AgenticGraphSwarmEngine()
    print("=" * 85)
    print("  ENTERPRISE AGENTIC MESH & HIGH-FREQUENCY SWARM ORCHESTRATION HARNESS")
    print("=" * 85)
    suite = engine.generate_synthetic_benchmark_suite()

    # 1. Attention Routing
    res_att = engine.enterprise_mesh.route_context_attention(*suite["p4_attention"])
    print(f"[1] Context-Budgeted Attention: info_coverage={res_att.total_information_coverage}, "
          f"utilization={res_att.context_utilization_pct}% ({res_att.execution_time_us} µs)")

    # 2. Epistemic Consensus
    res_ep = engine.enterprise_mesh.resolve_epistemic_conflicts(suite["p3_consensus"])
    print(f"[2] Epistemic Consensus: statements={len(res_ep.consensus_graph)}, "
          f"kemeny_dist={res_ep.kemeny_distance} ({res_ep.execution_time_us} µs)")

    # 3. Sandbox Tool Scheduling
    res_sched = engine.enterprise_mesh.schedule_tool_sandboxes(*suite["p6_tool"])
    print(f"[3] Multi-Tool Sandbox Dispatch: makespan={res_sched.makespan_ms}ms, "
          f"deadlock_free={res_sched.deadlock_free_certified} ({res_sched.execution_time_us} µs)")

    # 4. Topology Evolution
    res_topo = engine.enterprise_mesh.evolve_communication_mesh(suite["p8_topology"][0], 10)
    print(f"[4] Evolutionary Graph Grammar: fitness={res_topo.best_fitness}, "
          f"pareto_size={res_topo.pareto_frontier_size} ({res_topo.execution_time_us} µs)")

    # 5. Pareto Game Theory
    res_game = engine.enterprise_mesh.negotiate_pareto_resource_split(*suite["p10_game"])
    print(f"[5] Hypergraph Pareto Coordination: social_welfare={res_game.expected_social_welfare}, "
          f"pareto_ok={res_game.pareto_efficient} ({res_game.execution_time_us} µs)")
    print("=" * 85)


def main():
    parser = argparse.ArgumentParser(description="Agentic Graph Swarm Kernel CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("benchmark-all", help="Benchmark all 10 NP-hard Agentic Graph Swarm solvers")
    subparsers.add_parser("world-sim-demo", help="Run Digital Parallel World Simulator demo")
    subparsers.add_parser("enterprise-mesh-demo", help="Run Enterprise Agentic Mesh demo")

    args = parser.parse_args()
    if args.command == "benchmark-all" or args.command is None:
        run_benchmark_all()
    elif args.command == "world-sim-demo":
        run_world_sim_demo()
    elif args.command == "enterprise-mesh-demo":
        run_enterprise_mesh_demo()


if __name__ == "__main__":
    main()
