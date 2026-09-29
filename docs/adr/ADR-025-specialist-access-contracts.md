# ADR-025: Specialist access contracts as opt-in local enforcement

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must support specialist access contracts that define exact actions, resources, audience, purpose, TTL, delegation depth, and approval quorum. These contracts must be enforced locally by the control plane but must not claim to be an external IAM integration or execution sandbox.

## Decision

**Specialist access contracts are opt-in, local, and enforced only by ControlStore.** Key characteristics:

- **Enforcement scope**: "These contracts are enforced only by ControlStore. They are not an external IAM integration, an installed skill/tool attestation, or an execution sandbox."
- **Contract lifecycle**: Create → approve → activate → bind to task → enforce → revoke.
- **Approval quorum**: Contracts require a configurable number of approver IDs before activation.
- **Exact resource matching**: Principal/tool/resource matching with expiry, revocation, cumulative reserved/settled budget, and lease renewal checks.
- **Secret rejection**: Contract JSON is recursively checked for credential fields.
- **Design contract fields**: Strict field validation for agents, teams, nodes, skills, tools, and assignments.

**Explicit non-goals:**
- Not an external IAM integration
- Not an installed skill/tool attestation
- Not an execution sandbox
- No arbitrary harness sandboxing or multi-tenant identity service

## Alternatives considered

1. **External IAM integration**: Would provide production-grade identity but requires external services and credentials.
2. **No access contracts**: Would simplify the system but would prevent fine-grained authority design.
3. **OS-level enforcement**: Would be safer but is platform-specific and complex.

## Consequences

- **Positive**: Fine-grained authority design; local enforcement; clear contract lifecycle; secret rejection.
- **Negative**: Not an external IAM; not a sandbox; requires manual approval; contracts are only as good as the local enforcement.
- **Critical statement**: "These contracts are enforced only by ControlStore. They are not an external IAM integration, an installed skill/tool attestation, or an execution sandbox."

## Related

- ADR-003 (SQLite control plane)
- ADR-010 (specialist team design)
- ADR-014 (secret rejection and credential hygiene)
