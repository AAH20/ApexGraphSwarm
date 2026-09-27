# Execution explanation graph

`apexgraphswarm.execution_graph` projects one persisted `ControlStore.status(run_id)`
mapping and its ledger into a deterministic, bounded graph. It is a read-only view for
explaining orchestration and accounting relationships; it does not execute work or
modify the control store.

## Python API

```python
from apexgraphswarm.control import ControlStore
from apexgraphswarm.execution_graph import project_execution_graph

with ControlStore(".runtime/control.sqlite") as store:
    status = store.status("run-id")
    graph = project_execution_graph(status, max_nodes=500, max_edges=1000)
```

The optional `ledger` mapping overrides `status["ledger"]`. Inputs must be mappings
and bounded lists/tuples. `max_nodes` is 1–5000 and `max_edges` is 0–10000. The
deterministic output has this shape:

```json
{
  "version": 1,
  "runId": "run-id",
  "nodes": [
    {"id":"task:task-id","kind":"task","label":"compile","status":"pending",
     "reservedMicrousd":1200,"actualMicrousd":0,
     "details":{"executionClass":"fixture","attempts":0,"maxAttempts":1},
     "explanations":[]}
  ],
  "edges": [
    {"id":"edge:1","source":"task:task-id","target":"task:dependency-id",
     "kind":"dependency","label":"depends on"}
  ],
  "summary": {
    "nodeCount":1,"edgeCount":0,"omittedNodes":0,"omittedEdges":0,
    "omittedAttempts":0,
    "attemptCoverage":{"expected":0,"recorded":0,"returned":0,"missing":0,"complete":true},
    "allCostsResolved":true,"knownActualMicrousd":0,
    "knownActualIsPartial":false,"unknownCostAttempts":0
  },
  "limitations":["..."],
  "truncated":false
}
```

Node kinds are `run`, `task`, `attempt`, `agent`, `worker`, `principal`, `grant`,
and `resource`. Edges describe run containment, declared task dependencies and agent
assignment, persisted attempt ownership, execution worker, principal attribution,
grant authorization, and tool/resource use. Node IDs are namespaced with the source
identifier. Logical agents in the submitted plan are distinct from authenticated
execution workers, since one worker can service multiple logical roles. Attempts are
created only from ledger rows that exist; a task's attempt
counter is used to report missing receipt coverage, never to invent attempt nodes.

Task costs come from persisted attempt receipts. A task with no attempts has known
zero actual cost; a task with unresolved or missing attempt receipts has `null`
actual cost. Attempt reservations and actual costs are integer micro-USD. The graph
does not replace the ledger: the summary's known actual total comes from records
available in the supplied ledger view, and coverage metadata must be considered when
the ledger reports truncation or missing history.

The projection applies an allowlist. It omits task payloads, result bodies, detailed
errors, receipt bodies, checkpoint data, and lease tokens. `details` contains only
small state and attribution fields. IDs and labels remain identifiers/metadata from
the control store; applications should still apply their normal authorization before
serving a run's graph.

Nodes are selected deterministically: run, tasks, declared agents, persisted attempts,
then execution attribution and resource identities. Edges with a missing/truncated
endpoint are dropped. `summary.omittedNodes`, `summary.omittedEdges`, and
`truncated` make this loss explicit. The projection is not a claim of a full graph
when the source ledger itself is truncated. `attemptCoverage.recorded` reflects the
ledger's total row count; `attemptCoverage.returned` is the number of rows included
in its bounded page. `omittedAttempts` reports rows left out by that page. These are
not labeled as missing history or unknown cost. Truly absent receipts are computed
from task attempt counters versus the ledger's total count; unresolved liabilities
come from the ledger's full aggregate. If the ledger does not provide these
aggregate fields, `knownActualIsPartial` signals that the known total was computed
from returned rows.

## Read-only CLI

The module CLI accepts an existing database path and run ID. It opens SQLite with
`mode=ro`, starts a read transaction, and bypasses `ControlStore.__init__` so schema
initialization/migration cannot write to the database.

```sh
python3 -m apexgraphswarm.execution_graph .runtime/control.sqlite RUN_ID
python3 -m apexgraphswarm.execution_graph .runtime/control.sqlite RUN_ID --max-nodes 200 --max-edges 400
printf '{"dbPath":".runtime/control.sqlite","runId":"RUN_ID"}' | python3 -m apexgraphswarm.execution_graph
```

The stdin form accepts exactly the server-side `dbPath` and `runId` fields, bounded
to 16 KiB. Successful stdout is one compact JSON graph. Errors are compact JSON with a generic
message; database paths and exception text are not echoed. The CLI is intended for a
trusted server-side caller that has already authorized the requested run ID. Never
accept a database path from an untrusted browser request.

This module uses only the Python standard library. It provides a persisted-state
explanation view, not a live stream, causal proof, or replacement for access-control
checks, event history, or financial reconciliation.

The browser rejects numeric values outside JavaScript's safe-integer range with an explicit precision error. Use the Python CLI for exact larger integer aggregates; the UI never rounds these costs silently. Read-only graph requests do not create a database or its parent directory.
