# ADR-006: Bounded execution model with explicit resource caps

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must prevent runaway execution — unbounded task counts, infinite loops, excessive memory, or uncontrolled cost. Every component must have explicit, enforced resource bounds. This is a core design principle stated throughout the codebase: "bound work and costs."

## Decision

**Every component enforces explicit resource bounds.** Key bounds include:

| Component | Bound |
|-----------|-------|
| Control plane plan size | 2 MiB |
| Control plane task count | 10,000 |
| Control plane logical agents | 300 |
| Control plane active leases | 4 (default), 64 (max) |
| Control plane max attempts | 10 per task |
| Control plane lease duration | 1–300 seconds |
| Control plane result size | 1 MiB |
| Control plane event size | 64 KiB |
| Control plane checkpoint | 64 KiB each, 128 KiB total, 12 per attempt |
| Graph UI visible nodes | 1,800 |
| Graph UI visible edges | 12,000 |
| Graph import | 25,000 nodes / 100,000 edges / 15 MB |
| Analyzer files | 2,000 |
| Analyzer symbols | 10,000 |
| Analytics live rows | 200,000 |
| Analytics import rows | 10,000 |
| Optimization tasks | 500 |
| Optimization options | 2,000 |
| Optimization exact schedule tasks | 8 |
| Optimization exact coverage items | 18 |
| Specialist designers | 300 specialists, 64 teams, 300 scope nodes |
| Specialist skills/tools | 32 each per specialist |
| Specialist import size | 512 KiB |
| Harness runner | 2-process cap, 40-second limit |
| Telemetry body | 2 MiB |
| Telemetry metric lines | 100,000 |

**Budget enforcement**: Paid work must carry an explicit integer micro-USD reservation at admission. Unknown cost cannot be represented as zero. Budget overruns are recorded and block further claims; accounting cannot reverse a charge already made by a provider.

## Alternatives considered

1. **Unbounded execution with user discretion**: Would allow more flexibility but risks runaway cost, infinite loops, and resource exhaustion.
2. **Soft limits with warnings**: Would be less disruptive but could be ignored; the system prioritizes safety over convenience.
3. **External resource enforcement (cgroups, containers)**: Would provide OS-level isolation but adds platform complexity and is not available in all environments.

## Consequences

- **Positive**: Predictable resource usage; no runaway cost; safe for local experimentation; clear error messages when bounds are exceeded.
- **Negative**: Large workloads must be split across multiple runs; users must understand and respect bounds; some valid use cases may exceed default limits.
- **Design principle**: Bounds are operating limits, not latency guarantees. Users should narrow dense graphs and inspect truncation warnings.

## Related

- ADR-001 (local-first architecture)
- ADR-003 (SQLite control plane)
- ADR-009 (execution classes)
- ADR-011 (cost accounting)
