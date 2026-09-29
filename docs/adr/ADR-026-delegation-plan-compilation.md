# ADR-026: Delegation plan compilation without dispatch

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must compile verified constrained model schedules into control-plane plans with explicit model/tool/resource mappings. This compilation must not dispatch workers, call model providers, or prove that supplied prices are accurate.

## Decision

**Delegation plan compilation creates metadata only and does not dispatch.** Key characteristics:

- **Metadata only**: "Compilation creates metadata only. It does not dispatch adapters, call model providers, or prove that supplied prices, durations, or adapter configuration are accurate outside the explicit mapping supplied by the caller."
- **Schedule recomputation**: The compiler recomputes a schedule from the supplied problem and exports a durable plan.
- **Explicit mappings**: Model/tool/resource mappings are explicit and caller-asserted.
- **Secret rejection**: Problem and adapter mappings are checked for credential fields.
- **Bounded output**: Compiled plan capped at 1 MiB; review graph capped at 300 nodes / 900 edges / 2 MiB.

**Compilation inputs:**
- Problem: tasks, model options, budget, capacities, deadline
- Adapter mappings: configured adapter ID, operation, model ID, resource ID, tool ID, cost, max parallel
- Repository graph: optional, for context

## Alternatives considered

1. **Compilation with dispatch**: Would be more convenient but would bypass the control plane's admission control.
2. **No compilation**: Would simplify the system but would prevent cost-aware delegation planning.
3. **Automatic price inference**: Would be convenient but would be unreliable and could produce false precision.

## Consequences

- **Positive**: Safe compilation; no dispatch side effects; explicit mappings; bounded output.
- **Negative**: Does not dispatch; does not verify prices; requires caller-asserted mappings.
- **Critical statement**: "Adapter configuration remains caller-asserted and compilation does not dispatch workers."

## Related

- ADR-009 (execution classes)
- ADR-011 (integer micro-USD cost accounting)
- ADR-016 (bounded local optimization)
- ADR-025 (specialist access contracts)
