# Constrained schedule to durable delegation plan

`apexgraphswarm.delegation_plan.compile_delegation_plan(problem,
model_bindings, *, task_inputs=None)` recomputes a constrained `schedule_dag`
result and compiles a feasible fully costed assignment. It never accepts a
caller-supplied schedule result. With no `task_inputs`, it remains a
compile-only metadata path and preserves the existing ControlStore plan shape.
With `task_inputs`, it builds the explicit execution-input contract described
in [planned-dispatch-contract.md](planned-dispatch-contract.md). Neither mode
creates a run, grants access, enrolls a worker, or calls a provider.

The `problem` object follows `schedule_dag` fields: `tasks`, `budget_microusd`,
`capacities`, and optional `model_options`, `deadline_seconds`, and
`exact_max_tasks`. Each chosen option must be resolvable through an explicit
`model_bindings` entry keyed by the schedule model ID:

```python
{
  "vendor/model-small": {
    "configured": True,
    "adapterId": "openrouter",
    "operation": "review",
    "modelId": "vendor/model-small-2026-09",
    "resourceId": "model:vendor/model-small-2026-09",
    "toolId": "integration:openrouter:review",
    "costMicrousd": 500,
    "maxParallel": 2,
  }
}
```

`configured: True` is a caller assertion; the compiler does not probe
environment state or verify that an adapter is deployed. The configured
per-task cost must exactly match the schedule estimate, and configured
parallel capacity must cover the problem's capacity. Missing mappings, unknown
costs, unconfigured adapters, mismatched tools, inadequate capacity, and
infeasible or unknown schedules fail closed. Selected schedule IDs that alias
the same resource or adapter/model endpoint are rejected to prevent one
capacity pool from being counted twice.

Compiled task reservations use the recomputed schedule costs, and task/agent
IDs are deterministic hashes. Dependencies remain explicit. Payload metadata
retains the source task ID, pinned model/adapter/resource references, selected
option duration, source task duration estimate, scheduled times, and deadline
estimate. Automatic retries are disabled because the schedule reserves one
attempt per task.

The scheduler's `algorithm`, `exact`, and `limits` remain visible. Exact
schedules are bounded by the scheduler's documented search limits; heuristic
schedules have no optimality or infeasibility guarantee. Costs, durations,
capacity declarations, and deadlines are caller-supplied estimates. The plan's
scheduled offsets and deadline estimates are metadata; live execution enforces
dependencies and resource concurrency but does not promise to follow the
predicted start/finish times. An execution-enabled durable plan is limited to
1 MB serialized size so duplicated per-task graph snapshots remain bounded.
