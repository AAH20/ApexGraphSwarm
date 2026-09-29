# ADR-018: Provider receipt normalization with reconciliation boundary

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must track costs from multiple providers (OpenRouter, vLLM, subscription services) with different billing models. Provider receipts must be normalized into a common format, but the system cannot reverse charges or guarantee that provider invoices match internal estimates.

## Decision

**Provider receipts are normalized into integer micro-USD, with an explicit reconciliation boundary.** Key characteristics:

- **OpenRouter usage receipts**: Normalized into the execution ledger's integer micro-USD accounting.
- **Provider invoice reconciliation**: Separate from receipt normalization; the system does not claim that internal estimates match provider invoices.
- **Unknown costs remain unknown**: If a provider receipt is unavailable or ambiguous, the cost remains unknown and blocks promotion.
- **No automatic replay**: "Ambiguous external completion or spend requires reconciliation instead of automatic replay."
- **Subscription vs. API billing**: Subscription access uses supported authenticated clients; it is not interchangeable with provider API billing.

**Receipt fields:**
- `tokenUsage` is the one permitted token-related receipt field in checkpoints, with intentionally narrow schema.
- Settlement receipts record actual cost in integer micro-USD.
- Unresolved liabilities remain unknown until reconciled.

## Alternatives considered

1. **Automatic invoice matching**: Would be convenient but is unreliable; provider invoices may differ from estimates due to retries, failed runs, or pricing changes.
2. **No receipt tracking**: Would simplify the system but would prevent cost-aware delegation and budget enforcement.
3. **Provider-specific cost models**: Would be more accurate but would couple the system to specific provider APIs.

## Consequences

- **Positive**: Common cost format; clear reconciliation boundary; honest handling of unknown costs; no false precision.
- **Negative**: Reconciliation requires manual intervention; provider invoices may not match estimates; subscription billing is not interchangeable with API billing.
- **Critical statement**: "Accounting cannot reverse a charge already made by a provider."

## Related

- ADR-003 (SQLite control plane)
- ADR-009 (execution classes)
- ADR-011 (integer micro-USD cost accounting)
- ADR-012 (explicit adapter pattern)
