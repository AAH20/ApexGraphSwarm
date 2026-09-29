# Bounded optimization helpers

`apexgraphswarm.optimization` contains pure, deterministic planners. It returns candidate schedules, evidence selections, coding waves, and capacity recommendations. `apexgraphswarm.hierarchy` adds a bounded root/domain/cluster/worker plan with field-specific metric profiles. It does not call models, inspect a checkout, execute shell commands, access a provider, or query prices. Estimates and telemetry are supplied by the caller. Unknown cost stays unknown.

All APIs reject malformed/non-finite numeric values and enforce input limits. `OptimizationInputError` reports invalid or over-bound inputs. Result objects are frozen dataclasses composed of tuples and scalar values; `optimize()` converts them to JSON-compatible dictionaries.

## DAG schedule and model-option delegation

`schedule_dag(tasks, *, budget_microusd, capacities, deadline_seconds=None, model_options=())` accepts `DagTask(id, dependencies, duration_estimate, options, deadline)` records and `ModelOption(model, estimated_cost_microusd, duration_estimate, eligible=True)` choices. Per-task options take precedence. If a task has no per-task options, all global options are considered for that task. A missing/unknown price is never interpreted as zero. Capacity, budget, eligibility and any task/global deadline are hard constraints.

For small DAGs, bounded exhaustive search enumerates precedence-respecting task orders and model choices, maximizing the resulting list-schedule makespan first, then minimizing estimated cost. Search is limited to at most 8 tasks, 65,536 leaves and 200,000 estimated search nodes. Larger inputs use deterministic lowest-cost choices. A failed exact search with fully known eligible choices reports `infeasible`; a heuristic failure reports `unknown`. If an otherwise usable choice has unknown cost, failure also reports `unknown`. The global deadline and any task deadline both apply, using the earlier limit. A feasible result contains one `ScheduledTask` per input task. The returned timeline is based on caller duration estimates and identical-capacity slots per model; it is not a provider promise or a universal optimum for resource-constrained project scheduling.

```json
{
  "action": "schedule",
  "budget_microusd": 12,
  "capacities": {"local-model": 1},
  "deadline_seconds": 10,
  "tasks": [
    {"id": "inspect", "dependencies": [], "duration_estimate": 2,
     "options": [{"model": "local-model", "estimated_cost_microusd": 5, "duration_estimate": 2}]},
    {"id": "summarize", "dependencies": ["inspect"], "duration_estimate": 1,
     "options": [{"model": "local-model", "estimated_cost_microusd": 7, "duration_estimate": 1}]}
  ]
}
```

## Token-budgeted evidence coverage

`select_evidence(items, *, token_budget)` takes `EvidenceItem(id, claims, token_cost, weights)`. The objective is weighted unique claim coverage under the hard token limit; overlapping claims are counted once. A claim weight is the maximum supplied weight from any evidence that names the claim, with default weight 1. Bounded exact enumeration runs through 18 items. Larger inputs use deterministic greedy marginal-weight-per-token selection and do not claim optimality. Exact tie breaking prefers fewer tokens, then lexicographically smaller evidence IDs. If the sum of distinct claim weights or the conservative sum of per-task duration estimates is non-finite, the input is rejected before planning.

```json
{
  "action": "evidence",
  "token_budget": 8,
  "items": [
    {"id": "test-log", "claims": ["tests-pass", "exit-zero"], "token_cost": 5, "weights": {"tests-pass": 3}},
    {"id": "diff-check", "claims": ["exit-zero", "clean-diff"], "token_cost": 4, "weights": {"clean-diff": 2}}
  ]
}
```

## Conflict-aware coding waves

`plan_waves(tasks)` takes `CodeTask(id, dependencies, reads, writes)` declarations. A write conflicts with another task's read or write of the same declared path. Relative paths normalize slash direction and lexical `.`/`..` aliases before conflict checks; absolute paths and paths escaping the repository root are rejected. Conflicting unordered tasks are serialized deterministically by task ID. Tasks in each wave therefore have no dependency or declared file conflict. The planner does not inspect actual files, resolve symlinks, infer undeclared accesses, execute coding agents, or perform Git operations. Missing dependencies and cycles (including cycles introduced by conflict serialization) are rejected.

```json
{
  "action": "waves",
  "tasks": [
    {"id": "edit-api", "dependencies": [], "reads": ["src/api.py"], "writes": ["src/api.py"]},
    {"id": "edit-docs", "dependencies": [], "reads": [], "writes": ["docs/api.md"]},
    {"id": "review", "dependencies": ["edit-api", "edit-docs"], "reads": ["src/api.py", "docs/api.md"], "writes": []}
  ]
}
```

## Telemetry-based capacity suggestion

`recommend_capacity(samples, *, target_utilization=0.75)` takes `TelemetrySample(concurrency, throughput, latency_seconds, utilization, queue_depth)` observations. It selects the highest observed throughput at or below the utilization target, breaking ties by latency and concurrency. If no sample is below the target, it selects the least utilized measured point. Empty observations return `insufficient_data`. `queue_depth` is validated and retained as part of the supplied sample shape, but this version does not use it in the selection rule. This is a heuristic over supplied measurements, does not extrapolate beyond the measured concurrency, and does not represent live vLLM/provider status, model prices, or a guaranteed safe capacity.

```json
{
  "action": "capacity",
  "target_utilization": 0.75,
  "samples": [
    {"concurrency": 1, "throughput": 8.0, "latency_seconds": 0.12, "utilization": 0.5, "queue_depth": 0},
    {"concurrency": 2, "throughput": 13.0, "latency_seconds": 0.2, "utilization": 0.7, "queue_depth": 1},
    {"concurrency": 4, "throughput": 20.0, "latency_seconds": 0.5, "utilization": 0.92, "queue_depth": 6}
  ]
}
```

## JSON dispatcher

`optimize(payload)` accepts exactly one of `schedule`, `evidence`, `waves`, or `capacity` in the `action` field and rejects unknown top-level fields. It returns `dataclasses.asdict()`-shaped data. Task/options/sample/evidence fields use the names shown above. Bounds are 500 tasks/evidence items, 2,000 total explicit/global model options, 2,000 distinct claims, 500 declared paths per coding task, and 10,000 telemetry samples. Exact thresholds and limits are exposed through result metadata.

The authenticated local `apexgraphswarm.lab` dispatcher also exposes `action: "hierarchy"`. Its exact bounded schema, versioned metric profiles, clustering behavior, hard gates, evaluation integration, benchmark boundaries, and economics are documented in [hierarchical orchestration](hierarchical-orchestration.md). It returns a plan only and independently requires live grant checks before any separate execution action.
