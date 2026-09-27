# Planned graph-review dispatch contract

The Python plan compiler has two modes. Calling
`compile_delegation_plan(problem, model_bindings)` produces `planMode:
"compile_only_metadata"`; it does not contain executable model input and does
not require activation capacity. To prepare explicit, durable graph-review
tasks, pass `task_inputs` keyed by every scheduled source task ID. The keys
must match the scheduled task set exactly, with no missing or extra entries.

Example:

```python
task_inputs = {
    "inspect": {
        "goal": "Identify dependency evidence relevant to this review.",
        "graph": {
            "version": 1,
            "name": "example-repository",
            "nodes": [
                {"id": "n1", "name": "engine.py", "kind": "file",
                 "path": "src/engine.py", "summary": "Entry point",
                 "confidence": "parsed"}
            ],
            "edges": [],
            "warnings": [],
            "truncated": False
        },
        "parameters": {"maxOutputTokens": 600}
    }
}
```

The compiler validates an explicit non-empty goal (at most 2,000 characters),
the full graph snapshot's structure and evidence fields, at most 300 nodes and
900 edges, a 2 MB request-size bound, and `maxOutputTokens` from 100 through
600. If omitted, `maxOutputTokens` is normalized to 600. It preserves the graph
snapshot it accepts; it does not slice, summarize, or infer hidden prompt text.
The entire compiled durable plan is also capped at 1 MB because per-task
snapshots are persisted into the control ledger.
It emits each review as:

```json
{
  "execution": {
    "version": 1,
    "integrationId": "openrouter",
    "operation": "review",
    "input": {
      "goal": "Identify dependency evidence relevant to this review.",
      "graph": {"version": 1, "name": "example-repository", "nodes": [], "edges": []},
      "parameters": {"maxOutputTokens": 600}
    }
  }
}
```

Only exact `openrouter` or `vllm` adapters with `review` operation are eligible.
The surrounding durable task continues to pin its exact `modelId`, `tool`, and
`resource`; the runtime dispatcher must validate these against the server's
configured integration catalog and policy before invocation. Unknown graph
evidence is rejected rather than stripped. The ordinary adapter currently
constructs model context from snapshot metadata and node/edge fields, truncates
each node summary to 240 characters, and does not pass warning or unresolved
lists as review evidence; therefore a stored graph is the full task input, not
a claim that every field reaches the model prompt verbatim.

Execution-enabled durable tasks additionally set
`requireResourceCapacity: true` and `resourceConcurrencyLimit` to the selected
model's declared schedule capacity. An administrator must configure the exact
resource's global capacity in the control store before run activation. Create
and claim transactions enforce the minimum of that global cap and the
per-plan concurrency limit. Missing global capacity blocks activation; the
compiler cannot check or configure database state. This runtime enforcement
limits active task effects, but it does not enforce scheduler-predicted
start/finish offsets or deadlines.

The planned runtime bridge contract is
`withPlannedTaskDispatch(runId, taskId, env, signal, invoke)`. It loads the
stored run/task, validates the nested request with the same
`parseIntegrationRequest` policy used by ordinary model reviews, checks exact
model, operation, tool, resource, configured reservation, and capacity fields,
and atomically claims that exact task before invoking the existing
OpenRouter/vLLM adapter. The invocation uses ordinary heartbeat, provider-call
reservation, checkpoint, receipt reconciliation, and settlement behavior. It
must not synthesize an untracked task or use a browser-provided resource,
model, database path, key, or spend cap.

`reservedCostMicrousd` and `costMicrousd` in the schedule are caller-provided
estimates and a durable admission reservation. They do not establish live
prices or cap provider spend. The provider can charge more, or report unknown
cost; the ledger then preserves unresolved liability and reconciliation
requirements. The plan's `planMode: "executable_review_plan"` means only that
the stored task contains a validated explicit request and a required-capacity
flag. It does not mean that server configuration, grants, activation, model
availability, provider success, or price is ready or guaranteed.

## Implemented worker

The bounded single-task bridge is now implemented in `apps/web/lib/integration-runtime.ts::executePlannedTask` and `apps/web/lib/durable-dispatch.ts::withExistingTaskDispatch`, exposed through the authenticated planned-tasks route and local CLI. See [activation and execution](planned-worker.md) for the operator workflow and its limits.
