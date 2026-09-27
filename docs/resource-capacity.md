# Resource concurrency capacity

`ControlStore` can enforce administrator-configured concurrency ceilings for exact resource identifiers, such as a configured model adapter or integration resource. Admission and claims use SQLite write transactions, so competing store connections sharing the same database cannot both consume the last slot.

Configure a resource locally through the control CLI:

```json
{"action":"configureResourceCapacity","dbPath":"/path/to/control.sqlite","resourceId":"adapter:model-x","maxConcurrency":2}
```

Read the bounded capacity snapshot with `{"action":"resourceCapacities","dbPath":"/path/to/control.sqlite","limit":1000}`. Reducing a cap below current occupied work fails. No web route configures capacity.

Legacy plans remain compatible: resources without a configured cap are uncapped unless a task explicitly opts in. A strict task opt-in has this shape:

```json
{"id":"review","agentId":"reviewer","dependencies":[],"payload":{},"reservedCostMicrousd":1000,"executionClass":"external","tool":"model:review","resource":"adapter:model-x","requireResourceCapacity":true,"resourceConcurrencyLimit":1}
```

An opted-in task requires an exact configured resource cap before `create_run` accepts the plan. Its `resourceConcurrencyLimit` is a per-run ceiling, combined with the administrator’s global cap; every task for that resource in the same run must opt in and declare the same limit. The field is metadata-enforced at claim time, while scheduler start times and deadline estimates remain advisory.

Running work occupies capacity. If an external task's lease expires or its effect is otherwise ambiguous, `needs_reconciliation` continues to hold its slot; lease expiry fences the old worker but does not prove a remote call stopped. Reconcile the task after inspecting the actual outcome to release the hold. A persisted successful output with unknown billing remains an unresolved ledger liability, but it no longer occupies an active-work slot because the call is known to have finished.

The status response includes each task’s opt-in fields and a capacity snapshot with configured global limit, global and run occupancy, per-run limit, and effective availability. This is local scheduler enforcement only: it does not provision provider capacity, stop remote work, or enforce limits outside processes sharing this SQLite database.
