# ADR-019: Swarm Arena as unsigned evidence sharing

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must allow users to share benchmark results with others for comparison. However, shared results must not be mistaken for verified leaderboard entries or authoritative performance claims.

## Decision

**Swarm Arena shares self-contained, unsigned evidence snapshots.** Key characteristics:

- **Self-contained report**: Share links contain a full report, run checksum, source hashes, and measurement environment.
- **No public leaderboard**: No result is uploaded to a public leaderboard.
- **Unsigned evidence**: "Treat a shared link as unsigned evidence and rerun it before relying on it."
- **Synthetic data**: Synthetic timings and microUSD inputs are not live model performance or provider prices.
- **Five-case deterministic fixture**: The Arena runs the versioned five-case synthetic optimization fixture.

**Largest measured fixture (2026-09-27):**

| Measure | Recorded result |
|---------|----------------|
| Logical agents | 300 |
| Fixture tasks | 600 |
| Active worker limit / observed peak | 32 / 32 |
| Elapsed time | 6,267.171 ms |
| Duplicate completions | 0 |
| Provider calls / API spend | 0 / $0 |

## Alternatives considered

1. **Public leaderboard**: Would enable comparison but would require verification, moderation, and could be gamed.
2. **No sharing**: Would simplify the system but would prevent collaborative evaluation.
3. **Signed/verified results**: Would require a trusted authority and infrastructure that is out of scope.

## Consequences

- **Positive**: Users can share results; self-contained reports include all context; no false precision; no public leaderboard to game.
- **Negative**: Shared results are unsigned; users must rerun before relying on them; no centralized comparison.
- **Critical statement**: "Treat a shared link as unsigned evidence and rerun it before relying on it."

## Related

- ADR-006 (bounded execution model)
- ADR-007 (deterministic fixture benchmarking)
- ADR-013 (evaluation and promotion gates)
