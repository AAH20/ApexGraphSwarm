# ADR-028: Access control with exact grants and budget enforcement

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must enforce access control with exact principal/tool/resource matching, expiry, revocation, and cumulative budget enforcement. This must be local, explicit, and must not claim to be an external IAM integration.

## Decision

**Access control uses exact grants with budget enforcement.** Key characteristics:

- **Exact matching**: Principal/tool/resource matching with exact identifiers (no wildcards or descendant inheritance).
- **Expiry**: Grants have explicit expiry times.
- **Revocation**: Grants can be revoked before expiry.
- **Budget enforcement**: Cumulative reserved/settled budget is tracked per grant; lease renewal checks enforce budget limits.
- **Schema initialization**: `initialize_access_schema()` sets up the access control tables.
- **Grant ID generation**: `new_grant_id()` creates unique grant identifiers.

**Access check flow:**
1. Verify principal identity
2. Check grant exists and is not expired or revoked
3. Match tool and resource exactly
4. Check cumulative budget (reserved + settled)
5. Return `denied`, `approval-required`, or `eligible-for-review`

## Alternatives considered

1. **Role-based access control (RBAC)**: Would be simpler but would lack the exact resource matching needed for fine-grained authority.
2. **Attribute-based access control (ABAC)**: Would be more flexible but would be more complex and harder to audit.
3. **No access control**: Would simplify the system but would prevent safe multi-worker operation.

## Consequences

- **Positive**: Fine-grained authority; explicit budget enforcement; local enforcement; clear audit trail.
- **Negative**: More complex than RBAC; requires explicit grant management; not an external IAM.
- **Critical statement**: "Resource assignments are exact, without descendant inheritance."

## Related

- ADR-003 (SQLite control plane)
- ADR-010 (specialist team design)
- ADR-011 (integer micro-USD cost accounting)
- ADR-025 (specialist access contracts)
- ADR-027 (worker identity)
