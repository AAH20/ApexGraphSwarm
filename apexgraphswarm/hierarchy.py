"""Deterministic, plan-only hierarchical swarm assignment and field profiles.

This module never executes agents. Provider, evaluator, scope, cost and capability
records are caller supplied and must be independently enforced at dispatch.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import math
import re
from typing import Any, Mapping, Sequence


class HierarchyError(ValueError):
    """Invalid hierarchy plan input."""


# Integer percentages are deliberate: serialized weights sum to exactly 100.
METRIC_PROFILES: dict[str, dict[str, Any]] = {
    "coding": {"label": "Coding and software engineering", "version": "1", "weights": {
        "correctness": 30, "test_coverage": 20, "regression_control": 15,
        "evidence_provenance": 10, "reliability": 10, "latency": 5,
        "cost_efficiency": 5, "coordination_efficiency": 5}},
    "research": {"label": "Research and knowledge work", "version": "1", "weights": {
        "task_utility": 20, "evidence_fidelity": 25, "citation_accuracy": 20,
        "completeness": 10, "uncertainty_calibration": 10, "reproducibility": 5,
        "latency": 5, "cost_efficiency": 5}},
    "analytics": {"label": "Data science and business intelligence", "version": "1", "weights": {
        "numeric_correctness": 25, "data_lineage": 20, "statistical_validity": 15,
        "reproducibility": 15, "interpretability": 10, "uncertainty": 5,
        "latency": 5, "cost_efficiency": 5}},
    "operations": {"label": "Operations and incident support", "version": "1", "weights": {
        "remediation_quality": 25, "time_to_restore": 20, "diagnostic_evidence": 20,
        "reliability": 15, "blast_radius_control": 10, "cost_efficiency": 5,
        "communication": 5}},
    "physical_simulation": {"label": "Physical AI simulation and advisory", "version": "1", "weights": {
        "simulation_success": 20, "constraint_satisfaction": 20, "robustness": 15,
        "latency": 15, "observability": 15, "recoverability": 10,
        "cost_efficiency": 5}},
}
HARD_GATES = (
    "authorization_and_scope", "privacy_and_data_boundary", "run_and_task_budget",
    "deadline_and_resource_capacity", "required_evidence", "independent_acceptance",
)
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}$")


def _text(value: object, name: str, *, maximum: int = 256) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or "\x00" in value:
        raise HierarchyError(f"{name} must be non-empty text of at most {maximum} characters")
    return value.strip()


def _id(value: object, name: str) -> str:
    result = _text(value, name, maximum=128)
    if not _ID.fullmatch(result):
        raise HierarchyError(f"{name} contains unsupported characters")
    return result


def _number(value: object, name: str, *, low: float = 0.0, high: float = 1.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise HierarchyError(f"{name} must be finite and between {low} and {high}")
    return float(value)


def _integer(value: object, name: str, *, low: int = 0, high: int = 2**63 - 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise HierarchyError(f"{name} must be an integer between {low} and {high}")
    return value


def _string_list(value: object, name: str, *, maximum: int = 200) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or len(value) > maximum:
        raise HierarchyError(f"{name} must be a list with at most {maximum} values")
    values = tuple(_id(item, name) for item in value)
    if len(set(values)) != len(values):
        raise HierarchyError(f"{name} values must be unique")
    return values


def get_metric_profile(profile_id: str) -> dict[str, Any]:
    """Return a copy of one versioned profile and its non-compensating gates."""
    if profile_id not in METRIC_PROFILES:
        raise HierarchyError("profileId must be one of: " + ", ".join(sorted(METRIC_PROFILES)))
    profile = METRIC_PROFILES[profile_id]
    return {"profileId": profile_id, "profileVersion": profile["version"],
            "label": profile["label"], "weights": dict(profile["weights"]),
            "hardGates": list(HARD_GATES), "scoreRange": [0, 1],
            "weightTotal": sum(profile["weights"].values())}


def normalize_metric_weights(profile_id: str, raw: Mapping[str, object] | None = None) -> dict[str, int]:
    """Validate an optional field-specific weight override; never fill missing weights."""
    if profile_id not in METRIC_PROFILES:
        raise HierarchyError("profileId must be one of: " + ", ".join(sorted(METRIC_PROFILES)))
    if raw is None:
        return dict(METRIC_PROFILES[profile_id]["weights"])
    expected = set(METRIC_PROFILES[profile_id]["weights"])
    if not isinstance(raw, Mapping) or set(raw) != expected:
        raise HierarchyError("metricWeights must include every registered field metric exactly once")
    weights = {}
    for name, value in raw.items():
        weights[name] = _integer(value, "metricWeights." + name, high=100)
    if sum(weights.values()) != 100:
        raise HierarchyError("metricWeights must sum to exactly 100")
    return weights


def weighted_score(profile_id: str, scores: Mapping[str, object], *,
                   weights: Mapping[str, object] | None = None,
                   weight_version: str | None = None) -> dict[str, Any]:
    """Score a complete field metric vector; never renormalize around missing metrics."""
    profile = get_metric_profile(profile_id)
    if not isinstance(scores, Mapping):
        raise HierarchyError("metricScores must be an object")
    clean_weights = normalize_metric_weights(profile_id, weights)
    if weights is not None and clean_weights != profile["weights"] and not weight_version:
        raise HierarchyError("a custom metricWeights set requires metricWeightVersion")
    if weight_version is not None:
        weight_version = _text(weight_version, "metricWeightVersion", maximum=64)
    extra = set(scores) - set(clean_weights)
    if extra:
        raise HierarchyError("metricScores contains unknown metrics: " + ", ".join(sorted(extra)))
    clean: dict[str, float] = {}
    for metric in clean_weights:
        if metric not in scores:
            continue
        clean[metric] = _number(scores[metric], f"metricScores.{metric}")
    missing = [metric for metric in clean_weights if metric not in clean]
    components = {metric: {"score": clean[metric], "weightPercent": weight,
                           "weightedContribution": clean[metric] * weight / 100}
                  for metric, weight in clean_weights.items() if metric in clean}
    return {"profileId": profile_id, "profileVersion": profile["profileVersion"],
            "metricWeightVersion": weight_version or "builtin-" + profile["profileVersion"],
            "weights": clean_weights,
            "score": None if missing else round(sum(item["weightedContribution"] for item in components.values()), 8),
            "complete": not missing, "missingMetrics": missing, "components": components,
            "hardGates": list(HARD_GATES),
            "note": "A weighted score cannot override a failed hard gate."}


@dataclass(frozen=True)
class _Task:
    id: str
    family: str
    dependencies: tuple[str, ...]
    capabilities: tuple[str, ...]
    actions: tuple[str, ...]
    scope: str
    boundary: str
    estimated_cost: int | None
    latency_ms: float


@dataclass(frozen=True)
class _Agent:
    id: str
    role: str
    profile_ids: tuple[str, ...]
    capabilities: tuple[str, ...]
    actions: tuple[str, ...]
    grant_id: str
    scopes: tuple[str, ...]
    boundaries: tuple[str, ...]
    capacity: int
    cluster_capacity: int
    metrics: Mapping[str, object]
    unit_cost: int | None
    weighted: Mapping[str, Any]


def _topological(tasks: Sequence[_Task]) -> tuple[_Task, ...]:
    by_id = {task.id: task for task in tasks}
    if len(by_id) != len(tasks):
        raise HierarchyError("task IDs must be unique")
    for task in tasks:
        missing = set(task.dependencies) - by_id.keys()
        if missing or task.id in task.dependencies:
            raise HierarchyError(f"task {task.id} has missing or self-referential dependencies")
    indegree = {task.id: len(task.dependencies) for task in tasks}
    children: dict[str, list[str]] = defaultdict(list)
    for task in tasks:
        for dep in task.dependencies:
            children[dep].append(task.id)
    ready = sorted(key for key, degree in indegree.items() if degree == 0)
    ordered: list[_Task] = []
    while ready:
        current = ready.pop(0)
        ordered.append(by_id[current])
        for child in sorted(children[current]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
                ready.sort()
    if len(ordered) != len(tasks):
        raise HierarchyError("task dependency graph contains a cycle")
    return tuple(ordered)


def _parse_task(raw: object) -> _Task:
    if not isinstance(raw, Mapping):
        raise HierarchyError("each task must be an object")
    allowed = {"id", "family", "dependencies", "requiredCapabilities", "requiredActions", "resourceScope",
               "dataBoundary", "estimatedCostMicrousd", "estimatedLatencyMs"}
    if set(raw) - allowed or not {"id", "resourceScope", "dataBoundary"} <= set(raw):
        raise HierarchyError("task has unknown fields or is missing id, resourceScope, or dataBoundary")
    cost = raw.get("estimatedCostMicrousd")
    if cost is not None:
        cost = _integer(cost, "estimatedCostMicrousd")
    return _Task(_id(raw["id"], "task.id"), _id(raw.get("family", "general"), "task.family"),
                 _string_list(raw.get("dependencies", []), "task.dependencies"),
                 _string_list(raw.get("requiredCapabilities", []), "task.requiredCapabilities"),
                 _string_list(raw.get("requiredActions", []), "task.requiredActions"),
                 _id(raw["resourceScope"], "task.resourceScope"),
                 _id(raw["dataBoundary"], "task.dataBoundary"), cost,
                 _number(raw.get("estimatedLatencyMs", 0), "task.estimatedLatencyMs", high=1e9))


def _parse_agent(raw: object, profile_id: str, weights: Mapping[str, int], weight_version: str | None) -> _Agent:
    if not isinstance(raw, Mapping):
        raise HierarchyError("each agent must be an object")
    allowed = {"id", "role", "profileIds", "capabilities", "resourceScopes", "dataBoundaries",
               "authorizedActions", "authorizationGrantId", "maxAssignments", "metricScores",
               "maxClustersLed", "estimatedCostMicrousdPerTask"}
    if set(raw) - allowed or not {"id", "role", "profileIds", "capabilities", "resourceScopes",
                                   "dataBoundaries", "authorizedActions", "authorizationGrantId",
                                   "metricScores"} <= set(raw):
        raise HierarchyError("agent has unknown fields or is missing required fields")
    role = raw["role"]
    if role not in ("leader", "worker", "leader_worker"):
        raise HierarchyError("agent.role must be leader, worker, or leader_worker")
    profile_ids = _string_list(raw["profileIds"], "agent.profileIds", maximum=10)
    metrics = raw["metricScores"]
    if not isinstance(metrics, Mapping):
        raise HierarchyError("agent.metricScores must be an object")
    scored = weighted_score(profile_id, metrics, weights=weights,
                            weight_version=weight_version)
    if not scored["complete"]:
        raise HierarchyError(f"agent {raw['id']} is missing profile metrics: {', '.join(scored['missingMetrics'])}")
    cost = raw.get("estimatedCostMicrousdPerTask")
    if cost is not None:
        cost = _integer(cost, "agent.estimatedCostMicrousdPerTask")
    return _Agent(_id(raw["id"], "agent.id"), role, profile_ids,
                  _string_list(raw["capabilities"], "agent.capabilities"),
                  _string_list(raw["authorizedActions"], "agent.authorizedActions"),
                  _id(raw["authorizationGrantId"], "agent.authorizationGrantId"),
                  _string_list(raw["resourceScopes"], "agent.resourceScopes"),
                  _string_list(raw["dataBoundaries"], "agent.dataBoundaries"),
                  _integer(raw.get("maxAssignments", 1), "agent.maxAssignments", low=1, high=500),
                  _integer(raw.get("maxClustersLed", 8), "agent.maxClustersLed", low=1, high=100),
                  dict(metrics), cost, scored)


def _covers(agent: _Agent, task: _Task, profile_id: str) -> bool:
    return (profile_id in agent.profile_ids and task.scope in agent.scopes and task.boundary in agent.boundaries
            and set(task.capabilities) <= set(agent.capabilities)
            and set(task.actions) <= set(agent.actions))


def plan_hierarchy(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Produce a bounded root/domain/cluster/worker plan without dispatching it."""
    allowed = {"profileId", "metricWeights", "metricWeightVersion", "tasks", "agents", "limits"}
    if not isinstance(payload, Mapping) or set(payload) - allowed or not {"profileId", "tasks", "agents", "limits"} <= set(payload):
        raise HierarchyError("hierarchy input requires profileId, tasks, agents, and limits only")
    profile_id = _text(payload["profileId"], "profileId", maximum=64)
    raw_weights = payload.get("metricWeights")
    weight_version = payload.get("metricWeightVersion")
    if raw_weights is not None and weight_version is None:
        raise HierarchyError("custom metricWeights requires metricWeightVersion")
    if raw_weights is None and weight_version is not None:
        raise HierarchyError("metricWeightVersion requires custom metricWeights")
    weights = normalize_metric_weights(profile_id, raw_weights)
    if raw_weights is not None:
        weight_version = _text(weight_version, "metricWeightVersion", maximum=64)
    else:
        weight_version = "builtin-1"
    profile = get_metric_profile(profile_id)
    profile["weights"] = weights
    profile["weightSetVersion"] = weight_version
    raw_tasks, raw_agents, limits = payload["tasks"], payload["agents"], payload["limits"]
    if not isinstance(raw_tasks, list) or not 1 <= len(raw_tasks) <= 200:
        raise HierarchyError("tasks must contain 1 to 200 records")
    if not isinstance(raw_agents, list) or not 1 <= len(raw_agents) <= 200:
        raise HierarchyError("agents must contain 1 to 200 records")
    if not isinstance(limits, Mapping) or set(limits) - {"budgetMicrousd", "deadlineMs", "maxClusterTasks", "maxClusters"} or "budgetMicrousd" not in limits:
        raise HierarchyError("limits requires budgetMicrousd and accepts deadlineMs, maxClusterTasks, maxClusters")
    budget = _integer(limits["budgetMicrousd"], "limits.budgetMicrousd")
    deadline = limits.get("deadlineMs")
    if deadline is not None:
        deadline = _number(deadline, "limits.deadlineMs", high=1e12)
    cluster_limit = _integer(limits.get("maxClusterTasks", 8), "limits.maxClusterTasks", low=1, high=50)
    max_clusters = _integer(limits.get("maxClusters", 32), "limits.maxClusters", low=1, high=100)
    tasks = _topological(tuple(_parse_task(item) for item in raw_tasks))
    agents = tuple(_parse_agent(item, profile_id, weights,
                                weight_version if raw_weights is not None else None) for item in raw_agents)
    if len({agent.id for agent in agents}) != len(agents):
        raise HierarchyError("agent IDs must be unique")

    # Greedy deterministic partition: co-locate compatible dependent work, but
    # never cross task family or declared data-boundary groups.
    clusters: list[dict[str, Any]] = []
    task_cluster: dict[str, str] = {}
    for task in tasks:
        key = (task.family, task.boundary)
        candidates = [c for c in clusters if c["key"] == key and len(c["tasks"]) < cluster_limit]
        dep_clusters = {task_cluster[dep] for dep in task.dependencies if dep in task_cluster}
        chosen = min(candidates, key=lambda c: (0 if c["id"] in dep_clusters else 1, len(c["tasks"]), c["id"])) if candidates else None
        if chosen is None:
            if len(clusters) >= max_clusters:
                raise HierarchyError("maxClusters bound exceeded")
            chosen = {"id": f"cluster-{len(clusters)+1:03d}", "key": key, "tasks": []}
            clusters.append(chosen)
        chosen["tasks"].append(task)
        task_cluster[task.id] = chosen["id"]

    blockers: list[dict[str, str]] = []
    assignment_load: dict[str, int] = defaultdict(int)
    leader_load: dict[str, int] = defaultdict(int)
    assignments: list[dict[str, Any]] = []
    cluster_outputs: list[dict[str, Any]] = []
    task_agents: dict[str, _Agent] = {}
    for cluster in clusters:
        members: list[_Task] = cluster["tasks"]
        leader_options = [a for a in agents if a.role in ("leader", "leader_worker")
                          and "coordination" in a.capabilities
                          and leader_load[a.id] < a.cluster_capacity
                          and profile_id in a.profile_ids
                          and all(t.scope in a.scopes and t.boundary in a.boundaries
                                  and set(t.actions) <= set(a.actions) for t in members)]
        leader = min(leader_options, key=lambda a: (-float(a.weighted["score"]), a.id)) if leader_options else None
        if leader is None:
            blockers.append({"code": "leader_unavailable", "clusterId": cluster["id"],
                             "detail": "No in-capacity leader with coordination capability covers every cluster action, scope, and data boundary with complete profile evidence."})
        else:
            leader_load[leader.id] += 1
        cluster_assignments = []
        for task in members:
            options = [a for a in agents if a.role in ("worker", "leader_worker")
                       and assignment_load[a.id] < a.capacity and _covers(a, task, profile_id)]
            worker = min(options, key=lambda a: (-float(a.weighted["score"]), assignment_load[a.id], a.id)) if options else None
            if worker is None:
                blockers.append({"code": "worker_unavailable", "taskId": task.id,
                                 "detail": "No in-capacity worker matches profile, capability, exact scope, and data boundary."})
                continue
            assignment_load[worker.id] += 1
            task_agents[task.id] = worker
            cost = task.estimated_cost if task.estimated_cost is not None else worker.unit_cost
            assignments.append({"taskId": task.id, "clusterId": cluster["id"], "leaderId": leader.id if leader else None,
                                "workerId": worker.id, "authorizationGrantId": worker.grant_id,
                                "declaredActions": list(task.actions), "dependencies": list(task.dependencies),
                                "estimatedCostMicrousd": cost,
                                "costSource": "task_input" if task.estimated_cost is not None else ("agent_rate_estimate" if worker.unit_cost is not None else "unknown"),
                                "estimatedLatencyMs": task.latency_ms,
                                "leaderMetricWeightVersion": leader.weighted["metricWeightVersion"] if leader else None,
                                "workerMetricWeightVersion": worker.weighted["metricWeightVersion"],
                                "workerProfileScore": worker.weighted["score"],
                                "workerMetricComponents": worker.weighted["components"]})
            cluster_assignments.append(task.id)
        cluster_outputs.append({"clusterId": cluster["id"], "family": cluster["key"][0],
                                "dataBoundary": cluster["key"][1], "taskIds": cluster_assignments,
                                "leaderId": leader.id if leader else None,
                                "leaderAuthorizationGrantId": leader.grant_id if leader else None,
                                "leaderLoad": leader_load[leader.id] if leader else None,
                                "leaderProfileScore": leader.weighted["score"] if leader else None,
                                "leaderMetricComponents": leader.weighted["components"] if leader else None,
                                "crossClusterDependencies": sorted({task_cluster[d] for t in members for d in t.dependencies
                                                                    if d in task_cluster and task_cluster[d] != cluster["id"]})})

    task_map = {task.id: task for task in tasks}
    latency_by_id = {task.id: task.latency_ms for task in tasks}
    finish: dict[str, float] = {}
    for task in tasks:
        finish[task.id] = latency_by_id[task.id] + max((finish[dep] for dep in task.dependencies), default=0.0)
    critical_path = max(finish.values(), default=0.0)
    cost_values = [assignment["estimatedCostMicrousd"] for assignment in assignments]
    unknown_cost_tasks = sorted(a["taskId"] for a in assignments if a["estimatedCostMicrousd"] is None)
    estimated_total = sum(cost_values) if not unknown_cost_tasks and len(assignments) == len(tasks) else None
    if unknown_cost_tasks:
        blockers.append({"code": "unknown_cost", "clusterId": "", "detail": "Cost per accepted outcome remains unknown until actual receipts and evaluator outcomes exist."})
    if estimated_total is not None and estimated_total > budget:
        blockers.append({"code": "budget_exceeded", "clusterId": "", "detail": "Estimated task spend exceeds the declared plan budget."})
    if deadline is not None and critical_path > deadline:
        blockers.append({"code": "deadline_exceeded", "clusterId": "", "detail": "Declared critical-path estimate exceeds the task deadline."})
    status = "plan_only"
    codes = {item["code"] for item in blockers}
    if "budget_exceeded" in codes:
        status = "over_budget"
    elif "deadline_exceeded" in codes:
        status = "deadline_exceeded"
    elif "unknown_cost" in codes:
        status = "blocked_unknown_cost"
    elif blockers:
        status = "not_plannable"
    accepted_outcomes = None  # This planner has no evaluator run records.
    return {
        "schemaVersion": "hierarchical-plan-v1", "status": status, "execution": "plan_only",
        "profile": profile, "hierarchy": {"root": "root", "domainCoordinator": profile_id,
            "depth": 4, "hardGates": list(HARD_GATES), "clusters": cluster_outputs},
        "assignments": assignments, "assignmentLoad": dict(sorted(assignment_load.items())),
        "leaderLoad": dict(sorted(leader_load.items())),
        "taskCount": len(tasks), "clusterCount": len(clusters),
        "estimatedCriticalPathMs": round(critical_path, 3), "deadlineMs": deadline,
        "budgetMicrousd": budget, "estimatedTotalCostMicrousd": estimated_total,
        "unknownCostTaskIds": unknown_cost_tasks, "actualCostMicrousd": None,
        "acceptedOutcomeCount": accepted_outcomes, "actualCostPerAcceptedOutcomeMicrousd": None,
        "unitEconomics": {"status": "estimate_only" if estimated_total is not None else "unknown",
            "formula": "total measured cost including failed attempts / independently accepted outcomes",
            "estimateMicrousd": estimated_total, "actualMicrousd": None,
            "acceptedOutcomes": None, "costPerAcceptedOutcomeMicrousd": None,
            "limitations": ["No execution or evaluator attempts were run.",
                            "Caller cost values are estimates, not provider receipts.",
                            "Unknown costs are not zero and prevent a budget-cleared plan."]},
        "blockers": blockers,
        "limits": ["Deterministic plan only; no agents, tools, models, or credentials were dispatched.",
                   "Caller-supplied capabilities, scopes, profile scores, rates, and latency are unverified assertions.",
                   "Exact resource authorization and budget enforcement must be repeated at the execution boundary.",
                   "The weighted profile score ranks declared evidence only; it cannot override hard gates.",
                   "Critical path uses caller latency estimates and ignores queueing and runtime variance."],
    }
