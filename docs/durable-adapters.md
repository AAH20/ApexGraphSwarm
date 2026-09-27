# Durable external adapter dispatch

External integrations use the local SQLite control store before calling a configured provider, framework or harness. Local deterministic kernels remain local experiments. No worker is automatically enrolled and no grant is fabricated from a browser team design.

## Setup

Run the control CLI from the repository root, sending one JSON object on stdin to `python3 -m apexgraphswarm.control`. All operations use the same `dbPath` (default `.runtime/control.sqlite` for the web app).

1. Local administrator: `enrollWorker` with `workerId`, `principalId`, and future Unix-seconds `expiresAt`. Store its one-time `data.credential` only in server secret configuration as `APEX_WORKER_CREDENTIAL`; set `APEX_WORKER_ID`. The database stores a credential hash.
2. Local administrator: `grantAccess` for that principal, exact `tool` such as `integration:openrouter:review`, exact `resource` such as `model:your-configured-model`, integer `maxBudgetMicrousd`, and future `expiresAt`.
3. Configure the provider normally, then define a matching policy in `APEX_INTEGRATION_POLICIES_JSON`:

```json
[{"integrationId":"openrouter","operation":"review","resourceId":"model:your-configured-model","modelId":"your-configured-model","maxCostMicrousd":1000,"maxProviderCalls":1}]
```

The amount above is an illustrative USD 0.001 reservation, not a quoted model price. The configured model ID must match exactly. Framework parameters must match `parameterEquals`; harness profiles must pin `harnessId` and `authMode`. AI Gateway review/swarm use integration ID `ai-gateway` and `GRAPH_REVIEW_MODEL`.

The operator also configures the existing API access token. Browser requests cannot enroll workers, grant themselves capabilities, choose arbitrary endpoints or supply their own principal. Local administrators can revoke a worker or grant through `revokeWorker`/`revokeAccess`.

## Execution and cost evidence

A durable task is created and claimed using the enrolled identity. A started checkpoint precedes each instrumented invocation, followed by immediate grant/lease revalidation and periodic renewal. Revocation does not undo an external action already accepted by a service. Audit checkpoints can still preserve evidence after a grant is revoked.

OpenRouter usage costs retain exact USD decimal text and conservatively round upward to integer microUSD for accounting. Missing, invalid or mismatched usage remains unknown. Outputs survive unresolved billing; unknown liability keeps its reservation. Partial specialist results persist even when a sibling fails. A provider response is not an independently reconciled invoice.

Policies limit planned call count (default one, or three for delegation/swarm), output size (at most 600 tokens for direct integrations; 1,000 for AI Gateway review), and admission reservations. Unknown call costs retain their per-call reservation. **These are not provider-enforced spending caps.** Provider-side limits and verified rates are still needed to constrain actual charges. SDK-internal tool loops are instrumented as parent operations rather than complete per-generation receipts; do not infer per-generation cost from the parent count.

`status` and `ledger` expose bounded checkpoint metadata; the local `checkpoints` action reads full saved values for a task. Checkpoint bodies are bounded and reject secret-shaped fields; configured secrets are redacted before persistence. Review returned content before sharing exports.

Python subprocesses receive only a minimal runtime environment, not provider credentials. The normalizer consumes selected receipt metadata over stdin. Frameworks, local harnesses and vLLM do not automatically produce authoritative monetary receipts, so their charges remain unresolved.

## Request retries and cancellation

`POST /api/integrations` requires an `Idempotency-Key` header containing 1–200 visible ASCII characters. While retained, the same key and normalized body return the same job; changing the body returns HTTP 409. The UI preserves a pending key after an uncertain submission. Only hashes are stored in the runtime index.

The request registry persists hashed keys, credential scope, canonical request hashes and stable job IDs in SQLite. The same registered request is never automatically redispatched after a restart or loss of in-memory job state: the API returns recovery-required with the known durable run reference when available. The registry is capped at 100,000 records and does not evict entries. Credential rotation starts a new scope. See [request registry and recovery](request-registry.md). The separate AI Gateway review/swarm routes do not provide this request-key contract.

Cancellation reports promptly but keeps a concurrency slot occupied until the underlying adapter actually settles. Unknown-cost failures promptly enter reconciliation while retaining reservations. Aborting a network request is not proof that a provider stopped generation.

## Boundaries

The store is local SQLite, not a distributed scheduler. Local administrative APIs remain trusted. A network abort does not prove remote cancellation, and uncertain effects must be reconciled before retrying. Model outputs and tool results remain untrusted. Existing scheduling recommendations do not automatically select a provider or dispatch an optimized fleet.
