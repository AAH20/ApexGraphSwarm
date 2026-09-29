# ADR-011: Integer micro-USD cost accounting

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must track costs precisely without floating-point rounding errors. Costs must be known at admission time (as reservations) and settled after execution. Unknown costs must remain unknown — they cannot be represented as zero.

## Decision

**Integer micro-USD (millionths of a USD) is the sole currency unit.** Key characteristics:

- **Reservation at admission**: Paid work must carry an explicit integer micro-USD reservation. Unknown price/usage cannot be represented as zero.
- **Budget enforcement**: The sum of admitted reservations may not exceed the run budget.
- **Settlement**: Actual cost is recorded in integer micro-USD after execution.
- **Overrun handling**: If actual cost exceeds its task reservation, the scheduler records the spend, sets `budgetExceeded`, moves the run to `budget_exceeded`, and blocks further claims. This records a breach; it cannot undo an external provider charge.
- **Unknown costs remain unknown**: "Unknown costs remain unknown" is a core principle. Estimates are not provider billing caps.

**Cost planning relationships:**

```
API estimate = sum(billable units × applicable rate)
Total operating cost = API + compute + retrieval/storage + tools + allocated fixed costs
Cost per successful result = total operating cost / successful results
Contribution per result = revenue per result − attributable variable cost per result
```

## Alternatives considered

1. **Floating-point dollars**: Would be simpler but introduces rounding errors that accumulate across many transactions.
2. **Provider-specific currencies**: Would complicate reconciliation and comparison.
3. **No cost tracking**: Would be simpler but would prevent budget enforcement and cost-aware delegation.

## Consequences

- **Positive**: Precise accounting; no floating-point errors; clear budget enforcement; honest handling of unknown costs.
- **Negative**: All costs must be converted to micro-USD; estimates must be reconciled against actual receipts; unknown costs block execution.
- **Critical rule**: "Accounting cannot reverse a charge already made by a provider."

## Related

- ADR-003 (SQLite control plane)
- ADR-006 (bounded execution model)
- ADR-009 (execution classes)
