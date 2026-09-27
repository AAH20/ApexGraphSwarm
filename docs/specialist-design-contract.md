# Specialist and fleet design contract

The `specialist-design` module validates an editable, versioned description of specialists, teams, and a workspace-scoped resource hierarchy. It is a design-time validator and access preview only. It does not connect to Agent IAM Lab, Agent JIT IAM, an MCP server, a provider, a harness, a device, or a datacenter. A decision of `eligible-for-review` is not an authorization decision and cannot be used to mint credentials or invoke tools.

## Data limits and references

- `schemaVersion` is exactly `1`; unknown properties are rejected. Input must be plain, acyclic JSON data without getters, unsafe object keys, or custom prototypes; maximum encoded design size is 512 KiB, nesting depth 24, and 20,000 values.
- A design can contain at most 300 specialists, 64 teams, and 300 scope nodes. IDs are exact non-secret identifiers, unique across specialists, teams, and nodes. References must resolve.
- Each scope tree has one root, and it must be a `workspace`. Parent links must be acyclic and every node must reach that root. Each node names its assigned teams. A specialist is assigned to a node only through a team that lists that specialist and is listed by that exact node. Parent assignment is never inherited.
- A policy resource is an exact node ID. Wildcards, glob patterns, duplicate actions/resources, and dangling IDs are rejected. The module accepts literal lowercase action labels, but only exact `read` and `plan` requests can reach review eligibility. Any action with `admin`, `administer`, `actuate`, or `actuation` as a segment is always denied; other actions remain denied pending a separately reviewed policy/enforcement contract.
- Skills are explicit bindings capped at 32 per specialist. Each binding requires an HTTPS source URL, a revision, and a lowercase 64-character SHA-256 digest. URL userinfo, queries, and fragments are rejected. A digest proves which bytes were selected; it does not prove those bytes are safe.
- Tool bindings are exact `{serverId, toolName, gatewayId}` identifiers, capped at 32 per specialist. No endpoint URLs, shell commands, credentials, or wildcard tool names are accepted.
- `externalRef` is opaque graph linkage only (up to 2,048 characters); an empty value represents a planned scope that is not connected to an external system. URL-shaped values cannot include URL userinfo, a query, or a fragment. It is never dereferenced by this module.
- `subjectRef`, `ownerRef`, `tenantRef`, `audience`, and `purpose` are non-secret exact identifiers. They are not credentials, and the module does not authenticate them.

Policies bound TTL to 1–300 seconds, delegation depth to 0–8, and approval quorum to 0–8. The preview accepts elapsed time and counts distinct supplied approver IDs, but it cannot establish who supplied them, validate the approval chain, or verify a delegation depth. A real adapter must enforce expiry, delegation depth/amplification, tenant/audience/purpose binding, approver authority and quorum, exact resource scope, and revocation at the point of use. Never treat request-supplied identity labels as authenticated claims.

## Preview decisions

`previewSpecialistAccess` returns one of:

- `denied`: invalid input/design; privileged or unsupported action; unknown agent/node; missing exact team assignment, action, resource, audience, purpose, or live TTL.
- `approval-required`: the request otherwise matches the design, but too few distinct approver IDs were supplied. Those IDs are unverified labels.
- `eligible-for-review`: the read/plan request matches the design and the configured quorum count is met. It is still only a candidate for review in a separately authenticated approval/enforcement system.

Every outcome has `executionAllowed: false`. Parent scope, policy-provider labels (`agentiam-lab`, `agent-jit-iam`, or `external`), and `maxDelegationDepth` are metadata only; no runtime capability is inherited or minted.

`createStarterDesign()` creates Planner, Researcher, and Reviewer roles under one Core team and workspace node. Skill/tool lists, policy actions, and policy resource grants start empty. It is therefore valid but grants nothing.

## Tests

`apps/web/tests/specialist-design.test.ts` exercises starter deny-by-default, review/quorum behavior, exact assignment/scope, dangling references, global ID collisions, cycles, wildcards, skill hash and URL checks, privileged actions, TTL, duplicate approvers, bounds, unknown fields, prototype/accessor defense, and rejection of unsupported delegation metadata.
