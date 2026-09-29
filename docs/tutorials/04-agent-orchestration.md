# Tutorial 4: Agent Orchestration

## Overview

The ApexGraphSwarm control plane is a durable, SQLite-backed task orchestration system. It persists task DAGs, dependency-ready claims, lease tokens, fenced completion, ordered events, recovery state, and integer micro-USD accounting. This tutorial covers the architecture, API, and operational patterns.

## Architecture

```
apexgraphswarm/              Python graph analyzer, preview utilities, SQLite control plane
apps/web/app/               Next.js workspace routes and API endpoints
apps/web/components/        Graph, team, orchestration, evaluation and cost interfaces
apps/web/lib/               Domain contracts, validation, routing and integration logic
```

The control plane (`apexgraphswarm.control.ControlStore`) uses SQLite transactions to persist:
- Task DAGs (directed acyclic graphs of work)
- Dependency-ready claims (which task is ready to run)
- Lease tokens (opaque, fenced completion tokens)
- Ordered events (append-only per-run event sequences)
- Recovery state (expired lease handling)
- Integer micro-USD accounting (budgets, reservations, actual costs)

It does **not** invoke a model, framework, repository command, or subprocess. Provider adapters must remain separate executors.

## Python API

### Creating a Run

```python
from apexgraphswarm.control import ControlStore

plan = {
    "version": 1,
    "agents": [
        {"id": "planner", "name": "Planner"},
        {"id": "reviewer", "name": "Reviewer"}
    ],
    "tasks": [
        {
            "id": "inspect",
            "agentId": "planner",
            "dependencies": [],
            "payload": {"kind": "fixture"},
            "reservedCostMicrousd": 0,
            "executionClass": "fixture",
            "maxAttempts": 2
        },
        {
            "id": "review",
            "agentId": "reviewer",
            "dependencies": ["inspect"],
            "payload": {"kind": "fixture"},
            "reservedCostMicrousd": 0,
            "executionClass": "fixture"
        }
    ]
}

with ControlStore(".apexgraphswarm/control.sqlite3", max_active=4) as store:
    created = store.create_run(plan, idempotency_key="demo-001", budget_microusd=0)
    run_id = created["run"]["id"]
```

### Claiming and Completing Work

```python
    lease = store.claim(run_id, "worker-1")
    store.complete(lease["taskId"], lease["leaseToken"], {"ok": True}, 0)
```

### Heartbeating

```python
    store.heartbeat(task_id, lease_token, lease_seconds=30)
```

### Recovery

```python
    store.recover_expired()  # Handles expired leases before new claims
```

### Reconciliation

```python
    store.reconcile(task_id, outcome="succeeded", actual_cost_microusd=0, result={...})
```

## Plan and Admission Contract

Plan version 1 contains exactly `version`, `agents`, and `tasks`.

**Validation rules:**
- Each agent has a unique `id` and optional `name`
- Each task has unique `id`, declared `agentId`, `dependencies` (task IDs), JSON `payload`, integer `reservedCostMicrousd`, optional `maxAttempts` (default 1, maximum 10), and optional `executionClass`
- Missing dependencies, duplicate/self edges, cycles, unknown agents, unsupported fields, oversized payloads, unknown cost, and reservations exceeding the run budget are **rejected before rows are committed**
- Common credential field names are rejected inside task payloads
- Total plan size is capped at **2 MiB**, task count at **10,000**, logical agents at **300**

### Budget Semantics

`budget_microusd` is mandatory and must be a non-negative exact integer. Paid work with unknown price/usage **cannot** be represented as zero — the caller must provide a reservation before creating a run.

If actual cost exceeds its task reservation, the scheduler:
1. Records the spend
2. Sets `budgetExceeded`
3. Moves the run to `budget_exceeded`
4. Blocks further claims

This records a breach; it cannot undo an external provider charge.

## Execution Classes

| Class | Behavior |
|-------|----------|
| `fixture` | Deterministic, zero-cost local fixture work. Expired leases may be retried automatically. |
| `local_idempotent` | Operator asserts repeat execution is safe. Nonzero/unknown-cost interrupted execution still requires reconciliation. |
| `external_idempotent` | Operator asserts adapter uses provider-side idempotency. Explicit worker-reported retryable failure may retry. |
| `external` | Default and safest class. No automatic retry after ambiguous worker crash or cancellation. |

Mark work as `fixture` only when it truly cannot call a paid service or cause external side effects.

## Lease Lifecycle

1. **Claim** — `claim(run_id, worker_id, lease_seconds=30, agent_id=None)` transactionally claims one dependency-ready task. Returns an opaque `leaseToken`.
2. **Heartbeat** — `heartbeat(task_id, lease_token, lease_seconds=30)` extends the current lease.
3. **Complete** — `complete(task_id, lease_token, result, actual_cost_microusd)` stores bounded JSON result and settles known usage.
4. **Fail** — `fail(..., retryable=True, actual_cost_microusd=...)` schedules another try for explicitly retry-safe classes.

Leases last **1–300 seconds**. A single database-wide active lease cap defaults to **four** and is persisted in the DB. Up to **300 logical agents** are independent of the active execution cap.

## Recovery and Reconciliation

`recover_expired()` handles expired leases:
- Zero-cost `fixture` work returns to `pending`
- External or ambiguous work moves to `needs_reconciliation`
- Unspent reservation remains held
- Run cannot claim more work until resolved

`reconcile(task_id, outcome, actual_cost_microusd, result)` resolves ambiguous tasks after an operator checks the remote system. Outcomes: `succeeded`, `failed`, or `not_started`.

## Status Document

All mutating operations return the same status structure:

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
    "status": "pending", "dependencies": [],
    "payload": {"kind": "fixture"},
    "attempts": 0, "maxAttempts": 2, "executionClass": "fixture",
    "reservedCostMicrousd": 0, "actualCostMicrousd": 0,
    "workerId": null, "leaseExpiresAt": null,
    "claimedAt": null, "completedAt": null, "result": null, "error": null
  }],
  "events": [{"sequence": 1, "type": "run.created", "taskId": null, "at": 1000.0, "data": {"taskCount": 2}}]
}
```

**Run statuses:** `queued`, `running`, `succeeded`, `failed`, `cancelled`, `needs_reconciliation`, `budget_exceeded`

**Task statuses:** `pending`, `running`, `succeeded`, `failed`, `cancelled`, `needs_reconciliation`

## JSON-Lines CLI

Run `python -m apexgraphswarm.control` from the project root. It reads one JSON request from stdin and writes one JSON response to stdout.

```json
{"action":"create","dbPath":".apexgraphswarm/control.sqlite3","maxActive":4,"idempotencyKey":"demo-001","budgetMicrousd":0,"plan":{"version":1,"agents":[{"id":"planner"}],"tasks":[{"id":"inspect","agentId":"planner","dependencies":[],"payload":{"kind":"fixture"},"reservedCostMicrousd":0,"executionClass":"fixture"}]}}
```

**Supported actions:** `initialize`, `create`, `status`, `claim`, `heartbeat`, `complete`, `fail`, `cancel`, `recover`

## Swarm Control UI

Navigate to [http://127.0.0.1:3010/swarm](http://127.0.0.1:3010/swarm) for the Swarm Control interface. It displays:
- Ledger coverage
- Unresolved cost
- Inspectable attempt receipts
- Execution graph connecting logical agents, tasks, attempts, workers, principals, grants, and resources

## Deployment Boundary

This is a **durable single-host foundation**, not a complete multi-tenant production control plane. It provides:
- SQLite WAL + `BEGIN IMMEDIATE` for serialized claims
- Process restart survival
- No tenant/RBAC model, distributed queue, secret broker, fairness policy, event streaming, automated remote-job poller, provider budget estimator, worktree manager, sandbox, or CPU/memory/network enforcement

Keep all worker processes configured with the database's persisted `max_active` and `max_registered_agents` values. Back up the database and test restore before using it for valuable state.

## Next Steps

- [Tutorial 5: Governance](05-governance.md) — Design specialist teams with proper authority.
- [Tutorial 8: Deployment](08-deployment.md) — Deploy the control plane for production use.
