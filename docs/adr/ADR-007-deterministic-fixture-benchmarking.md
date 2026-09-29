# ADR-007: Deterministic fixture-based benchmarking

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must be verifiable without requiring paid model calls, external services, or non-deterministic inputs. Regression tests, scheduler benchmarks, and optimization experiments must produce consistent, reproducible results that can be checked into the repository.

## Decision

**All benchmarks and regression tests use deterministic fixtures.** Key characteristics:

- **Zero-cost fixture work**: The `fixture` execution class is explicitly deterministic and zero-cost. Expired leases may be retried automatically while attempts remain.
- **Synthetic data**: Analytics, optimization, and evolution experiments use synthetic data that is clearly labeled as such.
- **Sealed fixtures**: The evolution experiment generates sealed task splits that are hashed but never passed to a solver, enabling independent evaluation.
- **Reproducible artifacts**: Benchmark outputs include source hashes, environment details, seed, configuration, timing, accounting, and recovery checks.
- **No paid model runs**: The regression suite requires no paid model run. Tests use harmless subprocesses and loopback sockets where required.

**Largest measured fixture (2026-09-27):**

| Measure | Recorded result |
|---------|----------------|
| Logical agents | 300 |
| Fixture tasks | 600 |
| Active worker limit / observed peak | 32 / 32 |
| Elapsed time | 6,267.171 ms |
| Duplicate completions | 0 |
| Provider calls / API spend | 0 / $0 |
| Recovery checks | Reopen, recovery completion, and stale-lease fencing recorded |

## Alternatives considered

1. **Live model benchmarks**: Would measure real model intelligence but are non-deterministic, expensive, and require credentials.
2. **External benchmark suites (PSPLIB, GraphRAG-Bench)**: Would provide standardized comparisons but require external data and are not always locally reproducible.
3. **No benchmarks**: Would simplify the codebase but would make regression detection and performance tracking impossible.

## Consequences

- **Positive**: Reproducible results; no credential requirements; fast regression testing; clear separation between local fixture results and live model performance.
- **Negative**: Fixture results do not measure model intelligence, real infrastructure control, or superiority over other frameworks; synthetic timings are not live performance.
- **Critical distinction**: "This measures SQLite orchestration of harmless fixed tasks. It does not measure model intelligence, 300 simultaneous model calls, real infrastructure control, or superiority over another orchestration framework."

## Related

- ADR-006 (bounded execution model)
- ADR-009 (execution classes)
- ADR-013 (evaluation and promotion gates)
