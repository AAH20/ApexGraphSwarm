# Tutorial 6: Security

## Overview

Security in ApexGraphSwarm is built on explicit boundaries, least-privilege design, and the principle that design tools must not become execution tools. This tutorial covers the security model, credential handling, authorization previews, and safe operation practices.

## Core Security Principles

### 1. Design vs. Execution Separation

The specialist designer, scope hierarchy, and authorization previews are **design-time tools**. They produce validated designs and previews but **never dispatch agents or execute work**. Execution requires:
- Explicitly configured adapters
- Authenticated workers
- Exact capability grants
- Server-side policy enforcement

### 2. Least Privilege

Every authorization is exact:
- **Actions** are specific operation IDs, not wildcard permissions
- **Resources** are exact identifiers, not descendant-inherited scopes
- **TTL** is bounded to 1–300 seconds
- **Delegation depth** is explicitly limited
- **Approval quorum** requires distinct, authenticated approvers

### 3. Fail Closed

When in doubt, the system denies:
- Duplicate approver IDs → denied
- Wrong audience/purpose → denied
- Expired grants → denied
- Invalid references → denied
- Administrative/physical actuation → always denied
- Unknown costs → cannot be represented as zero

### 4. Secrets Stay Server-Side

- Keep secrets server-side and outside Git
- Browser design fields should contain non-secret references, not tokens or connection strings
- Imported graphs and skill documents remain untrusted data
- Local harness execution inherits the installed tool's permissions

## Credential Handling

### INTEGRATION_ACCESS_TOKEN

The private workspace token (`INTEGRATION_ACCESS_TOKEN` in `apps/web/.env.local`) authorizes the bounded Python runner. Rules:
- Enter it only in the local execution control that requests it
- Keep it out of screenshots, shared exports, and commits
- Review the environment template (`apps/web/.env.example`) before enabling services

### Provider Credentials

Provider credentials (OpenRouter, vLLM, etc.) are separate from the workspace token. They require configured server-side credentials/endpoints and model IDs. vLLM selection does not provision a GPU.

### Task Payload Security

Common credential field names are **rejected** inside task payloads by the control plane. Payload values must use secret references, never plaintext credentials.

## Authorization Preview States

| State | Meaning |
|-------|---------|
| `denied` | Request is not allowed under current policy |
| `approval-required` | Needs additional approvals before activation |
| `eligible-for-review` | Can be reviewed for activation (execution still disabled) |

> Approver IDs entered in the preview are **unverified simulation input**, not authenticated approval receipts.

## IAM/PAM Intent Model

Each specialist declares:
- **Provider** — identity provider (e.g., AgentIAM, JIT IAM)
- **Subject** — the specialist's workload identity
- **Accountable owner** — human responsible for the specialist
- **Tenant** — tenant isolation boundary
- **Audience** — intended recipients of the grant
- **Purpose** — why access is needed
- **Actions** — exact allowed operations
- **Resources** — exact resource scope (no descendant inheritance)
- **TTL** — 1 to 300 seconds
- **Delegation depth** — max hops
- **Approval quorum** — number of distinct approvers required

## Identity Integration Boundaries

The two pinned identity projects provide conformance fixtures, not production enforcement:

- **[AAH20/ai-agent-identity-authorization-security](https://github.com/AAH20/ai-agent-identity-authorization-security)** — principal/intent/resource/audience/evidence concepts
- **[AAH20/agent-jit-iam](https://github.com/AAH20/agent-jit-iam)** — JIT credential mediation patterns

For production, treat JIT credential mediation as a separate enforcing proxy/broker with:
- Issuer verification
- Key isolation
- Request canonicalization
- Replay protection
- Revocation
- Durable audit records

## MCP Security

MCP discovery supports the documented handshake/HTTP subset with bounded responses. It is **not** universal support for every MCP transport, protocol revision, gateway, or authentication mode.

Selecting a gateway does **not** grant all tools behind it. Each tool must be explicitly bound to a specialist.

## Skills Security

Skill review accepts manifests/content for provenance and metadata checks. It does **not**:
- Fetch packages from skills.sh or another library
- Install arbitrary packages
- Execute code from skill documents

A recorded SHA-256 hash is **not** proof that content was fetched, verified, installed, or trusted.

## Harness Security

The optional local harness runner:
- Accepts allowlisted profile identifiers and bounded goals
- Commands, workspaces, and authentication modes are fixed server-side
- Uses a loopback bearer-protected interface
- Two-process cap, 40-second limit, bounded output
- Is **not** an OS security sandbox

Example profiles start disabled. Use appropriate isolation for real workloads.

## Analytics Security

- The stdlib engine caps live scans at 200,000 rows and imports at 10,000 rows
- Imports remain in memory and never write to the execution ledger
- The private workspace token provides read-only ledger analytics
- CSV/JSON imports are bounded and validated

## Physical Operations Security

For data-center, Physical AI, and IoT scopes:
- Commands need separately authenticated enforcement
- Durable receipts, idempotency, revocation required
- Independent physical safety controls mandatory
- An LLM or web graph must not sit in a hard real-time safety loop
- Start with inventory/telemetry-only mode
- Test scope isolation, revocation, stale data, disconnects, duplicate delivery, and emergency-stop behavior before enabling commands

## Security Checklist

Before deploying any ApexGraphSwarm configuration:

- [ ] All secrets are server-side, outside Git
- [ ] Browser design fields contain non-secret references only
- [ ] Task payloads use secret references, not plaintext credentials
- [ ] Authorization previews tested for exact requests
- [ ] Scope assignments are explicit (no descendant inheritance assumed)
- [ ] MCP tool bindings are exact (no gateway-wide grants)
- [ ] Skill hashes recorded and content reviewed
- [ ] Harness profiles are allowlisted and bounded
- [ ] Database is backed up and restore tested
- [ ] Worker processes respect `max_active` and `max_registered_agents`
- [ ] Unknown costs are explicitly labeled, not zeroed

## Next Steps

- [Tutorial 5: Governance](05-governance.md) — Design specialist teams with proper authority.
- [Tutorial 8: Deployment](08-deployment.md) — Secure deployment practices.
