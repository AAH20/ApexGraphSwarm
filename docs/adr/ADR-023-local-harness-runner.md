# ADR-023: Local harness runner with fixed server-side policy

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must support running local harness profiles (OpenManus, Understand Anything) for model evaluation. This must be bounded, server-side controlled, and must not be an OS security sandbox.

## Decision

**The local harness runner uses fixed server-side policy with bounded execution.** Key characteristics:

- **Allowlisted profile identifiers**: Only pre-configured profiles can be run.
- **Bounded goals**: Goals are bounded in length and content.
- **Fixed server-side configuration**: Commands, workspaces, and authentication modes are fixed server-side.
- **Loopback bearer-protected interface**: The runner uses a loopback interface with bearer token protection.
- **Two-process cap**: Maximum two concurrent processes.
- **40-second limit**: Maximum execution time per run.
- **Bounded output**: Output is capped in size.
- **Not an OS security sandbox**: "It is not an OS security sandbox."
- **Example profiles start disabled**: Users must explicitly enable profiles.

**Critical limitations:**
- Opening an existing Understand Anything viewer does not analyze a repository.
- Local harness execution inherits the installed tool's permissions; use appropriate isolation for real workloads.

## Alternatives considered

1. **OS-level sandboxing**: Would be safer but is platform-specific and complex.
2. **No harness runner**: Would be safer but would prevent local model evaluation.
3. **Unbounded execution**: Would be more flexible but risks runaway processes and excessive cost.

## Consequences

- **Positive**: Bounded execution; server-side control; loopback protection; no unbounded processes.
- **Negative**: Not a security sandbox; inherits tool permissions; limited to allowlisted profiles; example profiles start disabled.
- **Critical statement**: "It is not an OS security sandbox."

## Related

- ADR-006 (bounded execution model)
- ADR-012 (explicit adapter pattern)
- ADR-014 (secret rejection and credential hygiene)
