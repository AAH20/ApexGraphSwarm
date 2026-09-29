# ADR-009: Execution classes with explicit retry semantics

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

Tasks in the control plane have different risk profiles. Some are safe to retry automatically (deterministic fixtures), while others may have already caused external side effects (paid API calls, infrastructure changes). The system must distinguish between these cases and handle retries appropriately.

## Decision

**Four execution classes** define retry semantics:

| Class | Description | Retry behavior |
|-------|-------------|----------------|
| `fixture` | Explicitly deterministic, zero-cost local fixture work | Expired leases may be retried automatically while attempts remain |
| `local_idempotent` | Operator asserts repeat execution is safe | Nonzero/unknown-cost interrupted execution still requires reconciliation |
| `external_idempotent` | Operator asserts adapter uses provider-side idempotency | Explicit worker-reported retryable failure may retry, subject to remaining reservation; crashed request still requires reconciliation |
| `external` | Default and safest class | No automatic retry after ambiguous worker crash or cancellation |

**Key principle**: "Mark work as fixture only when it truly cannot call a paid service or cause external side effects. The control plane trusts the adapter's class declaration; it cannot inspect arbitrary callback code."

**Reconciliation**: Ambiguous external work moves to `needs_reconciliation`. Its unspent reservation remains held and the run cannot claim more work. Reconciliation requires known actual cost and is itself transactional. Outcomes are `succeeded`, `failed`, or `not_started`.

## Alternatives considered

1. **Single execution class**: Would be simpler but would either over-retry (risking duplicate charges) or under-retry (losing work that could be safely retried).
2. **Automatic retry for all classes**: Would maximize throughput but risks duplicate charges and side effects for external work.
3. **No automatic retry (all manual)**: Would be safest but would lose work that could be safely retried, requiring manual intervention for fixture work.

## Consequences

- **Positive**: Clear retry semantics; safe handling of external work; fixture work recovers automatically; reconciliation preserves unspent reservations.
- **Negative**: Operators must correctly classify work; misclassification can lead to duplicate charges or lost work; reconciliation requires manual intervention.
- **Critical rule**: "A crashed request still requires reconciliation because actual use may be unknown."

## Related

- ADR-003 (SQLite control plane)
- ADR-006 (bounded execution model)
- ADR-008 (lease-based task claiming)
- ADR-011 (cost accounting)
