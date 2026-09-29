# ADR-001: Local-first, single-host architecture

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

ApexGraphSwarm is an engineering workspace for repository intelligence, specialist teams, bounded swarm orchestration, evaluation, and cost-aware delegation. The system must operate without requiring cloud infrastructure, paid services, or network access for its core functionality. Users need to explore repositories, design teams, compare architectures, and measure scheduler behavior on their own machine.

## Decision

The entire system is **local-first and single-host**. The supported deployment is bound to loopback (`127.0.0.1:3010`). All state lives in local SQLite databases. No one-click cloud deployment (Vercel, Cloudflare, Supabase) is claimed. A hosted frontend alone cannot replace the durable local database, long-running runner, or private infrastructure connectivity.

## Alternatives considered

1. **Cloud-native deployment (Vercel/Supabase)**: Would simplify sharing but introduces tenant isolation, secrets management, and network dependency that conflict with the local-first principle.
2. **Distributed multi-node swarm**: Would enable scale but requires a distributed queue, consensus, and worker fleet — out of scope for an engineering workspace.
3. **Hybrid local + optional cloud**: Adds complexity without clear benefit; the system is designed for local evaluation and design, not production serving.

## Consequences

- **Positive**: No network dependency for core functionality; secrets never leave the machine; deterministic local benchmarks are reproducible; users retain full control of their data.
- **Negative**: No native multi-user collaboration; no horizontal scaling; users must run the system themselves; sharing results requires explicit export.
- **Migration path**: Future hosted operation would require selecting durable storage/queues, secrets management, tenant isolation, recovery, observability, and budget admission before exposing execution endpoints.

## Related

- ADR-002 (stdlib-only control plane)
- ADR-003 (SQLite control plane)
- ADR-006 (bounded execution model)
