# OpenRouter receipt reconciliation

OpenRouter calls can complete while the local worker loses the provider response or cannot persist a usable usage receipt. The scheduler then retains the task reservation in `needs_reconciliation`; it does not treat missing cost as zero or retry the paid operation automatically.

The local operator reconciliation helper is `apexgraphswarm.receipt_reconciliation.reconcile_openrouter_task(store, task_id, entries, operator_id=...)`. Each entry is `{ "attempt": 1, "callId": "call-…", "payload": { ...OpenRouter receipt metadata... } }`. The payload may be a completion response or a generation metadata response accepted by `normalize_openrouter_receipt`. It must contain a USD cost and the matching generation ID and returned model.

The helper only accepts OpenRouter review/delegation tasks awaiting reconciliation. It reads the request model and generation ID from the saved started/response checkpoints, rejects missing identities, and requires exactly one supplied receipt for every saved started call across all attempts. It does not infer IDs from the supplied receipt, fetch remote data, or make a provider request. Keep receipt payloads limited to provider accounting metadata; generated text is not needed for settlement.

Settlement re-reads attempt and checkpoint state inside one SQLite write transaction. Known attempt costs are checked against the corresponding provider receipts and remain charged once. Only the sum for unresolved attempts is added to cumulative task/run/grant spend. Each OpenRouter USD amount is rounded upward independently to integer micro-USD using `ROUND_CEILING`; this prevents fractional micro-USD values from disappearing when several calls are aggregated. Exact provider USD strings and normalized token/model/generation metadata are retained in the reconciliation audit record.

Each OpenRouter generation ID is globally claimed for one task/attempt/call/model in SQLite when its response checkpoint is first persisted. The unique constraint prevents two calls—even in different tasks—from being attributed the same provider generation. Startup backfills this ownership from both response checkpoints and prior reconciliation audit records. If legacy evidence has conflicting owners or cannot be bound unambiguously, the store fails closed on every reopen until the database is reviewed; it does not silently reassign the ID.

Successful model output is preserved unchanged. Reconciliation changes accounting status only: a task with retained successful output becomes `succeeded`; a task without successful output becomes `failed` after costs are known. A missing, malformed, partial, conflicting, or identity-mismatched receipt leaves the task unresolved and its liability reserved. A replay with the identical normalized evidence and operator identity is idempotent; different evidence after settlement conflicts.

The stored provenance is explicitly `trusted_local_operator_assertion`. The caller-provided operator ID and generation ID are attribution/reconciliation keys, not cryptographic proof that OpenRouter emitted the supplied payload. An operator should obtain metadata from an authenticated provider account or trusted local record and preserve that source outside the application when a stronger audit trail is required. Raw provider payload strings are not retained; only the normalized accounting subset is stored.

For a local stdin/stdout invocation, use the module CLI with one bounded JSON request:

```json
{
  "action": "reconcileOpenRouterReceipts",
  "dbPath": "/absolute/path/to/control.sqlite3",
  "taskId": "task-id",
  "operatorId": "operator-alias",
  "receipts": [
    {
      "attempt": 1,
      "callId": "call-1",
      "payload": {
        "id": "gen-…",
        "model": "provider/returned-model",
        "usage": {"cost": "0.000001", "prompt_tokens": 12, "completion_tokens": 4, "total_tokens": 16}
      }
    }
  ]
}
```

Run it with `python3 -m apexgraphswarm.receipt_reconciliation`. Input and receipt metadata are bounded; the command prints a status response or a sanitized validation error. It does not contact OpenRouter or accept a caller-supplied URL/API key.

vLLM GPU allocation estimates remain separate from this path. Those estimates are not provider bills and cannot settle an OpenRouter task.
