# ADR-021: Repository conflict detection via Git object pinning

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must detect conflicts between proposed repository changes and the current state of the repository. This requires comparing candidate changes against Git objects and rechecking plan semantics against fresh repository evidence.

## Decision

**Repository conflicts are detected by pinning candidate changes to Git objects and rechecking plan semantics against fresh repository evidence.** Key characteristics:

- **Git object pinning**: Candidate changes are pinned to specific Git objects (commits, blobs, trees).
- **Fresh evidence recheck**: Plan semantics are rechecked against fresh repository evidence, not cached snapshots.
- **Stale/tamper detection**: The system detects when the working tree has changed since the plan was created.
- **Browser limitation**: "The browser cannot choose an arbitrary filesystem path" — repository selection is constrained to prevent unauthorized access.
- **No automatic merges**: "Working-tree changes excluded; no automatic merges."

**Conflict detection scope:**
- Dependency-respecting waves
- Declared access conflicts
- Committed Git diffs with stale/tamper rechecks
- Read paths remain declarations; working-tree changes are excluded

## Alternatives considered

1. **Working-tree diff**: Would be simpler but would include uncommitted changes that may be irrelevant or temporary.
2. **No conflict detection**: Would be simpler but would risk applying plans to changed repositories.
3. **Automatic merge**: Would be convenient but is unsafe and can produce unexpected results.

## Consequences

- **Positive**: Detects conflicts before execution; prevents stale plan application; no unsafe automatic merges.
- **Negative**: Requires Git metadata; browser cannot select arbitrary paths; read paths remain declarations.
- **Critical statement**: "The browser cannot choose an arbitrary filesystem path."

## Related

- ADR-005 (evidence-bearing repository graph)
- ADR-016 (bounded local optimization)
- ADR-017 (hierarchical orchestration plan-only)
