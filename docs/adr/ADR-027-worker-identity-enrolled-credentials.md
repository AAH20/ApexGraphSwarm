# ADR-027: Worker identity with enrolled credentials

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must support worker identity for lease binding and access control. Workers must enroll with credentials that bind lease identity, but the system must not claim to be a multi-tenant identity service.

## Decision

**Worker identity uses enrolled credentials that bind lease identity.** Key characteristics:

- **Enrollment**: Workers issue credentials through `issue_credential()`.
- **Verification**: `verify_credential()` validates worker credentials.
- **Token digest**: `token_digest()` provides a non-reversible identifier for credentials.
- **Lease binding**: "Enrolled worker credentials bind lease identity; no arbitrary harness sandboxing or multi-tenant identity service."
- **Schema initialization**: `initialize_identity_schema()` sets up the identity tables in the control plane database.

**Explicit non-goals:**
- Not a multi-tenant identity service
- Not an external IAM integration
- Not an arbitrary harness sandbox

## Alternatives considered

1. **External identity provider (OAuth, OIDC)**: Would provide production-grade identity but requires external services and credentials.
2. **No worker identity**: Would simplify the system but would prevent lease binding and access control.
3. **OS-level identity**: Would be more secure but is platform-specific and complex.

## Consequences

- **Positive**: Lease binding; local enforcement; no external dependencies.
- **Negative**: Not a multi-tenant identity service; not an external IAM; credentials are only as good as the local storage.
- **Critical statement**: "Enrolled worker credentials bind lease identity; no arbitrary harness sandboxing or multi-tenant identity service."

## Related

- ADR-003 (SQLite control plane)
- ADR-008 (lease-based task claiming)
- ADR-025 (specialist access contracts)
