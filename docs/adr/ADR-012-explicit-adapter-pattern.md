# ADR-012: Explicit adapter pattern for external integrations

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must integrate with external frameworks (LangGraph, CrewAI, Cognee, MiroFish, Hermes), model providers (OpenRouter, vLLM), and optimization kernels. These integrations must not compromise the local-first, stdlib-only control plane. Each integration must be explicit, configured, and bounded.

## Decision

**External integrations use explicit adapters that are isolated from the stdlib control plane.** Key characteristics:

- **Configured HTTP/service adapters**: Cognee, MiroFish, LangGraph, CrewAI, and Hermes require their documented service configuration. A successful submission can still require a later status check.
- **Optional local harness profiles**: OpenManus and Understand Anything depend on separately installed applications/plugins and reviewed profiles.
- **Pinned optimization kernels**: Four original kernels (graph-rag-np-hard-kernel, agentic-np-hard-kernel, mirofish-swarm-optimizer, agentic-graph-swarm-kernel) are pinned by source reference and audited.
- **MCP discovery**: Supports the documented handshake/HTTP subset and configured server profiles, with bounded responses and explicit compatibility limits.
- **Skills review**: Accepts skill manifests/content for provenance and metadata checks. Does not fetch, install, or execute arbitrary packages.

**Adapter principles:**
- Optional framework/service dependencies stay isolated from the stdlib control plane.
- A successful submission can still require a later status check.
- Inclusion in a comparison does not install or benchmark a project.
- No universal NP-hard solver, optimality, or superiority claim follows from exposing these adapters.

## Alternatives considered

1. **Direct imports of external frameworks**: Would couple the control plane to external dependencies, violating the stdlib-only constraint.
2. **No external integrations**: Would prevent comparison and evaluation of other frameworks.
3. **Implicit auto-discovery**: Would be convenient but would lack explicit configuration and boundary enforcement.

## Consequences

- **Positive**: Control plane remains stdlib-only; integrations are explicit and configurable; adapters can be audited and bounded; no hidden dependencies.
- **Negative**: Each adapter requires separate configuration; users must understand adapter limitations; some adapters require external services.
- **Critical statement**: "A routing plan or cost scenario does not itself change provider routing or execute models."

## Related

- ADR-001 (local-first architecture)
- ADR-002 (stdlib-only control plane)
- ADR-004 (Next.js web frontend)
- ADR-010 (specialist team design)
