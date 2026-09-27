# Specialist teams and graph scopes

Open `/teams` for the specialist designer. This increment implements a validated design model, local persistence/import/export, node-to-team assignments, a zoomable scope hierarchy and an authorization preview. It does not replace the existing rule/model review teams or dispatch arbitrary specialists. Existing API execution controls remain unchanged.

## Design flow

1. Create specialists with precise responsibility/acceptance criteria and model/harness references.
2. Bind exact skill artifacts using source URL, revision and SHA-256; use the Ecosystem skill review to inspect the content first. Declare exact MCP server/tool identities and an optional gateway ID. These declarations do not install a skill, discover all tools behind a gateway or grant access.
3. Group specialists into dedicated teams and assign teams to explicit scope nodes. Graph Studio's selected-node inspector links to the designer with reference metadata in the browser fragment; attaching the node is an explicit action. Repositories, modules, swarms, data centers, racks, fleets, devices and IoT command centers can be modeled under one workspace root.
4. Configure IAM/PAM intent per specialist: provider, subject, accountable owner, tenant, audience, purpose, exact actions/resources, short TTL, delegation limit and approval quorum.
5. Preview an exact request. A team assignment alone is insufficient; policy resource scope is also required. Parent scopes do not imply descendant authority. Duplicate approver IDs, wrong audience/purpose, expired grants and invalid references fail closed. `read`/`plan` can become eligible for review only; all decisions keep execution disabled. Administrative and physical actuation requests remain denied.
6. Save in browser storage or export a validated JSON design. These records can contain private names and asset references: use non-secret identifiers. No credentials are minted. Import checks the complete schema and rejects unknown fields, excessive size/depth, cycles, dangling references and wildcard scopes.

The SVG diagram renders a focused node and at most 40 direct children; its searchable directory provides access to the remaining nodes. Limits are 300 specialists, 300 scope nodes and 64 teams; they describe design capacity, not simultaneously running agents. Remove operations clean related team memberships/resource references. Removing a scope is restricted to non-root leaves.

## Security project mapping

See [the pinned identity source assessment](specialist-identity-integrations.md) for the actual boundaries of AgentIAM Lab and Agent JIT IAM. The designer uses neither as a production authorization server. Approval IDs entered in the preview are unverified simulation input, not authenticated approval receipts. `maxDelegationDepth` is a proposed adapter policy; the preview does not mint or validate a live delegation chain.

Use AgentIAM's principal/intent/resource/audience/evidence concepts as conformance fixtures. Treat JIT credential mediation as a separate enforcing proxy/broker with issuer verification, key isolation, request canonicalization, replay protection, revocation and durable audit records. Do not rely on UI configuration or a model's compliance to enforce permissions.

## Contracts for later private integrations

Do not attach credentials or private source content to graph labels. A future connector should provide:

- **Asset inventory:** stable tenant-scoped ID, parent/containment relation, asset type, source revision, trust domain and accountable owner. Handle renamed/decommissioned assets without silently reusing identity.
- **Capabilities:** exact action IDs with versioned request/result schemas, risk/privilege classification, resource scope, tenant and permitted audiences. Tool/gateway inventory must not become a blanket grant.
- **Telemetry:** authenticated source, timestamp/sequence, freshness bounds, units and data classification. Treat stale or missing telemetry as unknown, not healthy.
- **Authorization:** trusted workload identity, purpose-bound delegation, authenticated distinct approvers where required, short-lived scoped grant, online revocation and per-operation re-evaluation. Child delegation must not widen parent constraints or change subject/workload unnoticed.
- **Execution:** durable request ID/idempotency key, bounded command lifetime, acknowledgments, cancellation/timeout behavior, result receipts, reconciliation of uncertain outcomes and actual usage/cost.
- **Physical operations:** authenticated device identity/attestation, independently enforced safety readiness and command envelope, local emergency stop, human override, site/geofence/operating limits where relevant, and append-only event evidence. An LLM or web graph must not sit in a hard real-time safety loop.

Start private adapters in inventory/telemetry-only mode. Test scope isolation, revocation, stale data, disconnects, duplicate delivery and emergency-stop behavior before enabling narrowly scoped physical commands. Data-center control and physical fleets have different latency/safety constraints; do not infer real-time capability from the browser graph.
