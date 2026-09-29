# ADR-016: Bounded local optimization without code generation

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must provide optimization capabilities (scheduling, evidence selection, coverage, delegation planning) without executing arbitrary code, contacting providers, or generating code. Optimization must be deterministic, bounded, and produce plans that can be reviewed before execution.

## Decision

**Optimization is bounded, deterministic, and plan-only.** Key characteristics:

- **No code execution**: "These functions produce plans and recommendations only. They never execute work, contact providers, inspect Git state, or infer prices/telemetry that were not supplied by the caller."
- **Bounded search**: Exact search is limited to 8 tasks, 18 coverage items, 65,536 combinations, and 200,000 nodes. Greedy fallback for larger instances.
- **Synthetic fixtures**: Optimization experiments use synthetic data that is clearly labeled; unknown monetary costs withhold promotion.
- **Configuration search, not code generation**: The evolution experiment runs a fixed weighted-max-coverage greedy implementation with a small supported exponent grid (0.0, 0.5, 1.0, 1.5). It is configuration search, not code generation.
- **Sealed fixtures**: The sealed split is generated and hashed but never passed to a solver, enabling independent evaluation.

**Optimization workstreams:**

| Workstream | Scope boundary |
|------------|---------------|
| Execution ledger | Stable attempt identities, task/tool/resource attribution, settlement receipts, retry accounting |
| Exact access grants | Principal/tool/resource matching, expiry, revocation, cumulative reserved/settled budget |
| Scheduling and delegation | Dependency/model-capacity/budget/deadline constraints, bounded exact search, compiled review plans |
| Evidence selection | Weighted coverage under token budgets, exact small-instance oracle and greedy fallback |
| Coding swarm planning | Dependency-respecting waves, declared access conflicts, committed Git diffs with stale/tamper rechecks |
| Evaluation and evolution | Versioned task splits, training selection, held-out gates, bounded local greedy configuration search |
| Inference capacity | Recommendations over supplied measurements plus optional bounded vLLM metrics collection |

## Alternatives considered

1. **Arbitrary code execution**: Would enable more optimization strategies but would be unsafe and unbounded.
2. **Live provider calls**: Would enable real-time optimization but would be expensive and non-deterministic.
3. **No optimization**: Would simplify the system but would prevent cost-aware delegation and scheduling.

## Consequences

- **Positive**: Safe, deterministic, reproducible; no provider calls; no code generation; clear scope boundaries.
- **Negative**: Limited to supplied data; no live optimization; synthetic results do not measure real performance.
- **Critical statement**: "No arbitrary code, provider, network, repository, or promotion side effect is executed."

## Related

- ADR-002 (stdlib-only control plane)
- ADR-006 (bounded execution model)
- ADR-007 (deterministic fixture benchmarking)
- ADR-013 (evaluation and promotion gates)
