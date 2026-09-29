# ADR-014: Secret rejection and credential hygiene

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must never store, log, or transmit plaintext credentials. This includes task payloads, specialist contracts, graph snapshots, analytics events, and API responses. The system must reject common credential field names and use secret references instead.

## Decision

**Credential fields are rejected at every boundary.** Key mechanisms:

- **Field name regex**: `_SECRET_FIELD = re.compile(r"(?:^|[_-])(api[_-]?key|access[_-]?token|password|secret|credential|authorization)(?:$|[_-])", re.IGNORECASE)` is used in `control.py` and `specialist_access.py`.
- **Rejection in task payloads**: Common credential field names are rejected inside task payloads; payload values must still use secret references, never plaintext credentials.
- **Rejection in specialist contracts**: `_reject_secrets()` recursively checks all keys in contract JSON; keys matching the secret pattern (unless ending in `_ref` or `-ref`) are rejected.
- **Rejection in delegation plans**: `_SECRET_KEY` regex is applied to problem and adapter mappings.
- **Workspace token**: `INTEGRATION_ACCESS_TOKEN` is configured in `apps/web/.env.local` and must be kept out of screenshots, shared exports, and commits.
- **Browser design fields**: Should contain non-secret references, not tokens or connection strings.

**Allowed secret-adjacent fields:**
- `tokenUsage` in checkpoint receipts (the one permitted token-related receipt field, with intentionally narrow schema).
- Fields ending in `_ref` or `-ref` (secret references, not values).

## Alternatives considered

1. **No credential checking**: Would be simpler but would risk credential leakage in logs, exports, and browser bundles.
2. **Encryption at rest**: Would protect stored credentials but adds key management complexity; the system prefers to never store credentials.
3. **External secret broker**: Would be more secure but adds deployment complexity that conflicts with local-first.

## Consequences

- **Positive**: Prevents credential leakage; clear error messages when credentials are detected; works with secret references.
- **Negative**: Users must use secret references; some valid field names may be rejected; requires discipline in naming conventions.
- **Critical rule**: "Keep secrets server-side and outside Git, logs, exports and browser bundles."

## Related

- ADR-001 (local-first architecture)
- ADR-002 (stdlib-only control plane)
- ADR-010 (specialist team design)
- ADR-012 (explicit adapter pattern)
