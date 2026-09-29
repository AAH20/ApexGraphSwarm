# ADR-024: Execution graph as read-only projection

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must provide a visual explanation of control-plane history, connecting logical agents, tasks, attempts, authenticated workers, principals, grants, specialist contract bindings, and resources. This must be a read-only projection that does not expose sensitive data.

## Decision

**The execution graph is a bounded, read-only projection of control-plane history.** Key characteristics:

- **Read-only**: "The projection exposes identifiers, states, safe accounting summaries and relationship edges. It deliberately never copies task payloads, result bodies, errors, receipts, checkpoints or lease credentials into the graph."
- **Bounded**: Default 500 nodes / 1,000 edges; maximum 5,000 nodes / 10,000 edges; maximum 20,000 source rows.
- **Node prioritization**: Run, tasks, persisted attempts, then attribution/resource identities.
- **Edge omission**: Edges whose endpoints are absent because of truncation are omitted.
- **Explicit limitations**:
  - "This is a projection of persisted control-store status and ledger receipts, not a live execution trace."
  - "Attempts without persisted ledger rows are reported as missing coverage; no historical attempt or cost is fabricated."
  - "Known actual cost includes only recorded integer micro-USD receipts; unresolved liabilities remain unknown."

## Alternatives considered

1. **Full data exposure**: Would enable more analysis but would risk credential and payload leakage.
2. **No execution graph**: Would simplify the system but would prevent visual explanation of control-plane history.
3. **Live execution trace**: Would be more real-time but would couple the graph to the control plane's live state.

## Consequences

- **Positive**: No sensitive data exposure; bounded resource usage; clear limitations; no fabricated history.
- **Negative**: Not a live trace; missing ledger rows are reported as coverage gaps; truncated graphs omit edges.
- **Critical statement**: "Attempts without persisted ledger rows are reported as missing coverage; no historical attempt or cost is fabricated."

## Related

- ADR-003 (SQLite control plane)
- ADR-006 (bounded execution model)
- ADR-015 (read-only analytics)
