# ADR-013: Versioned evaluation with held-out promotion gates

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must evaluate candidate configurations (routing, team structures, optimization parameters) and decide whether to promote them. Evaluation must be rigorous, reproducible, and must not promote configurations that have unknown costs or that fail on held-out tasks.

## Decision

**Versioned, paired evaluation with held-out promotion gates** is the evaluation framework:

- **Versioned suites**: Each evaluation suite has a `suiteId`, `suiteVersion`, `tasksetId`, `tasksetVersion`, `evaluatorId`, and `evaluatorVersion`.
- **Task splits**: Tasks are divided into `train`, `heldout`, and `sealed` splits. The sealed split is generated and hashed but never passed to a solver.
- **Promotion gates**: Quality floor (default 0.8), max latency (default 60,000 ms), max policy violations (default 0), max accept rate regression (default 0.02), max cost per task (optional), and cost cap enforcement.
- **Unknown cost blocks promotion**: "Unknown spend is preserved and blocks a favorable promotion decision."
- **Conservative comparison**: Candidates are compared using paired tasks and repeated trials; uncertainty, raw failures, and actual receipts are reported.

**Evidence levels (distinct):**
- Published third-party reports
- Documented features
- Proposed tests
- Locally measured results

These have different evidence levels and must not be collapsed into a shared leaderboard.

## Alternatives considered

1. **No evaluation**: Would allow rapid changes but would risk regressions and invalid promotions.
2. **Training-set-only evaluation**: Would be simpler but would overfit to training data.
3. **Automatic promotion without gates**: Would be convenient but would risk promoting configurations that fail on held-out work.

## Consequences

- **Positive**: Rigorous evaluation; reproducible results; clear promotion criteria; honest handling of unknown costs; prevents overfitting.
- **Negative**: Requires careful task splitting; sealed tasks cannot be used for tuning; promotion requires passing all gates.
- **Critical rule**: "Configuration evolution should pass held-out quality and budget/latency gates before promotion."

## Related

- ADR-006 (bounded execution model)
- ADR-007 (deterministic fixture benchmarking)
- ADR-011 (integer micro-USD cost accounting)
