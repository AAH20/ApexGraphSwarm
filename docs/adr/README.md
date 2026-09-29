# ApexGraphSwarm Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for all major decisions in the ApexGraphSwarm project. Each ADR documents the context, decision, alternatives considered, and consequences of a significant architectural choice.

## Index

### Core Architecture

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](ADR-001-local-first-architecture.md) | Local-first, single-host architecture | Accepted |
| [ADR-002](ADR-002-stdlib-only-control-plane.md) | Python standard-library-only control plane | Accepted |
| [ADR-003](ADR-003-sqlite-control-plane.md) | SQLite as the durable control plane | Accepted |
| [ADR-004](ADR-004-nextjs-web-frontend.md) | Next.js web frontend with separate npm dependencies | Accepted |

### Graph Intelligence

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-005](ADR-005-evidence-bearing-repository-graph.md) | Evidence-bearing repository graph with confidence levels | Accepted |

### Execution Model

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-006](ADR-006-bounded-execution-model.md) | Bounded execution model with explicit resource caps | Accepted |
| [ADR-007](ADR-007-deterministic-fixture-benchmarking.md) | Deterministic fixture-based benchmarking | Accepted |
| [ADR-008](ADR-008-lease-based-task-claiming.md) | Lease-based task claiming with fencing | Accepted |
| [ADR-009](ADR-009-execution-classes.md) | Execution classes with explicit retry semantics | Accepted |

### Specialist Teams and Access

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-010](ADR-010-specialist-team-design.md) | Specialist team design without live dispatch | Accepted |
| [ADR-025](ADR-025-specialist-access-contracts.md) | Specialist access contracts as opt-in local enforcement | Accepted |
| [ADR-027](ADR-027-worker-identity-enrolled-credentials.md) | Worker identity with enrolled credentials | Accepted |
| [ADR-028](ADR-028-access-control-exact-grants.md) | Access control with exact grants and budget enforcement | Accepted |

### Cost and Economics

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-011](ADR-011-integer-microusd-cost-accounting.md) | Integer micro-USD cost accounting | Accepted |
| [ADR-018](ADR-018-provider-receipt-normalization.md) | Provider receipt normalization with reconciliation boundary | Accepted |
| [ADR-032](ADR-032-cost-routing-editable-assumptions.md) | Cost routing with editable assumptions and unknown preservation | Accepted |

### Evaluation and Quality

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-013](ADR-013-evaluation-promotion-gates.md) | Versioned evaluation with held-out promotion gates | Accepted |
| [ADR-019](ADR-019-swarm-arena-unsigned-evidence.md) | Swarm Arena as unsigned evidence sharing | Accepted |
| [ADR-035](ADR-035-verification-test-suites.md) | Verification via Python and web test suites | Accepted |

### Security and Credentials

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-014](ADR-014-secret-rejection-credential-hygiene.md) | Secret rejection and credential hygiene | Accepted |

### Data and Analytics

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-015](ADR-015-read-only-analytics.md) | Read-only analytics with explicit data boundaries | Accepted |
| [ADR-024](ADR-024-execution-graph-read-only-projection.md) | Execution graph as read-only projection | Accepted |
| [ADR-031](ADR-031-analytics-visualizations-data-requirements.md) | Analytics visualizations with explicit data requirements | Accepted |

### Optimization

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-016](ADR-016-bounded-local-optimization.md) | Bounded local optimization without code generation | Accepted |
| [ADR-017](ADR-017-hierarchical-orchestration-plan-only.md) | Hierarchical orchestration as plan-only design | Accepted |
| [ADR-033](ADR-033-optimization-kernels-pinned-adapters.md) | Optimization kernels as pinned, audited adapters | Accepted |

### Integrations

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-012](ADR-012-explicit-adapter-pattern.md) | Explicit adapter pattern for external integrations | Accepted |
| [ADR-029](ADR-029-mcp-discovery-bounded-subset.md) | MCP discovery with bounded handshake subset | Accepted |
| [ADR-030](ADR-030-skills-review-provenance-only.md) | Skills review as provenance check without installation | Accepted |
| [ADR-034](ADR-034-ecosystem-comparison-evidence-based.md) | Ecosystem comparison without installation claims | Accepted |

### Operations

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-020](ADR-020-decision-intelligence-structured-tool.md) | Decision intelligence as structured tool | Accepted |
| [ADR-021](ADR-021-repository-conflict-detection.md) | Repository conflict detection via Git object pinning | Accepted |
| [ADR-022](ADR-022-inference-telemetry-read-only.md) | Inference telemetry as read-only Prometheus metrics | Accepted |
| [ADR-023](ADR-023-local-harness-runner.md) | Local harness runner with fixed server-side policy | Accepted |
| [ADR-026](ADR-026-delegation-plan-compilation.md) | Delegation plan compilation without dispatch | Accepted |

## Principles

These ADRs collectively encode the following core principles:

1. **Local-first**: The system runs on a single host without cloud dependency.
2. **Stdlib-only**: The Python control plane uses only the standard library.
3. **Bounded**: Every component has explicit, enforced resource bounds.
4. **Deterministic**: Benchmarks and tests use deterministic fixtures.
5. **Evidence-bearing**: The repository graph distinguishes observed from inferred relationships.
6. **Plan-only**: Design tools (specialist teams, hierarchy, delegation) do not dispatch.
7. **Read-only**: Analytics, telemetry, and execution graph projections do not mutate state.
8. **Explicit adapters**: External integrations are isolated from the control plane.
9. **Unknown preservation**: Unknown costs remain unknown; they are not zero.
10. **No false claims**: The system does not claim capabilities it does not have.
