# Tutorial 5: Governance — Specialist Teams and Scopes

## Overview

ApexGraphSwarm's governance model lets you design specialist teams with precise capabilities, authority boundaries, and scope assignments. This tutorial covers the team designer, scope hierarchy, authorization previews, and the separation between design and execution.

## Accessing the Team Designer

Navigate to [http://127.0.0.1:3010/teams](http://127.0.0.1:3010/teams) or click **Specialist teams** in the navigation.

## Design Flow

### Step 1: Create Specialists

Each specialist has:
- **Name and responsibility** — precise description of what the specialist does
- **Acceptance criteria** — how to evaluate the specialist's output
- **Model/provider reference** — which model or harness to use
- **Harness selection** — the execution environment

### Step 2: Bind Skills

Attach skill artifacts to each specialist:
- **Skill ID** — unique identifier
- **Library/source URL** — where the skill is documented
- **Pinned revision** — exact version
- **SHA-256 reference** — content hash

> A recorded hash is **not** proof that content was fetched, verified, installed, or trusted. Use the Ecosystem skill review to inspect content first.

### Step 3: Declare MCP Tool Bindings

Specify exact MCP server/tool identities and an optional gateway ID. Selecting a gateway does **not** grant all tools behind it — each tool must be explicitly bound.

### Step 4: Group into Teams

Create reusable teams and assign specialists to them. Teams can be shared across multiple scope assignments.

### Step 5: Assign to Scope Nodes

Select a Graph Studio node and choose **Assign a specialist swarm**. Attach it beneath the intended scope, then explicitly assign teams. Hierarchy membership does **not** imply inherited permissions.

### Step 6: Configure IAM/PAM Intent

For each specialist, declare:
- **Provider** — identity provider
- **Subject** — the specialist's identity
- **Accountable owner** — who is responsible
- **Tenant** — tenant scope
- **Audience** — intended recipients
- **Purpose** — why access is needed
- **Actions** — exact allowed operations
- **Resources** — exact resource scope
- **TTL** — 1 to 300 seconds
- **Delegation depth** — how many hops allowed
- **Approval quorum** — how many approvers required

### Step 7: Preview Authorization

Test an exact request against the policy. The preview returns:
- `denied` — request is not allowed
- `approval-required` — needs additional approvals
- `eligible-for-review` — can be reviewed for activation

> **Execution remains disabled in every case.** Administrative and physical actuation requests remain denied.

### Step 8: Export or Save

Save in browser storage or export a validated JSON design. Imports are capped at **512 KiB** and checked for schema compliance, cycles, dangling references, and wildcard scopes.

## Scope Hierarchy

The scope hierarchy supports these node types:
- **Repository** — top-level code repository
- **Module** — a subsystem or package
- **Swarm** — a group of agents working together
- **Data center** — physical or virtual data center
- **Rack** — a rack within a data center
- **Fleet** — a group of devices or vehicles
- **Device** — an individual device
- **IoT command center** — IoT control point

The SVG diagram renders a focused node and at most **40 direct children**; the directory provides access to remaining nodes.

## Limits

| Resource | Limit |
|----------|-------|
| Specialists | 300 |
| Teams | 64 |
| Scope nodes | 300 |
| Skill bindings per specialist | 32 |
| Tool bindings per specialist | 32 |
| Import size | 512 KiB |
| TTL | 1–300 seconds |

These counts describe **design capacity**, not concurrently running agents.

## Security Boundaries

### What the Designer Does NOT Do

- Does not dispatch arbitrary specialists
- Does not enforce live IAM/PAM
- Does not mint credentials
- Does not grant access to MCP tools behind a gateway
- Does not imply descendant authority from parent scopes
- Does not authenticate approval IDs (they are simulation input)

### Identity Integration

The designer uses two pinned identity projects as conformance fixtures:
- [AAH20/ai-agent-identity-authorization-security](https://github.com/AAH20/ai-agent-identity-authorization-security)
- [AAH20/agent-jit-iam](https://github.com/AAH20/agent-jit-iam)

Neither is installed as a production authorization server. Treat JIT credential mediation as a separate enforcing proxy/broker with issuer verification, key isolation, request canonicalization, replay protection, revocation, and durable audit records.

## Contracts for Private Integrations

When building private adapters for data-center, Physical AI, or IoT:

1. **Start in inventory/telemetry-only mode** — no command capabilities
2. **Map assets** to stable tenant-scoped IDs with parent/containment relations
3. **Define capabilities** with exact action IDs, versioned schemas, and risk classification
4. **Add telemetry** with authenticated source, timestamps, freshness bounds
5. **Implement authorization** with trusted workload identity, purpose-bound delegation, short-lived scoped grants, online revocation
6. **Add execution** with durable request IDs, idempotency, bounded command lifetime, result receipts
7. **Physical operations** require authenticated device identity, independently enforced safety readiness, local emergency stop, human override, and append-only event evidence

> An LLM or web graph must **not** sit in a hard real-time safety loop.

## Next Steps

- [Tutorial 6: Security](06-security.md) — Deep dive into security model and best practices.
- [Tutorial 4: Agent Orchestration](04-agent-orchestration.md) — Understand the execution layer.
