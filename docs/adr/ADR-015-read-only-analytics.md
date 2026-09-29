# ADR-015: Read-only analytics with explicit data boundaries

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must provide analytics over execution attempt ledgers (costs, outcomes, latency, tool/resource usage) without mutating the control plane database or exposing sensitive data. Analytics must be bounded, read-only, and clearly separated from execution.

## Decision

**Analytics is a read-only projection with explicit data boundaries.** Key characteristics:

- **No ControlStore import**: `analytics.py` intentionally does not import `ControlStore`; opening a ledger for analytics must never create, migrate, or mutate its database.
- **Bounded scans**: Live scans capped at 200,000 rows; imports capped at 10,000 rows; SQLite reads are batched; the capped selection is materialized in memory.
- **Event schema**: Analytics events have exactly `attemptId`, `taskId`, `tool`, `resource`, `startedAt`, `settledAt`, `outcome`, `actualCostMicrousd`. No payloads, results, errors, or credentials.
- **Outcomes**: `running`, `unknown`, `succeeded`, `failed`, `cancelled`, `not_started`, `expired_retryable`.
- **Opt-in refresh**: 30-second refresh while the page is visible; imports remain in memory and never write to the execution ledger.
- **Synthetic demo**: The explicitly labeled synthetic demo can be loaded without credentials; the private workspace token is required for read-only ledger analytics.

**Analytics capabilities:**
- Daily cost and attempt trends
- Tool/resource cohorts
- Latency distributions
- Pearson correlation and UTC activity heatmaps
- Seven-day linear spending baselines with chronological holdout MAE
- BI-style visualization gallery (pie/donut, bar/column, area/line/combo, treemap, waterfall, funnel, gauge, KPI, table, matrix, hierarchical)

## Alternatives considered

1. **Mutating analytics**: Would simplify read patterns but would risk corrupting the control plane database.
2. **No analytics**: Would simplify the system but would prevent cost tracking and performance analysis.
3. **External analytics service**: Would provide more features but would require network access and raise privacy concerns.

## Consequences

- **Positive**: Read-only safety; bounded resource usage; clear data boundaries; no credential exposure; works offline.
- **Negative**: Analytics is limited to the event schema; large datasets must be capped; no real-time streaming.
- **Critical statement**: "This is a bounded local analytics implementation, not a distributed warehouse or a calibrated predictive model."

## Related

- ADR-002 (stdlib-only control plane)
- ADR-003 (SQLite control plane)
- ADR-006 (bounded execution model)
- ADR-011 (integer micro-USD cost accounting)
