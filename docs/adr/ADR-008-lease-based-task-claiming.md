# ADR-008: Lease-based task claiming with fencing

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The control plane must support concurrent workers claiming tasks from a shared DAG. Workers may crash, hang, or be delayed. The system must prevent duplicate execution, detect stale leases, and recover from worker failures without losing state.

## Decision

**Lease-based task claiming with token fencing** is the concurrency model:

1. **Claim**: `claim(run_id, worker_id, lease_seconds=30, agent_id=None)` transactionally claims one dependency-ready task. Returns an opaque `leaseToken` only to the claimant.
2. **Heartbeat**: `heartbeat(task_id, lease_token, lease_seconds=30)` extends the current lease.
3. **Complete**: `complete(task_id, lease_token, result, actual_cost_microusd)` stores bounded JSON result and settles known usage.
4. **Fail**: `fail(..., retryable=True, actual_cost_microusd=...)` schedules another try only for explicitly retry-safe classes and within attempts.
5. **Recovery**: `recover_expired()` handles expired leases before a new claim. Zero-cost `fixture` work can return to pending; external or ambiguous work moves to `needs_reconciliation`.

**Fencing**: Every completion, failure, and heartbeat must present the current lease token. Expired or replaced tokens are fenced — the operation is rejected. This prevents a crashed worker from completing a task that has been re-claimed by another worker.

**Lease duration**: 1–300 seconds. The active lease cap is database-wide and defaults to 4.

## Alternatives considered

1. **No leasing (first-come-first-served)**: Would be simpler but would not handle worker crashes or prevent duplicate execution.
2. **Heartbeat-only without tokens**: Would detect crashes but would not prevent a crashed worker from completing a task after recovery.
3. **Distributed consensus (Raft/Paxos)**: Would provide stronger guarantees but is overkill for a single-host SQLite system.
4. **External job queue (Celery, RQ)**: Would provide mature leasing but adds dependencies and deployment complexity.

## Consequences

- **Positive**: Prevents duplicate execution; handles worker crashes; transactional integrity; no external dependencies; works offline.
- **Negative**: Requires workers to present tokens correctly; expired leases require recovery; external work that crashes requires manual reconciliation.
- **Critical rule**: "Do not automatically repeat an external action whose prior completion or charge is unknown."

## Related

- ADR-003 (SQLite control plane)
- ADR-006 (bounded execution model)
- ADR-009 (execution classes)
