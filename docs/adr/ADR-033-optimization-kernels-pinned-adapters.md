# ADR-033: Optimization kernels as pinned, audited adapters

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must integrate with four original optimization kernels for bounded graph selection, agent/task optimization, swarm/simulation optimization, and combined graph/swarm solving. These kernels must be pinned by source reference, audited, and explicitly bounded.

## Decision

**Optimization kernels are pinned, audited adapters with explicit capability boundaries.** Key characteristics:

- **Pinned sources**: Four kernels are pinned by source reference in `integrations/kernel-sources.json`.
- **Source audit**: Each kernel's source is audited for capabilities and limitations.
- **Capability matrix**: A capability matrix documents what each kernel does and does not do.
- **Bottleneck analysis**: A bottleneck analysis documents optimization limits.
- **No superiority claims**: "No universal NP-hard solver, optimality, or superiority claim follows from exposing these adapters."

**The four kernels:**

| Kernel | Role |
|--------|------|
| graph-rag-np-hard-kernel | Bounded graph selection and GraphRAG optimization experiments |
| agentic-np-hard-kernel | Agent/task optimization interfaces |
| mirofish-swarm-optimizer | Swarm/simulation optimization experiments |
| agentic-graph-swarm-kernel | Combined graph/swarm solver interfaces |

## Alternatives considered

1. **Unpinned latest versions**: Would be more up-to-date but would be unreproducible and unauditable.
2. **No kernel integration**: Would simplify the system but would prevent optimization experiments.
3. **Universal solver claims**: Would be misleading; no universal NP-hard solver exists.

## Consequences

- **Positive**: Reproducible experiments; audited sources; clear capability boundaries; no false claims.
- **Negative**: Pinned versions may become outdated; kernels require separate installation; no superiority claims.
- **Critical statement**: "No universal NP-hard solver, optimality, or superiority claim follows from exposing these adapters."

## Related

- ADR-002 (stdlib-only control plane)
- ADR-012 (explicit adapter pattern)
- ADR-016 (bounded local optimization)
