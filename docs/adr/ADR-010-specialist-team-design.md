# ADR-010: Specialist team design without live dispatch

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must allow users to design specialist teams with precise capabilities, authority, and scope assignments. However, the system must not claim to dispatch custom teams or enforce IAM/PAM without explicit adapters. The design tool must be honest about what it does and does not do.

## Decision

**Specialist team design is a design-time tool, not a dispatch system.** Key characteristics:

- **Design capacity**: Up to 300 specialists, 64 teams, 300 scope nodes, 32 skill and 32 tool bindings per specialist.
- **Scope hierarchy**: Repository, module, swarm, data-center, rack, fleet, device, and IoT command-center nodes.
- **IAM/PAM intent**: Identity, accountable owner, tenant, audience, purpose, actions, resources, TTL (1–300 seconds), delegation depth, and approval quorum.
- **Authorization previews**: Return `denied`, `approval-required`, or `eligible-for-review`. **Execution remains disabled in every case.**
- **Resource assignments**: Exact, without descendant inheritance.
- **Approver IDs**: Simulation inputs, not authenticated approvals.
- **Administrative and physical actuation requests**: Remain denied.

**Explicit non-goals:**
- Custom dispatch is not connected.
- Live IAM/PAM enforcement is not connected.
- Data-center, Physical AI, and IoT nodes are planning scopes, not connected infrastructure controllers.
- The visualization and an LLM orchestration loop are not hard real-time safety controllers.

## Alternatives considered

1. **Full dispatch system**: Would require external IAM integration, worker provisioning, and safety controls that are out of scope.
2. **No design tool**: Would prevent users from planning and evaluating team structures.
3. **Design tool with implicit dispatch claims**: Would mislead users into thinking designs are executable.

## Consequences

- **Positive**: Users can design and evaluate team structures; clear boundaries prevent misuse; designs can be exported for review; future dispatch can build on validated designs.
- **Negative**: Designs are not executable; users must understand the boundary; future dispatch requires additional engineering.
- **Critical statement**: "Specialist-team designs do not yet dispatch custom teams or enforce IAM/PAM."

## Related

- ADR-001 (local-first architecture)
- ADR-006 (bounded execution model)
- ADR-012 (explicit adapter pattern)
