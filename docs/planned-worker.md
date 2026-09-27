# Execute a compiled graph-review task

The operator-driven worker executes one existing durable task, using its stored
inputs. It does not create another run. OpenRouter and vLLM single graph reviews
are supported; automatic swarm loops and coding harness execution are not part
of this worker.

## Prepare and activate

1. Compile with `task_inputs` in Python, or `taskInputs` in the local lab JSON.
   Provide every source task's explicit goal, graph snapshot and bounded output
   parameters. Plain schedule compilation remains metadata-only.
2. Independently configure the actual endpoint/model and server integration
   policy. The stored adapter/model/resource/tool and integer reservation must
   exactly match that policy. Caller assertions of readiness do not bypass it.
3. Through the local control CLI, configure `configureResourceCapacity` with
   `resourceId` and `maxConcurrency`. Enroll the worker and grant its principal
   the exact tool/resource and budget with an expiry. Keep credentials in the
   server environment or a secret manager; never embed them in plans.
4. Create the compiled `plan` through `ControlStore.create_run` using a unique
   idempotency key and the compiled run budget. Tasks require a configured exact
   resource cap and carry their per-run resource concurrency limit. Inspect the
   returned persisted run and task UUIDs before execution.
5. Load that run in Swarm Control and select **Run configured review**, or run
   from `apps/web` with the already configured environment:

   ```sh
   npm run worker:task -- RUN_ID TASK_ID
   ```

The CLI and authenticated `POST /api/planned-tasks` accept only run/task IDs.
There is no browser override for goal, graph, model, grant, policy or reservation.
The web route allows two active requests per process, a 1 KiB body and a
45-second abort deadline. The control store atomically arbitrates claims across
processes. It is the authoritative duplicate-execution boundary; process-local
HTTP admission is only an additional bound.

## Execution and evidence

The worker validates stored inputs before claiming the exact task. Claims check
dependencies, identity, grants, budgets and resource slots. Provider invocation
requires a durable start checkpoint and a fresh lease/grant check. Heartbeats
renew the lease while work proceeds. Response evidence and normalized receipts
are saved through the existing durable adapter. The result's execution run ID
is the original compiled run ID. A repeated trigger cannot claim an already
claimed or completed task.

Only one bounded model call is admitted. No API call occurs during compilation,
activation validation or a rejected trigger. Running an admitted task can incur
provider charges. Estimated reservations do not impose a provider-side monetary
cap, and actual overages must still be recorded.

Aborting one worker does not cancel sibling tasks or the whole run. The abort
signal cannot prove the provider stopped. Unknown effects/costs retain liability
and may require operator receipt reconciliation; no automatic external replay
occurs. Existing run cancellation intentionally affects the whole run and is a
separate action. A completed response with unknown money can release an execution
slot while retaining its financial reservation; ambiguous in-flight effects
continue occupying capacity until reconciled.

The runtime enforces dependency readiness and global/per-run resource slots.
Planned start/finish offsets and deadlines remain estimates; this is not a
real-time scheduler or a guarantee that measured durations match a schedule.
Stored input hashes provide provenance, not an external evaluator attestation.
The graph review adapter sends bounded graph context and excerpts node summaries
using its existing limits; results are not comprehensive source-code execution.
