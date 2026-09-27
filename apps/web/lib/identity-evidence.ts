export type IdentityEvidence = {
  id: string;
  name: string;
  source: string;
  revision: string;
  status: string;
  capabilities: string[];
  limits: string[];
  adoption: string;
};

/** Public-source integration assessment; no external code was installed or executed. */
export const identityEvidence: readonly IdentityEvidence[] = Object.freeze([
  {
    id: 'agentiam-lab',
    name: 'AAH20 AgentIAM Lab',
    source: 'https://github.com/AAH20/ai-agent-identity-authorization-security/tree/0a8b3d9d2f437c297f021184cb242c33f9413e3a',
    revision: 'main @ 0a8b3d9d2f437c297f021184cb242c33f9413e3a (2026-09-22)',
    status: 'Pinned source and schemas reviewed through the authorized GitHub reader. The project labels v0.1 a deterministic reference/conformance lab, not a production identity provider or certification. Tests were inspected but not run.',
    capabilities: [
      'Published scenario and JSON-schema surface covers principal/agent/delegation context, task-scoped audience/resource/action grants, proof-of-possession, child scope narrowing, cascading revocation, receipt fields, and approval gates.',
      'README specifies a default maximum five-minute task-token lifetime and up-to-30-second physical-action lease requirements.',
      'Published scenarios describe MCP wrong-audience/stolen-bearer denial, material-privilege approval quorum, and physical-action readiness/attestation gates.',
      'Includes an OPA reference policy, portable core test command, vulnerable/controlled examples, and a GitHub Action described as running portable conformance tests.',
    ],
    limits: [
      'The code stores principals and grants in per-process dictionaries. It has no durable identity/grant store, issuer/secret broker, external IAM/PAM adapter, or deployed enforcement point.',
      'Approval enforcement in TrustFabric checks only the count of approval strings; duplicate strings can satisfy the count, and the inspected model has no approver identity/signature verification or durable approval receipt.',
      'Parent delegation narrowing covers resources/actions/purpose/depth and required-approval count, but remaining budget is a declaration rather than a consumed/reserved ledger; geographic/data-classification fields are not checked in evaluate().',
      'The project explicitly says v0.1 is a deterministic reference lab, not a production identity provider or certification; published test results are not equivalent to deployed enforcement evidence.',
      'README says local HMAC receipts establish shared-secret integrity only, not public-key non-repudiation. Independently verifiable/asymmetric receipt signing is listed as future work.',
      'Cloud identity-provider, workload-identity, AWS STS, GitHub OIDC, AuthZEN, and other production adapters are roadmap items; no actual workforce IAM/PAM grant, token broker, secret vault, or device control plane was verified.',
      'Physical lease creation checks an ALLOW decision, request/policy binding, short expiry, attestation/readiness/model fields, and safety obligations, but returns only an evidence digest, not a signed lease. No robot, independent safety controller, hardware attestation, or physical-action enforcement was exercised.',
      'The MCP scenario invokes the local Broker token checks; it does not speak MCP or enforce authorization in an MCP server/gateway. Runtime MCP auth and authorization still need enforcement at each protected tool boundary.',
      'The referenced receipt schema uses ALLOW_WITH_APPROVAL while TrustFabric returns REQUIRE_APPROVAL; define the mapping before relying on schema interoperability.',
      'The pinned commit is unsigned in GitHub commit metadata; this review pins content identity, not publisher authenticity. No code or conformance suite was executed.',
    ],
    adoption: 'Use as a requirements/schema/conformance-fixture input for Apex identity contracts. Before any deployment grant, pin and independently inspect a commit, run its tests in an isolated review environment, and build a separate adapter to the selected IAM/PAM, OAuth/token broker, MCP gateway, and receipt-verification services. Require short TTLs, narrowed delegated scopes, revocation propagation, independently verifiable receipts, and a human/safety interlock for physical actions; do not treat the lab as a grant issuer or robot authorization service.',
  },
  {
    id: 'agent-jit-iam',
    name: 'AAH20 Agent JIT IAM',
    source: 'https://github.com/AAH20/agent-jit-iam/tree/c6dc25454eb51cc02f2d6f41e9b3ddd6a8d1c78c',
    revision: 'main @ c6dc25454eb51cc02f2d6f41e9b3ddd6a8d1c78c (2026-08-22)',
    status: 'Pinned public source reviewed through the authorized GitHub reader. The new AuthorityBroker is a deterministic policy component, not a complete IAM/PAM service or provider proxy. Tests were inspected but not run.',
    capabilities: [
      'AuthorityBroker signs canonical provider/method/path/fact capabilities with HMAC, performs explicit-deny-first operation checks, binds a workload string, caps delegated uses/lifetime relative to parent, and atomically consumes max-use counters in SQLite when a persistent replay_db path is configured.',
      'The repo retains a legacy AgentJITDelegator string-scope API with one-use tokens, a local kill switch, and a SHA-256 audit chain; this is distinct from the newer provider-operation broker.',
    ],
    limits: [
      'The README says a trusted proxy must attach provider credentials after ALLOW, while AuthorityBroker deliberately performs no network I/O; no proxy, credential issuance, cloud/IAM provider connector, approval flow, or MCP adapter exists in the pinned tree.',
      'Code audit: child validation checks provider, expiry, max uses, and operation method/path, but does not bind child subject/workload to the parent, nor require child semantic constraints and denied paths to be subsets. Authorization verifies the child signature but does not resolve/check parent_digest or support revoking a capability/parent. Do not use parent_digest as a live revocation chain.',
      'Root capability TTL has no maximum in AuthorityBroker.issue(); `max_uses` is an operation-count limit, not a money/budget control. Receipts use HMAC and an in-memory chain head by default; HMAC is not public-key non-repudiation and default `:memory:` replay state does not survive restart.',
      'The legacy AgentJITDelegator stores consumed-token IDs in memory, and its SHA-256 hash chain is not a keyed signature. It is not a distributed durable replay or independently verifiable receipt service.',
      'No production workforce IAM/PAM grant, private data-center identity, physical device, robot, or IoT integration is in the inspected tree.',
    ],
    adoption: 'Use the provider-operation capability shape as an adapter design input only. Before any execution integration, require a fixed trusted proxy, workload identity verification, subject/delegation-chain enforcement, full constraint/deny narrowing, maximum root TTL, online revocation, durable receipt persistence/signatures, budget semantics, and integration tests against the real IAM/PAM and MCP enforcement points. Do not admit paid or physical actions through this reference implementation.',
  },
]);
