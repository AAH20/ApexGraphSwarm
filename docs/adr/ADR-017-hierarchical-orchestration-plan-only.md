# ADR-017: Hierarchical orchestration as plan-only design

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must support hierarchical swarm planning (root/domain/cluster/worker) with field-weighted assignment evidence, explicit IAM/PAM references, and budget/deadline blockers. However, this must be a design tool, not a dispatch system.

## Decision

**Hierarchical orchestration is plan-only and deterministic.** Key characteristics:

- **Plan-only**: "This module never executes agents. Provider, evaluator, scope, cost and capability records are caller supplied and must be independently enforced at dispatch."
- **Bounded clustering**: The planner constructs hierarchies at 4, 32, 128, and 200 tasks in the synthetic local benchmark.
- **Field profiles**: Five metric profiles (coding, research, analytics, operations, physical_simulation) with integer percentage weights that sum to exactly 100.
- **Hard gates**: `authorization_and_scope`, `privacy_and_data_boundary`, `run_and_task_budget`, `deadline_and_resource_capacity`, `required_evidence`, `independent_acceptance`.
- **Paired profile-score promotion gates**: Promotion requires passing paired profile-score gates.
- **Cost-per-accepted-outcome accounting**: The hierarchy planner tracks cost per accepted outcome.

**Synthetic benchmark scope**: The synthetic local benchmark measures planner construction at 4, 32, 128, and 200 tasks; it does not run agents or establish scale capacity.

## Alternatives considered

1. **Live hierarchical dispatch**: Would require worker provisioning, IAM enforcement, and safety controls that are out of scope.
2. **No hierarchy support**: Would prevent users from designing multi-level team structures.
3. **Implicit hierarchy from flat designs**: Would be simpler but would lack explicit domain/cluster boundaries and field-weighted assignment.

## Consequences

- **Positive**: Users can design hierarchical structures; clear scope boundaries; deterministic and reproducible; no agent execution.
- **Negative**: Designs are not executable; users must understand the boundary; synthetic benchmark does not measure agent throughput.
- **Critical statement**: "The synthetic local benchmark measures planner construction at 4, 32, 128, and 200 tasks; it does not run agents or establish scale capacity."

## Related

- ADR-006 (bounded execution model)
- ADR-007 (deterministic fixture benchmarking)
- ADR-010 (specialist team design)
- ADR-016 (bounded local optimization)
