# Local durable control plane

`apexgraphswarm.control.ControlStore` is a Python 3.10+ standard-library-only SQLite scheduler foundation. It persists plans, task state, append-only per-run event sequences, lease tokens and integer micro-USD accounting. It does not invoke a model, framework, repository command, or subprocess. Provider adapters must remain separate executors and explicitly report usage/cost.

```python
from apexgraphswarm.control import ControlStore

plan = {
    "version": 1,
    "agents": [{"id": "planner", "name": "Planner"},
               {"id": "reviewer", "name": "Reviewer"}],
    "tasks": [
        {"id": "inspect", "agentId": "planner", "dependencies": [],
         "payload": {"kind": "fixture"}, "reservedCostMicrousd": 0,
         "executionClass": "fixture", "maxAttempts": 2},
        {"id": "review", "agentId": "reviewer", "dependencies": ["inspect"],
         "payload": {"kind": "fixture"}, "reservedCostMicrousd": 0,
         "executionClass": "fixture"},
    ],
}

with ControlStore(".apexgraphswarm/control.sqlite3", max_active=4) as store:
    created = store.create_run(plan, idempotency_key="demo-001", budget_microusd=0)
    run_id = created["run"]["id"]
    lease = store.claim(run_id, "worker-1")
    store.complete(lease["taskId"], lease["leaseToken"], {"ok": True}, 0)
```

## Plan and admission contract

Plan version 1 contains exactly `version`, `agents`, and `tasks`. Each agent has a unique `id` and optional `name`. A task has unique `id`, declared `agentId`, `dependencies` (task IDs), JSON `payload`, integer `reservedCostMicrousd`, optional `maxAttempts` (default 1, maximum 10), and optional `executionClass` (defaults to `external`). Missing dependencies, duplicate/self edges, cycles, unknown agents, unsupported fields, oversized payloads, unknown cost, and reservations exceeding the run budget are rejected before rows are committed. Common credential field names are rejected inside task payloads; payload values must still use secret references, never plaintext credentials. Total plan size is capped at 2 MiB, task count at 10,000 and logical agents at 300 by default.

`budget_microusd` is mandatory and must be a non-negative exact integer. Paid work with unknown price/usage cannot be represented as zero: the caller must provide a reservation before creating a run. Each task reservation bounds total known spend across its attempts. The sum of admitted reservations may not exceed the run budget. Settlement records actual cost in integer micro-USD. If actual cost exceeds its task reservation, the scheduler records the spend, sets `budgetExceeded`, moves the run to `budget_exceeded`, and blocks further claims instead of discarding the overage. This records a breach; it cannot undo an external provider charge.

`executionClass` is one of:

- `fixture`: explicitly deterministic, zero-cost local fixture work. Expired leases may be retried automatically while attempts remain.
- `local_idempotent`: operator asserts repeat execution is safe. A nonzero/unknown-cost interrupted execution still requires reconciliation.
- `external_idempotent`: operator asserts the adapter uses provider-side idempotency. Explicit worker-reported retryable failure may retry, subject to remaining reservation; a crashed request still requires reconciliation because actual use may be unknown.
- `external`: default and safest class. No automatic retry after an ambiguous worker crash or cancellation.

Mark work as fixture only when it truly cannot call a paid service or cause external side effects. The control plane trusts the adapter's class declaration; it cannot inspect arbitrary callback code.

## Lease lifecycle and recovery

`claim(run_id, worker_id, lease_seconds=30, agent_id=None)` transactionally claims one dependency-ready task, optionally filtered by logical agent assignment. It returns an opaque `leaseToken` only to the claimant. Every completion, failure and heartbeat must present the current token; expired or replaced tokens are fenced. Leases last 1–300 seconds. A single database-wide active lease cap defaults to four and is persisted in the DB; reopening with a different configured cap is rejected. Up to 300 logical agents are independent of the active execution cap.

`heartbeat(task_id, lease_token, lease_seconds=30)` extends the current lease. `complete(task_id, lease_token, result, actual_cost_microusd)` stores bounded JSON result and settles known usage. `fail(..., retryable=True, actual_cost_microusd=...)` only schedules another try for the explicitly retry-safe classes and within attempts; worker failure must report actual cost. Results cap at 1 MiB; events cap at 64 KiB each.

`recover_expired()` (also run before a new claim) handles expired leases. Zero-cost `fixture` work can return to pending. External or otherwise ambiguous work moves to `needs_reconciliation`; its unspent reservation remains held and the run cannot claim more work. Do not automatically repeat an external action whose prior completion or charge is unknown.

`cancel(run_id)` fences current lease tokens and cancels pending tasks. In-flight zero-cost fixture/local-idempotent tasks can be canceled immediately; an in-flight external task becomes `needs_reconciliation`, its reservation remains held, and the run remains in that state until resolved. Cancellation is state bookkeeping, not a guarantee that an external provider stopped.

`reconcile(task_id, outcome=..., actual_cost_microusd=..., result=...)` resolves an ambiguous task after an operator or adapter checks the remote system. Outcomes are `succeeded`, `failed`, or `not_started`. `not_started` requires zero actual cost; it may return to pending only if cancellation was not requested and attempts remain. Reconciliation requires known actual cost and is itself transactional.

## Status document

`create_run`, `complete`, `fail`, `cancel`, and `reconcile` return the same status structure; `status(run_id)` returns it or `None`:

```json
{
  "run": {
    "id": "...", "status": "queued", "version": 1,
    "createdAt": 1000.0, "updatedAt": 1000.0,
    "idempotencyKey": "demo-001", "budgetMicrousd": 0,
    "reservedMicrousd": 0, "spentMicrousd": 0,
    "remainingMicrousd": 0, "budgetExceeded": false
  },
  "agents": [{"id": "planner", "name": "Planner"}],
  "tasks": [{
    "taskId": "...", "id": "inspect", "agentId": "planner",
    "status": "pending", "dependencies": [], "payload": {"kind": "fixture"},
    "attempts": 0, "maxAttempts": 2, "executionClass": "fixture",
    "reservedCostMicrousd": 0, "actualCostMicrousd": 0,
    "workerId": null, "leaseExpiresAt": null,
    "claimedAt": null, "completedAt": null, "result": null, "error": null
  }],
  "events": [{"sequence": 1, "type": "run.created", "taskId": null,
               "at": 1000.0, "data": {"taskCount": 2}}]
}
```

Run status is `queued`, `running`, `succeeded`, `failed`, `cancelled`, `needs_reconciliation`, or `budget_exceeded`; `cancelRequested` remains set while ambiguous work is being reconciled. Task status is `pending`, `running`, `succeeded`, `failed`, `cancelled`, or `needs_reconciliation`. Claim responses include the lease token; persisted status does not. Events are ordered by monotonically increasing per-run sequence and stored in the same transaction as their state transition. Event types include `run.created`, `task.claimed`, `task.heartbeat`, `task.completed`, `task.retry_scheduled`, `task.failed`, `task.lease_expired`, `task.requeued`, `task.needs_reconciliation`, `task.cancel_requested`, `task.cancelled`, `task.reconciled`, `run.budget_exceeded`, `run.cancel_requested`, `run.cancelled`, and `run.completed`.

`create_run(plan, idempotency_key=..., budget_microusd=...)` scopes the idempotency key to the database. Repeating an identical plan/budget returns the existing run; reusing the key for different input raises `ConflictError`. Multi-tenant deployments must include a verified tenant scope in the admission layer/key and add tenant authorization to stored records before sharing a DB.

## JSON-lines CLI

Run `python -m apexgraphswarm.control` from the project root. It reads one JSON request from stdin and writes one JSON response to stdout. The wrapper has no network access and invokes no external process. `dbPath` selects a local database path; keep it outside public/static web directories and out of Git.

```json
{"action":"create","dbPath":".apexgraphswarm/control.sqlite3","maxActive":4,"idempotencyKey":"demo-001","budgetMicrousd":0,"plan":{"version":1,"agents":[{"id":"planner"}],"tasks":[{"id":"inspect","agentId":"planner","dependencies":[],"payload":{"kind":"fixture"},"reservedCostMicrousd":0,"executionClass":"fixture"}]}}
```

Supported actions: `initialize`, `create`, `status`, `claim`, `heartbeat`, `complete`, `fail`, `cancel`, `recover`. `claim` accepts `runId`, `workerId`, optional `leaseSeconds` and `agentId`; `heartbeat` accepts `taskId`, `leaseToken` and optional `leaseSeconds`; `complete` accepts `taskId`, `leaseToken`, `result`, `actualCostMicrousd`; `fail` also accepts `error`, optional `retryable` and actual cost; `cancel` accepts `runId`. `recover` returns requeued and terminal-failure counts; pending ambiguous external work is counted separately by its persisted `needs_reconciliation` status.

## Deployment boundary

This is a durable single-host foundation, not a complete multi-tenant production control plane. SQLite WAL plus `BEGIN IMMEDIATE` serializes claims and makes rows survive process restart, but there is no tenant/RBAC model, distributed queue, secret broker, fairness policy, event streaming endpoint, automated remote-job poller, provider budget estimator, worktree manager, sandbox, or CPU/memory/network enforcement. Cancellation of an external request only fences the local lease until its outcome is reconciled. Keep all worker processes configured with the database's persisted `max_active` and `max_registered_agents` values. Back up the database and test restore before using it for valuable state.
