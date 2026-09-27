# Verifiable optimization program

The objective is lower cost per independently accepted outcome under hard quality, authorization, budget and latency constraints. More agents and higher throughput are useful only when these conditions hold.

## Delegated work and dependency order

| Priority | Deliverable | Assigned workstream | Acceptance evidence |
| --- | --- | --- | --- |
| P0 | Execution attempts and attributed cost receipts | execution_foundation (GPT-6 Luna, high) | Idempotent transactions, failures/retries charged, unknown liability retained |
| P0 | Exact specialist capability enforcement | execution_foundation | Missing, expired or revoked grants deny external leases; cumulative budget enforced |
| P1 | DAG scheduling and model-option delegation | optimization_engine (GPT-6 Luna, high) | Feasible plan validation, bounded oracle, hard budget/capacity/dependencies |
| P1 | Budgeted evidence selection | optimization_engine | Greedy baseline versus exact small instances; explicit token and search limits |
| P1 | Conflict-aware coding swarm plans | optimization_engine | Read/write conflicts separated into dependency-respecting waves |
| P1 | Reproducible evaluation and promotion gates | analysis_verification (GPT-6 Luna, high) | Disjoint splits, paired tasks, all-attempt cost, quality/policy/SLO gates |
| P2 | Verified configuration evolution | analysis_verification | Training selection followed by held-out gate; sealed tasks excluded from selection |
| P2 | Inference capacity recommendations | optimization_engine | Supplied telemetry, explicit assumptions, no invented live GPU measurements |
| Cross-cutting | Optimization workbench and integration review | root | Browser → authenticated API → bounded Python experiment → inspectable output |

## Delivery boundaries

Initial implementations are bounded local foundations. Coding waves describe a plan; they do not open worktrees or merge changes. Inference recommendations consume supplied telemetry, with an optional configured read-only vLLM collector; they do not operate a GPU cluster. Opaque enrolled credentials now bind worker identity to leases and external adapter dispatch. Local administrator enrollment is trusted; this does not sandbox arbitrary tools or establish a multi-tenant identity service. Evolution selects supplied configurations; it does not run untrusted generated code or automatically deploy winners.

The local Optimization Lab requires the existing private workspace execution token. Tokens remain in memory. JSON payloads are bounded to 128 KiB, Python subprocesses have a 15-second deadline, and each web process accepts at most two concurrent experiments. These are local safety bounds, not a distributed admission controller.

## Implemented foundation checkpoint

All three delegated workstreams completed the bounded local implementation and independent cross-review. Root integrated the browser workbench and attempt-ledger display. Validation recorded 70 Python and 104 web tests passing, typecheck/build, desktop/mobile browser checks and a five-case synthetic benchmark artifact. See [verification](verification.md). This checkpoint completes the local foundation, while the overall optimization program remains active through the production milestones below.

## Authenticated adapter and telemetry checkpoint

External adapter dispatch now uses enrolled opaque worker credentials, exact grants and pre-invocation renewal checks. OpenRouter receipt metadata can settle integer microUSD costs while retaining the exact decimal source; missing costs and ambiguous effects retain liability. Bounded checkpoints preserve partial outputs. Receipt reconciliation checks exact saved-call coverage atomically and only settles previously unknown attempt costs. The credential-scoped SQLite request registry suppresses uncertain redispatch after restart. A configured read-only vLLM collector reports counter deltas, queue/cache observations and histogram bounds without starting inference. These improvements do not provide a distributed identity service, invoice reconciliation, provider-enforced spending limits or automatic capacity control.

## Subsequent production milestones

1. Extend the enrolled-worker dispatch path to externally issued IAM/PAM identities, distributed workers and explicit recovery of registered requests across processes without trusting browser declarations.
2. Reconcile OpenRouter/provider receipts and measured vLLM compute allocations with the ledger. Preserve separate estimated, reserved, invoiced and unresolved costs; include human review and indexing in outcome economics.
3. Connect repository file ownership and actual patch read/write sets to isolated worktrees, integration queues and conflict-aware re-planning.
4. Import pinned PSPLIB, GraphRAG-Bench, ToolSandbox/τ-bench, MultiAgentBench and Terminal-Bench cases in isolated runners. Record licenses, dataset hashes, evaluator versions and per-run budgets. Fixture results are never substitutes for these external benchmarks.
5. Add canary execution and rollback after held-out promotion, drift monitoring, quota-aware provider dispatch and closed-loop decisions over the read-only inference telemetry. Validate scale before raising concurrency limits.

## Evaluation contract

Freeze task identities, dataset/split versions, seeds, tool versions and budgets. Compare matched workloads and quality. Charge failed attempts, retries, retrieval, optimization, infrastructure and review. Unknown cost blocks favorable cost claims. Report logical population and active workers separately. A heuristic returning no solution is not proof of infeasibility; a bounded oracle is exact only inside its documented domain.

Track success and independent acceptance, cost per accepted outcome, p50/p95 latency, deadline misses, permission violations, unresolved cost, solver overhead, feasible-plan rate and optimality gap only when a valid bound is available. Initial parameter ranges are experiment settings, not performance guarantees.

## Algorithm execution and delegation compilation checkpoint

The local workbench now executes a bounded greedy configuration search against exact weighted-coverage oracles, with training-only selection, held-out checks and unscored sealed fixtures. Actual monetary costs remain unknown and block promotion. The delegation compiler recomputes constrained schedules and exports ControlStore-compatible plans with deterministic IDs, exact mappings and reservations. Adapter readiness is caller-asserted; automatic planned-worker dispatch remains a separate milestone. See [evolution](algorithm-evolution.md) and [delegation compilation](delegation-plan.md).

## Capacity-enforced planned task execution checkpoint

Executable review plans now persist explicit graph/goal inputs and require administrator-configured resource capacity. The exact-task worker rechecks server policy and atomically claims the stored task without creating another run. Global and per-run capacities apply across database connections; ambiguous remote effects retain slots. Swarm Control provides an explicit execution action, while the graph explains persisted slot availability. Scheduled offsets and estimated deadlines remain advisory. See [worker activation](planned-worker.md), [resource limits](resource-capacity.md) and [executable input contract](planned-dispatch-contract.md).
