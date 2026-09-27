# Local execution grants and receipts

`ControlStore` keeps the existing SQLite run, lease, and spend tables and adds
`access_grants` and `execution_attempts`. Existing databases receive additive
tables and task scope columns when opened. Old attempts are not reconstructed:
`coverageComplete` is false and the missing historical attempt count is included
in `unresolvedCostCount`.

Every nonfixture task should declare exact `tool` and `resource` strings in its
plan. Legacy unscoped external tasks can still be read, but `claim()` rejects
them. Fixture tasks remain grant-free. For a paid task, create a grant and pass
the same trusted principal string when claiming:

```python
grant = store.grant_access(
    principal_id="worker-service",
    tool_id="provider.invoke",
    resource_id="model:vendor/model-v1",
    max_budget_microusd=250000,
    expires_at=1_800_000_000,
)
task = store.claim(run_id, "worker-17", principal_id="worker-service")
```

The grant must match principal, tool, and resource exactly. Its ceiling includes
settled spend and active or unresolved reservations across every task using the
grant. A lease cannot extend beyond grant expiry. Heartbeats recheck expiry and
revocation; revoking a grant cannot stop side effects already underway, so an
interrupted external attempt remains unresolved until `reconcile()` records its
outcome and known cost.

`store.ledger(run_id, limit=1000)` returns stable attempt IDs, worker/principal,
grant and tool/resource attribution, receipt outcome, reserved cost, and actual cost. Unknown
actual cost is JSON `null`; it is never converted to zero. `store.status()`
includes the newest 100 receipts plus aggregate coverage and cost fields. The
CLI JSON actions are `grantAccess`, `revokeAccess`, `claim` (with `principalId`),
and `ledger` (optional `runId`, bounded `limit`). Grant/revoke CLI access is a
local administrative operation.

The principal is a caller-supplied local identifier. This layer does not
authenticate that identity, mediate every provider/network/harness path, or
sandbox arbitrary code. It provides exact policy checks at `ControlStore.claim`
and does not claim production IAM enforcement.


## Worker credentials and checkpoints

Local administrators enroll workers with a unique `workerId`, the exact
`principalId` used in grants, and a Unix expiry timestamp. `enrollWorker`
returns one opaque 256-bit credential once; SQLite stores only its SHA-256
hash. Keep the CLI response private and deliver the credential through the
local secret manager or protected environment. Never put it in a plan, result,
checkpoint, event, or UI payload. Revoke with `revokeWorker`; use a new worker
ID for a replacement enrollment.

External transitions on the control CLI use `authClaim`, `authHeartbeat`,
`authComplete`, and `authFail`. Each request includes `workerId` and
`credential`; task transitions also include both `taskId` and the current
`leaseToken`. The credential fixes the worker and principal identity. The
control plane verifies the active worker record and lease inside the same
SQLite transaction. Worker expiry caps the lease. Claims and heartbeats recheck
the current capability grant; authenticated worker operations recheck worker
revocation/expiry. The legacy Python methods remain for trusted
in-process callers; the CLI rejects unauthenticated claim/heartbeat/complete/
fail actions.

Before dispatching an external call, the adapter can append an
`authCheckpoint` with a stable ID such as `<call-id>:started`; after receiving a
response it can append `<call-id>:receipt` with sanitized output and provider
receipt data. Checkpoints are append-only and idempotent for the same ID and
canonical JSON. Each attempt accepts at most 12 checkpoints, 64 KiB per value,
and 128 KiB total. Secret-bearing fields and the worker credential itself are
rejected. Status and ledger show bounded checkpoint IDs and hashes; the local
`checkpoints` CLI action returns at most 12 stored values for an attempt.
Checkpoints do not settle cost or release budget.

`authComplete` accepts a successful result with unknown actual cost by omitting
`actualCostMicrousd`. It persists the result, records a NULL-cost attempt receipt,
and marks the task `needs_reconciliation`, retaining the run and grant
reservations. An administrator later reconciles the known amount; a persisted
successful output cannot be reconciled as `not_started`.

`authFail` may also omit `actualCostMicrousd` for cancellation or an outcome
whose spend is unknown. It immediately clears the live lease, records a NULL
cost failure receipt, and leaves the task in `needs_reconciliation` with its
reservation held. An identical retry from the same valid worker credential,
lease token, and error is idempotent; a changed replay conflicts. Unknown-cost
failures cannot be automatically retried. An already-running worker may append
audit checkpoints and report failure after its capability grant is revoked,
but revoking or expiring the worker identity still blocks those operations.
