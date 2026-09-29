# Hierarchical swarm planning, field profiles, and economics

This document specifies the versioned, deterministic hierarchy planner exposed through the Optimization Lab. `action: hierarchy` returns a **plan only**. It does not call a model, run a tool, mint a credential, reserve a provider budget, or dispatch an agent. The execution boundary must independently verify every grant, scope, data boundary, budget, capacity, and current policy.

The first implementation caps one plan at 200 tasks and 200 candidate agents, 100 clusters, 50 tasks per cluster, and 15 seconds in the local experiment process. Its dependency-aware partitioner is deterministic and heuristic; it does not claim a globally optimal graph cut or schedule.

## Control-plane architecture

~~~mermaid
flowchart TD
    Request[Request plus graph and evidence snapshot] --> Normalize[Normalize objective, tasks, and evidence]
    Normalize --> Classify[Classify domain, task family, risk, SLA, and budget]
    Classify --> Admission{Hard admission constraints}
    Admission -->|Blocked| Explain[Explain blocker or request clarification]
    Admission -->|Eligible| DAG[Build dependency and resource DAG]
    DAG --> Partition[Partition by affinity, dependency, and data boundary]
    Partition --> Root[Root orchestrator]
    Root --> Domain[Field or domain coordinator]
    Domain --> LeadA[Cluster leader A]
    Domain --> LeadB[Cluster leader B]
    LeadA --> WorkerA[Specialist worker]
    LeadA --> WorkerB[Specialist worker]
    LeadB --> WorkerC[Specialist worker]
    WorkerA --> Validate[Independent evaluation and policy checks]
    WorkerB --> Validate
    WorkerC --> Validate
    Validate --> Decision{Accepted within all gates}
    Decision -->|No budget remains or policy failure| Escalate[Stop, label partial, or escalate to a human]
    Decision -->|Bounded retry allowed| Repair[Repair or reassign with a new attempt record]
    Repair --> LeadA
    Decision -->|Yes| Aggregate[Aggregate with evidence, confidence, and provenance]
    Aggregate --> Ledger[Append attempts, usage, cost, and outcome]
    Escalate --> Ledger
    IAM[Identity and policy service] -. exact action, scope, audience, expiry .-> Admission
    IAM -. recheck grant before dispatch .-> LeadA
    Budget[Budget, concurrency, and deadline controller] -. admission and runtime limits .-> Root
    Budget -. stop dispatch on cap .-> LeadB
~~~

The hierarchy has a root, a domain coordinator, cluster leaders, and workers. Depth and fan-out are configuration limits, not targets to maximize. Leaders coordinate, decompose, and summarize; they cannot grant themselves new permissions. Persist a versioned delegation record containing parent and task IDs, cluster, leader and worker IDs, dependencies, capability and action IDs, exact resource scope, data boundary, grant reference, evaluator profile, deadline, attempt limit, and per-task/run budgets.

## Classification and clustering

Classification uses declared objective/domain, task kind, dependency graph, required capabilities and actions, resource scope, data boundary, context size, error impact, evidence requirements, deadline, and budget. Missing or contradictory inputs yield a blocked plan, not silent guessing.

Clusters group tasks with a compatible family and data boundary. The planner places dependency-related work together when the cluster cap allows it, then reports dependencies that cross cluster boundaries. It never merges distinct data boundaries. An execution implementation should add observed file/resource conflicts and current capacity before dispatch.

~~~mermaid
flowchart LR
    Input[Declared workload] --> Features[Domain, DAG, capabilities, actions, scope, boundary, cost]
    Features --> Profile[Versioned metric profile and weight set]
    Profile --> Candidates[Leader and worker candidates]
    Candidates --> ScopeCheck{Profile, action, scope, boundary, and capacity match}
    ScopeCheck -->|No| Block[Record an explicit unassigned-task blocker]
    ScopeCheck -->|Yes| Cluster[Deterministic affinity and dependency clustering]
    Cluster --> Rank[Rank eligible agents using complete profile evidence]
    Rank --> Resource[Check budget, critical-path estimate, and cluster bounds]
    Resource --> Plan[Export versioned plan with grant references]
    Plan --> Recheck[Revalidate live grants and resource state at dispatch]
~~~

The plan reports `estimatedCriticalPathMs`, a caller-estimate calculation over the dependency DAG. It does not model queueing, leader overhead, tool variance, or model latency distributions. Its task-cost subtotal is not all-in unless the caller allocates coordination, infrastructure, evaluation, and review costs into those estimates. Avoid counting the same shared cost both in task estimates and again in the run ledger. If any task has neither an explicit estimated cost nor a selected worker's per-task rate estimate, total estimated spend is unknown and the plan is blocked. The accepted-outcome denominator and actual cost-per-accepted-outcome remain null until evaluation and usage receipts exist.

## Field-specific metric profiles

Built-in profile version 1 has the following initial weights. They are transparent defaults for evaluation design, not empirically optimal weights. Each profile uses normalized scores in [0, 1].

| Field profile | Exact metric weights |
|---|---|
| Coding | correctness 30; test_coverage 20; regression_control 15; evidence_provenance 10; reliability 10; latency 5; cost_efficiency 5; coordination_efficiency 5 |
| Research | task_utility 20; evidence_fidelity 25; citation_accuracy 20; completeness 10; uncertainty_calibration 10; reproducibility 5; latency 5; cost_efficiency 5 |
| Analytics / BI | numeric_correctness 25; data_lineage 20; statistical_validity 15; reproducibility 15; interpretability 10; uncertainty 5; latency 5; cost_efficiency 5 |
| Operations | remediation_quality 25; time_to_restore 20; diagnostic_evidence 20; reliability 15; blast_radius_control 10; cost_efficiency 5; communication 5 |
| Physical simulation | simulation_success 20; constraint_satisfaction 20; robustness 15; latency 15; observability 15; recoverability 10; cost_efficiency 5 |

Every row sums to exactly 100. A custom weight set must include every metric ID exactly once, use integer percentages summing to exactly 100, and supply `metricWeightVersion`. Missing metric values are never renormalized away. The result includes every weighted contribution. `EvaluationSuite.metricProfile` can attach the same profile and a custom, versioned weight set to each evaluator attempt. Weighted quality is averaged over the final attempt per task and receives a conservative interval. Promotion requires the existing quality/cost/policy/SLO gates and the field-profile floor; the candidate's paired held-out profile-score difference must meet its non-inferiority margin.

Hard gates remain separate from the composite: exact authorization and scope, privacy boundary, enforced cost cap, deadline/resource limits, required evidence, and independent acceptance. A composite score cannot offset a failed gate. Keep the evaluation profile separate from the target-audience display: an investor view may foreground cost and risk evidence without changing the engineering evaluator's weights.

## Evolution and promotion

Evolve bounded planner configuration such as cluster size, maximum depth, leader span, split threshold, bounded redundancy, retry policy, and aggregation rule. Do not evolve permissions or policy thresholds from model feedback.

~~~mermaid
flowchart TD
    Registry[Versioned tasks, evaluator, profile, weights, and cost rules] --> Split[Disjoint train, held-out, and sealed task IDs]
    Split --> Baseline[Single-agent and flat-swarm baselines]
    Split --> Search[Bounded hierarchy and clustering search]
    Baseline --> Run[Matched task, model, tool, and budget evaluation]
    Search --> Run
    Run --> Select[Select only on training evidence]
    Select --> Freeze[Freeze config hash, weight version, seeds, and budget]
    Freeze --> Held[Paired held-out comparison]
    Held --> Gates{Quality, profile, policy, reliability, latency, and cost gates}
    Gates -->|Fail or uncertain| Reject[Withhold promotion and show intervals]
    Gates -->|Pass| Review[Human review and bounded canary]
    Review --> Canary{Canary stays within gates}
    Canary -->|No| Rollback[Rollback to previous plan version]
    Canary -->|Yes| Promote[Promote version with provenance]
    Promote --> Monitor[Drift, cost, quality, and policy monitoring]
    Monitor --> Registry
    Promote --> Sealed[Separate post-selection sealed audit]
~~~

The existing evaluator charges all attempts, including failures and retries, and keeps sealed tasks out of selection. A profile adds weighted quality and profile-specific non-inferiority; it does not replace paired acceptance, unknown-cost, cost-cap, latency, or policy gates. Small samples should remain inconclusive. Every report should include confidence intervals, split identity, evaluator version, candidate config hash, metric profile, and weight-set version.

## Benchmarks and operating economics

The local synthetic benchmark includes planner construction at 4, 32, 128, and 200 tasks. The checked-in run took approximately 0.15 ms, 0.29 ms, 0.99 ms, and 3.25 ms respectively on its recorded local environment; the 200-task fixture was correctly blocked because the single synthetic leader's cluster capacity was exhausted. These timings measure local deterministic planning only: they do not measure model quality, active agents, tool execution, or production throughput. Treat logical population and concurrently active workers as separate benchmark axes. A 150K logical-agent simulation is not evidence of 150K simultaneous inference sessions.

For a meaningful scale evaluation, compare single-agent, flat-swarm, hierarchy without clustering, clustering without adaptive leaders, and the full candidate on matched task families and equivalent budgets. Record accepted outcomes, quality vectors, p50/p95 end-to-end and queue latency, throughput, duplicate work, handoffs, leader saturation, cluster imbalance, dependency cut, conflicts, retries, cancellations, permission violations, unknown cost, and recovery behavior. Publish dataset hashes, evaluator/model/tool versions, seeds, concurrency, hardware, and confidence intervals. Never compare a synthetic planning microbenchmark to a vendor's live-agent result.

Account for inference (input, cache reads/writes, output), tools, GPU/CPU time, storage and egress, orchestration, evaluation, human review, failed attempts, and retries. Keep estimate, reservation, actual usage, and invoice as distinct ledger values:

~~~text
run_cost = inference + tools + compute + storage_network + orchestration
           + evaluation + human_review + retries
cost_per_accepted_outcome = all_run_cost / independently_accepted_outcomes
incremental_value = value_of_incremental_accepted_outcomes - incremental_run_cost
~~~

If actual cost or accepted outcomes are missing, cost per accepted outcome is unknown. Subscription allocation and local vLLM GPU cost require declared, auditable allocation rules; neither should be represented as free compute.

## Plan request

The Optimization Lab's **Hierarchical swarm plan** example sends this shape to the authenticated local optimization endpoint:

~~~json
{
  "action": "hierarchy",
  "profileId": "coding",
  "limits": {"budgetMicrousd": 50000, "deadlineMs": 5000, "maxClusterTasks": 8, "maxClusters": 32},
  "tasks": [{
    "id": "review-source", "family": "repository-review", "dependencies": [],
    "requiredCapabilities": ["repository_read"], "requiredActions": ["read"],
    "resourceScope": "repo:example", "dataBoundary": "public-repo",
    "estimatedCostMicrousd": 12000, "estimatedLatencyMs": 1000
  }],
  "agents": [{
    "id": "review-worker", "role": "worker", "profileIds": ["coding"],
    "capabilities": ["repository_read"], "authorizedActions": ["read"],
    "authorizationGrantId": "operator-grant-reference",
    "resourceScopes": ["repo:example"], "dataBoundaries": ["public-repo"],
    "maxAssignments": 1,
    "metricScores": {
      "correctness": 0.9, "test_coverage": 0.9, "regression_control": 0.9,
      "evidence_provenance": 0.9, "reliability": 0.9, "latency": 0.8,
      "cost_efficiency": 0.8, "coordination_efficiency": 0.8
    }
  }]
}
~~~

Scores, grant references, capability declarations, costs, and latencies are input assertions, not verified facts. Live execution must resolve grants at the resource boundary and record actual receipts. The planner is not an IAM system, sandbox, distributed queue, autoscaler, or production benchmark.
