# Integration request replay registry

`POST /api/integrations` validates the request and then atomically registers a
scoped idempotency key in the same SQLite file used by the durable control
plane (`APEX_CONTROL_DB_PATH`, or `.runtime/control.sqlite`). The registry
stores only SHA-256 digests of the request key, authenticated server-token
scope, and canonical JSON body, plus the stable in-memory job UUID. Raw keys,
tokens, prompts, and bodies are not stored in the registry.

Within the current process, an identical request returns the original job.
Reusing the scoped key with another body returns HTTP 409. If the durable
registry entry exists but its in-memory job is unavailable (including after a
server restart), the route returns HTTP 409 with `recovery.jobId` and the
`recovery.durableRunIdempotencyKey` (`integration-<jobId>`). It will not
redispatch automatically. Inspect the corresponding durable control run and
ledger before deciding whether to retry.

Registry records are never evicted. At 100,000 records it refuses new request
registrations rather than opening old keys to accidental redispatch. A new
server access token creates a distinct request scope, so token rotation is an
idempotency boundary: retries after rotation do not match prior keys. This
scope is not a multi-tenant identity system. Deployments needing stable
cross-rotation or tenant scopes require an authenticated workspace identity.

The registry prevents duplicate dispatch after process uncertainty; it is not
a durable worker queue and does not resume execution across restarts.
