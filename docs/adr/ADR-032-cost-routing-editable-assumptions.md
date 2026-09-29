# ADR-032: Cost routing with editable assumptions and unknown preservation

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must support cost-aware delegation planning with editable rate assumptions, token estimates, and cost-per-successful-result calculations. However, estimates must not be mistaken for provider billing caps, and unknown costs must remain unknown.

## Decision

**Cost routing exposes editable assumptions and preserves unknown costs.** Key characteristics:

- **Editable rates**: Token rates, input/output/cache assumptions, fanout, retries, success rate, monthly volume, subscriptions, GPU allocation, fixed operating costs, retrieval/indexing expenses, revenue, and budget constraints are all editable.
- **Dated rates**: Rates are dated and editable; users must understand when rates were last updated.
- **Unknown preservation**: "Unknown costs remain unknown." Estimates are not provider billing caps.
- **No execution**: "A routing plan or cost scenario does not itself change provider routing or execute models."

**Cost planning relationships:**

```
API estimate = sum(billable units × applicable rate)
Total operating cost = API + compute + retrieval/storage + tools + allocated fixed costs
Cost per successful result = total operating cost / successful results
Contribution per result = revenue per result − attributable variable cost per result
```

## Alternatives considered

1. **Fixed rates**: Would be simpler but would become outdated and misleading.
2. **Automatic rate fetching**: Would be more accurate but would require network access and provider APIs.
3. **Estimates as billing caps**: Would be dangerous; estimates are not provider billing caps.

## Consequences

- **Positive**: Flexible planning; explicit assumptions; honest handling of unknown costs; no false precision.
- **Negative**: Requires manual rate updates; estimates are not billing caps; no automatic execution.
- **Critical statement**: "Actual costs stay unknown unless independently measured; an estimate is not a provider billing cap."

## Related

- ADR-011 (integer micro-USD cost accounting)
- ADR-012 (explicit adapter pattern)
- ADR-018 (provider receipt normalization)
- ADR-020 (decision intelligence structured tool)
