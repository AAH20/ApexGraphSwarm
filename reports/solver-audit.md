# NP-Hard Solver Kernel Audit Report

**Project:** ApexGraphSwarm  
**Date:** 2026-09-29  
**Scope:** All NP-hard solver kernels — algorithms, complexity, bottlenecks, optimization opportunities

---

## Executive Summary

Audited **43 solver kernels** across 5 modules. All solvers address NP-hard or harder problems (PPAD-complete, APX-hard, NP-complete). The majority use greedy heuristics, local search, or exhaustive enumeration. Common bottlenecks include: repeated expensive computations (cycle detection, BFS, LOS ray-casting), lack of incremental updates, fixed iteration counts without convergence detection, and absence of pruning or bounding strategies.

---

## 1. agentic_graph_swarm_kernel (10 solvers)

### 1.1 budgeted_attention_routing.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Budgeted Maximum Submodular Coverage |
| **Algorithm** | Greedy density-sorted packing (entropy/token_length) |
| **Complexity** | O(N log N + N·A) — N=nodes, A=agents |
| **Bottleneck** | Per-agent sequential packing with no cross-agent deduplication; overlapping concepts routed to multiple agents |
| **Optimization** | Lazy greedy with priority queues; cross-agent concept deduplication; submodular knapsack DP for small instances |

### 1.2 byzantine_epistemic_filter.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Truth Discovery + Byzantine Consensus |
| **Algorithm** | Iterative trust-weighted voting with spectral trimming |
| **Complexity** | O(I·C·A) — I=iterations (fixed 20), C=claims, A=agents |
| **Bottleneck** | Fixed iteration count without convergence detection; O(C) claim grouping rebuilt every iteration |
| **Optimization** | Early termination on convergence (ε=1e-4); cache claim groupings; parallel trust updates |

### 1.3 causal_dag_synthesis.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Bayesian Causal DAG Structure Learning |
| **Algorithm** | Greedy edge addition with DFS cycle detection + BIC penalty |
| **Complexity** | O(E·(V+E)) — E=candidate edges, V=variables; DFS cycle check O(V+E) per edge |
| **Bottleneck** | DFS cycle detection on every candidate edge trial — O(V+E) per edge |
| **Optimization** | Incremental cycle detection via union-find with rollback; topological order maintenance; score caching |

### 1.4 disjunctive_tool_scheduler.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Job-Shop Scheduling (J_m \| prec \| C_max) |
| **Algorithm** | Topological sort + list scheduling with resource contention |
| **Complexity** | O(V + E + V·R) — V=tasks, E=dependencies, R=resources |
| **Bottleneck** | Name says "Shifting-Bottleneck" but implementation is simple list scheduling; no bottleneck machine identification |
| **Optimization** | Implement shifting-bottleneck heuristic; priority-based dispatching; resource leveling |

### 1.5 epistemic_consensus.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Kemeny-Young Graph Consensus |
| **Algorithm** | Weighted Borda aggregation with conflict detection |
| **Complexity** | O(G·S) — G=graphs, S=statements per graph |
| **Bottleneck** | Only detects direct subject-predicate conflicts; no full Kemeny-Young optimization |
| **Optimization** | Full Kemeny-Young with branch-and-bound for small instances; Borda is only a heuristic |

### 1.6 game_theoretic_hypergraph_nash.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Polymatrix Hypergraph Nash Equilibrium (PPAD-complete) |
| **Algorithm** | Regret Matching+ with iterative strategy updates |
| **Complexity** | O(I·P·H·A^H) — I=iterations (50), P=players, H=hyperedges, A=actions; exponential in hyperedge arity |
| **Bottleneck** | Joint action space A^H explodes with hyperedge size; fixed 50 iterations |
| **Optimization** | Monte Carlo regret matching; early convergence detection; factored payoff representation |

### 1.7 graph_grammar_evolution.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Multi-Objective Graph Architecture Search |
| **Algorithm** | Evolutionary algorithm with crossover and mutation |
| **Complexity** | O(G·P·N²) — G=generations, P=population, N=agents; BFS for path length per fitness eval |
| **Bottleneck** | BFS from every node for average path length → O(N·(N+E)) per fitness evaluation |
| **Optimization** | Precompute all-pairs shortest paths once; use spectral methods (algebraic connectivity) as proxy |

### 1.8 hypergraph_csg.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Coalition Structure Generation (CSG) |
| **Algorithm** | Greedy with inverted capability index and lazy heap |
| **Complexity** | O(E·(K + M log M)) — E=hyperedges, K=caps per edge, M=relevant agents |
| **Bottleneck** | Greedy doesn't guarantee optimal partition; no branch-and-bound |
| **Optimization** | DP over subsets for small instances; branch-and-bound with upper bounds (e.g., fractional relaxation) |

### 1.9 spectral_memory_decay.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Spectral Hypergraph Sparsification + Memory Decay |
| **Algorithm** | Effective resistance sampling with temporal decay |
| **Complexity** | O(N + E·R) — R=effective resistance computations (requires Laplacian solve) |
| **Bottleneck** | Effective resistance computation requires solving Laplacian system — O(N³) naive |
| **Optimization** | Spielman-Srivastava spectral sparsification with random projections; nearly-linear time solvers |

### 1.10 temporal_subgraph_detector.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Temporal Subgraph Isomorphism |
| **Algorithm** | DFS with temporal ordering constraints |
| **Complexity** | O(E^S) — E=events, S=sequence length; exponential in pattern size |
| **Bottleneck** | No pruning beyond temporal ordering; exhaustive DFS |
| **Optimization** | VF2-style pruning with degree constraints; indexing by action type; parallel matching |

---

## 2. agentic_np_hard_kernel (10 solvers)

### 2.1 byzantine_consensus.py
| Aspect | Detail |
|--------|--------|
| **Problem** | 3-Phase BFT State Machine Replication |
| **Algorithm** | Merkle tree voting with equivocation detection |
| **Complexity** | O(R) — R=receipts |
| **Bottleneck** | Single-threaded vote tallying; no parallel verification |
| **Optimization** | Parallel Merkle verification; batch signature checking; incremental receipt processing |

### 2.2 fault_tolerant_dag.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Self-Healing DAG Reconfiguration |
| **Algorithm** | Fallback substitution + full re-synthesis |
| **Complexity** | O(V + E) for re-synthesis |
| **Bottleneck** | Full DAG re-synthesis on every failure; no incremental repair |
| **Optimization** | Incremental rescheduling; cache critical path; only recompute affected subgraph |

### 2.3 least_privilege_rbac.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Minimum Risk Capability Set Cover |
| **Algorithm** | Greedy set cover with MRV heuristic |
| **Complexity** | O(R·C) — R=requirements, C=candidates |
| **Bottleneck** | Greedy doesn't guarantee minimum risk; no LP relaxation |
| **Optimization** | LP relaxation with rounding; branch-and-bound for exact solutions |

### 2.4 pareto_model_router.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Pareto-Optimal Model Selection |
| **Algorithm** | Non-dominated sorting |
| **Complexity** | O(M²) — M=models |
| **Bottleneck** | Quadratic pairwise comparison |
| **Optimization** | NSGA-II or sorting-based approaches; incremental Pareto frontier maintenance |

### 2.5 prefix_kv_cache.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Prefix-based KV Cache Deduplication |
| **Algorithm** | Trie-based prefix matching |
| **Complexity** | O(T·L) — T=tokens, L=prefix length |
| **Bottleneck** | Linear scan for prefix matching |
| **Optimization** | Radix tree or hash-based lookup; suffix automaton |

### 2.6 sandbox_resource_scheduler.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Resource Scheduling with Exclusive Locks |
| **Algorithm** | LPT-based list scheduling with lock contention |
| **Complexity** | O(R·L) — R=requests, L=locks |
| **Bottleneck** | No deadlock prevention beyond ordering; greedy lock assignment |
| **Optimization** | Banker's algorithm for deadlock avoidance; constraint programming |

### 2.7 speculative_tree.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Speculative Decoding Tree Construction |
| **Algorithm** | Beam search with probability thresholds |
| **Complexity** | O(B·D) — B=beam width, D=depth |
| **Bottleneck** | Fixed beam width; no adaptive expansion |
| **Optimization** | Adaptive beam search; pruning with confidence bounds; learned tree policies |

### 2.8 submodular_memory.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Submodular Memory Selection |
| **Algorithm** | Lazy greedy submodular maximization |
| **Complexity** | O(N·K) — N=items, K=selection size |
| **Bottleneck** | Repeated marginal gain computation |
| **Optimization** | Stochastic greedy; distributed greedy; CELF++ optimization |

### 2.9 tool_routing.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Tool Selection and Routing |
| **Algorithm** | Constraint satisfaction with greedy assignment |
| **Complexity** | O(T·C) — T=tools, C=capabilities |
| **Bottleneck** | No backtracking on constraint violation |
| **Optimization** | CSP with backtracking; SAT encoding; graph neural network routing |

### 2.10 workflow_dag.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Workflow DAG Synthesis |
| **Algorithm** | Critical Path Method (CPM) |
| **Complexity** | O(V + E) |
| **Bottleneck** | No resource leveling; simple CPM without resource constraints |
| **Optimization** | Resource leveling heuristics; PERT for uncertainty; RCPSP solvers |

---

## 3. datacenter_np_hard_kernel (7 solvers)

### 3.1 bgp_a2a_orchestrator.py
| Aspect | Detail |
|--------|--------|
| **Problem** | BGP Anycast Orchestration |
| **Algorithm** | Greedy anycast assignment |
| **Complexity** | O(N·P) — N=prefixes, P=PoPs |
| **Bottleneck** | No latency-aware optimization; static assignment |
| **Optimization** | Latency-constrained assignment; ILP; real-time latency feedback |

### 3.2 bgp_microloop_reroute.py
| Aspect | Detail |
|--------|--------|
| **Problem** | BGP Microloop Prevention |
| **Algorithm** | Shortest path recomputation |
| **Complexity** | O(E + V log V) per reroute |
| **Bottleneck** | Full recomputation; no incremental update |
| **Optimization** | Incremental shortest path (LPA*); partial recomputation |

### 3.3 collective_allreduce_topology.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Collective Communication Topology |
| **Algorithm** | Ring-based allreduce with topology awareness |
| **Complexity** | O(G) — G=GPUs |
| **Bottleneck** | Fixed ring; no hierarchical optimization |
| **Optimization** | Hierarchical allreduce; recursive halving; topology-aware ring construction |

### 3.4 erasure_coding_hypergraph.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Erasure Coding Placement |
| **Algorithm** | LRC chunk generation with fault-domain grouping |
| **Complexity** | O(C) — C=chunks |
| **Bottleneck** | No optimization of placement; round-robin assignment |
| **Optimization** | Constraint-based placement; network flow for fault-domain balancing |

### 3.5 optical_traffic_engineering.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Multi-Commodity Flow (NP-Complete) |
| **Algorithm** | Garg-Könemann FPTAS with Dijkstra |
| **Complexity** | O(I·E·log V) — I=iterations |
| **Bottleneck** | Fixed iteration count; no warm starting |
| **Optimization** | Warm starting from previous solution; column generation; path-based formulation |

### 3.6 power_thermal_scheduler.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Power/Thermal Job Scheduling (RCPSP) |
| **Algorithm** | Greedy temporal shifting with carbon awareness |
| **Complexity** | O(J·T) — J=jobs, T=time slots |
| **Bottleneck** | No spatial optimization; greedy assignment |
| **Optimization** | LP relaxation; constraint programming; multi-objective optimization |

### 3.7 vector_bin_packing.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Multi-Dimensional Vector Bin Packing (APX-Hard) |
| **Algorithm** | Tetris cosine alignment with first-fit |
| **Complexity** | O(N·M) — N=items, M=bins |
| **Bottleneck** | First-fit decreasing; no best-fit or optimization |
| **Optimization** | Best-fit decreasing; branch-and-bound; approximation schemes (AFPTAS) |

---

## 4. geospatial_np_hard_kernel (10 solvers)

### 4.1 colocation_mining.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Spatial Co-Location Pattern Mining |
| **Algorithm** | Apriori-like candidate generation with PI pruning |
| **Complexity** | O(N²·2^T) — N=instances, T=types; exponential in pattern size |
| **Bottleneck** | Candidate generation explodes with pattern size |
| **Optimization** | FP-growth style; sampling-based; parallel candidate evaluation |

### 4.2 dubins_uav_path.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Dubins TSP with Neighborhoods + Threat Avoidance |
| **Algorithm** | 2-opt local search with arc-tangent heading relaxation |
| **Complexity** | O(I·N²) — I=iterations, N=waypoints |
| **Bottleneck** | 2-opt is local optimum prone; no global optimization |
| **Optimization** | LKH heuristic; genetic algorithm; simulated annealing |

### 4.3 evacuation_routing.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Time-Dependent Evacuation Routing (TD-VRPTW) |
| **Algorithm** | Dynamic shortest path with capacity constraints |
| **Complexity** | O(Z·(E + V log V)) — Z=zones |
| **Bottleneck** | Independent per-zone routing; no global coordination |
| **Optimization** | System-optimal assignment; congestion pricing; iterative user-equilibrium |

### 4.4 facility_location.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Capacitated p-Median (CPMP) |
| **Algorithm** | Teitz-Bart vertex substitution |
| **Complexity** | O(I·N·P) — I=iterations, N=candidates, P=facilities |
| **Bottleneck** | Local search; no global optimization guarantee |
| **Optimization** | Lagrangian relaxation; branch-and-price; metaheuristics (VNS, tabu) |

### 4.5 label_placement.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Cartographic Label Placement (MWIS) |
| **Algorithm** | Greedy independent set with position weights |
| **Complexity** | O(F·P·L) — F=features, P=positions (8), L=labels |
| **Bottleneck** | Greedy; no backtracking |
| **Optimization** | Branch-and-bound; simulated annealing; graph coloring reduction |

### 4.6 line_simplification.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Min-Vertex Polyline Simplification (Imai-Iri) |
| **Algorithm** | Dynamic programming with Fréchet error bound |
| **Complexity** | O(N³) — N=points |
| **Bottleneck** | Cubic time; no approximation for large N |
| **Optimization** | Approximation algorithms (e.g., Douglas-Peucker variant); parallel DP; output-sensitive |

### 4.7 satellite_tasking.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Agile Earth Observation Satellite Scheduling (AEOSSP) |
| **Algorithm** | Time-indexed insertion heuristic |
| **Complexity** | O(T²·I) — T=targets, I=insertion positions |
| **Bottleneck** | Greedy insertion; no look-ahead |
| **Optimization** | Look-ahead; constraint programming; metaheuristics (GRASP, ALNS) |

### 4.8 spatial_weights.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Spatial Weights Matrix Optimization |
| **Algorithm** | k-NN with Moran's I evaluation |
| **Complexity** | O(K·N²) — K=candidate k values, N=features |
| **Bottleneck** | Brute-force k-NN; no spatial index |
| **Optimization** | KD-tree or ball tree; approximate NN (LSH); parallel distance computation |

### 4.9 territorial_districting.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Spatial Contiguity-Constrained Districting |
| **Algorithm** | Seed growing + boundary exchange |
| **Complexity** | O(N²·K) — N=tracts, K=districts |
| **Bottleneck** | Greedy region growing; no simulated annealing |
| **Optimization** | Simulated annealing; graph partitioning (METIS); multi-level refinement |

### 4.10 viewshed_siting.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Terrain Viewshed Sensor Placement |
| **Algorithm** | Submodular greedy set cover with (1-1/e) guarantee |
| **Complexity** | O(K·C·G) — K=sensors, C=candidates, G=grid cells |
| **Bottleneck** | LOS computation for every candidate-target pair — O(C·G·D) where D=ray steps |
| **Optimization** | R-tree indexing; parallel ray casting; GPU acceleration; horizon-based pruning |

---

## 5. frontier_ai_compiler_kernel (6 solvers)

### 5.1 cowos_chiplet_floorplanner.py
| Aspect | Detail |
|--------|--------|
| **Problem** | 2.5D/3D Multi-Chiplet Floorplanning |
| **Algorithm** | Heuristic placement with 2D Gaussian thermal model |
| **Complexity** | O(D²) — D=dies |
| **Bottleneck** | Fixed placement strategy (symmetric HBM flanking); no optimization search |
| **Optimization** | Simulated annealing; analytical placement; thermal-aware optimization loop |

### 5.2 flash_attention_sram_tiling.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Polyhedral Loop Tiling + SRAM Bank Conflict Elimination (NP-Complete) |
| **Algorithm** | Exhaustive search over tile sizes and padding |
| **Complexity** | O(T·P·32) — T=tile configs, P=padding values (0-16) |
| **Bottleneck** | Exhaustive search; no analytical solution for bank conflict-free swizzling |
| **Optimization** | Analytical bank conflict formula; constraint solving; XOR-based swizzle patterns |

### 5.3 kv_cache_submodular_eviction.py
| Aspect | Detail |
|--------|--------|
| **Problem** | KV-Cache Dynamic Attention Submodular Eviction |
| **Algorithm** | Greedy attention-weighted selection with sink/window preservation |
| **Complexity** | O(T log T) — T=tokens |
| **Bottleneck** | Sorting all tokens; no incremental update |
| **Optimization** | Incremental heap; approximate attention; token merging |

### 5.4 megatron_4d_parallelism.py
| Aspect | Detail |
|--------|--------|
| **Problem** | 4D Distributed Parallelism Partitioning (TP×PP×DP×CP) |
| **Algorithm** | Exhaustive search over valid (TP, PP, DP, CP) combinations |
| **Complexity** | O(D⁴) — D=divisors of GPU count |
| **Bottleneck** | Exhaustive enumeration; no pruning by cost model |
| **Optimization** | Constraint propagation; cost model pruning; dynamic programming over factorization |

### 5.5 moe_token_dispatch_balancer.py
| Aspect | Detail |
|--------|--------|
| **Problem** | MoE All-to-All Token Dispatch |
| **Algorithm** | Greedy capacitated bipartite matching |
| **Complexity** | O(T·E) — T=tokens, E=experts |
| **Bottleneck** | Greedy; no global optimization; token drops when capacity exceeded |
| **Optimization** | Hungarian algorithm; network flow; auxiliary routing optimization |

### 5.6 speculative_decoding_tree.py
| Aspect | Detail |
|--------|--------|
| **Problem** | Speculative Decoding Draft-Token Tree Scheduling |
| **Algorithm** | Priority queue-based tree expansion with KV budget |
| **Complexity** | O(N log N) — N=nodes |
| **Bottleneck** | Fixed KV budget; no adaptive allocation; no learned tree structure |
| **Optimization** | Adaptive budget; learned tree policies; draft model confidence calibration |

---

## Cross-Cutting Bottleneck Patterns

| Pattern | Affected Solvers | Impact |
|---------|-----------------|--------|
| **Repeated expensive computation** | causal_dag_synthesis (DFS cycle check), graph_grammar_evolution (BFS), viewshed_siting (LOS ray-cast) | O(N²) to O(N³) per iteration that could be O(1) amortized |
| **No incremental updates** | fault_tolerant_dag, bgp_microloop_reroute, kv_cache_submodular_eviction | Full recomputation on every change |
| **Fixed iteration counts** | byzantine_epistemic_filter (20), game_theoretic_hypergraph_nash (50), optical_traffic_engineering | Wasted computation or premature termination |
| **Greedy without bounding** | hypergraph_csg, least_privilege_rbac, moe_token_dispatch_balancer, vector_bin_packing | No optimality guarantee; can be arbitrarily bad |
| **Exhaustive enumeration** | flash_attention_sram_tiling, megatron_4d_parallelism, line_simplification | Doesn't scale beyond tiny instances |
| **No spatial indexing** | spatial_weights (k-NN), viewshed_siting (LOS), colocation_mining | O(N²) where O(N log N) possible |
| **Local search only** | dubins_uav_path (2-opt), facility_location (Teitz-Bart), territorial_districting | Local optima; no global guarantee |

---

## Priority Optimization Recommendations

### High Impact (fix first)
1. **causal_dag_synthesis** — Replace DFS cycle detection with union-find + rollback → O(E·α(V)) vs O(E·(V+E))
2. **viewshed_siting** — Add R-tree indexing + GPU ray casting → 10-100x speedup
3. **spatial_weights** — Add KD-tree for k-NN → O(N log N) vs O(N²)
4. **graph_grammar_evolution** — Precompute APSP once → O(N·(N+E)) once vs per fitness eval
5. **fault_tolerant_dag** — Incremental rescheduling → O(ΔV + ΔE) vs O(V + E)

### Medium Impact
6. **game_theoretic_hypergraph_nash** — Monte Carlo regret matching → handles larger hyperedges
7. **hypergraph_csg** — Branch-and-bound with upper bounds → optimality guarantee
8. **optical_traffic_engineering** — Warm starting → fewer iterations
9. **line_simplification** — Approximation algorithm → handles large polylines
10. **moe_token_dispatch_balancer** — Network flow → zero token drops

### Low Impact (polish)
11. Add convergence detection to all iterative solvers
12. Parallelize independent computations (byzantine_consensus, evacuation_routing)
13. Cache intermediate results (prefix_kv_cache, spectral_memory_decay)

---

## Summary Statistics

| Kernel | Solvers | Dominant Technique | Avg Complexity | Key Bottleneck |
|--------|---------|-------------------|----------------|----------------|
| agentic_graph_swarm | 10 | Greedy heuristics | O(N²) to O(2^N) | Repeated computation |
| agentic_np_hard | 10 | Greedy + local search | O(N²) to O(N³) | No incremental updates |
| datacenter_np_hard | 7 | Greedy + FPTAS | O(N²) to O(N³) | No warm starting |
| geospatial_np_hard | 10 | DP + greedy + local search | O(N²) to O(N³) | No spatial indexing |
| frontier_ai_compiler | 6 | Exhaustive search + greedy | O(N²) to O(D⁴) | No analytical solution |

**Total:** 43 solvers audited across 5 kernels. All address NP-hard or harder problems. The most common optimization opportunity is replacing repeated expensive computations with incremental or cached alternatives.
