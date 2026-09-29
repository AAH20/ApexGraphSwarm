# ADR-035: Verification via Python and web test suites

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must be verifiable through automated tests. The Python control plane and web frontend have separate test suites that must both pass. Tests must be deterministic, fast, and must not require paid model calls or external services.

## Decision

**Verification uses separate Python and web test suites with deterministic fixtures.** Key characteristics:

- **Python tests**: `python3 -m unittest discover tests` runs the Python regression suite (214 tests as of 2026-09-27).
- **Web tests**: `npm --prefix apps/web test` runs the web/domain/adapter tests (183 tests as of 2026-09-27).
- **Type checking**: `npm --prefix apps/web run typecheck` validates TypeScript types.
- **Production build**: `npm --prefix apps/web run build` verifies the production build.
- **No paid model runs**: "No paid model model run is required for the regression suite."
- **Harmless subprocesses**: "Tests use harmless subprocesses and loopback sockets where required."

**Test coverage areas:**
- Repository graph analysis
- Control plane (SQLite scheduler)
- Specialist access contracts
- Optimization and evolution
- Evaluation and promotion gates
- Analytics
- Delegation planning
- Hierarchy planning
- Execution graph projection
- Provider receipts
- Inference telemetry
- Web components and API routes

## Alternatives considered

1. **Manual testing only**: Would be more flexible but would be slow, error-prone, and non-reproducible.
2. **Live service integration tests**: Would be more realistic but would be slow, expensive, and non-deterministic.
3. **No tests**: Would be faster to develop but would risk regressions and bugs.

## Consequences

- **Positive**: Reproducible verification; fast regression detection; no credential requirements; clear test coverage.
- **Negative**: Tests must be maintained; some edge cases may not be covered; test timing is machine-dependent.
- **Critical statement**: "Test timing is machine-dependent; consult the recorded environment and workload when comparing results."

## Related

- ADR-002 (stdlib-only control plane)
- ADR-004 (Next.js web frontend)
- ADR-007 (deterministic fixture benchmarking)
- ADR-013 (evaluation and promotion gates)
