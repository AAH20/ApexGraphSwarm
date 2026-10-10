"""Compile a verified constrained model schedule into a control-plane plan.

Compilation creates metadata only. It does not dispatch adapters, call model
providers, or prove that supplied prices, durations, or adapter configuration
are accurate outside the explicit mapping supplied by the caller.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

from .optimization import DagTask, ModelOption, OptimizationInputError, schedule_dag


class DelegationPlanError(ValueError):
    """A schedule or its executable adapter mapping is unsafe to compile."""


_TASK_FIELDS = {"id", "dependencies", "duration_estimate", "options", "deadline"}
_PROBLEM_FIELDS = {"tasks", "model_options", "budget_microusd", "capacities",
                   "deadline_seconds", "exact_max_tasks"}
_BINDING_FIELDS = {"configured", "adapterId", "operation", "modelId", "resourceId",
                   "toolId", "costMicrousd", "maxParallel"}
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./:@-]{0,127}$")
_SECRET_KEY = re.compile(r"(?:^|[_-])(api[_-]?key|access[_-]?token|password|secret|credential|authorization)(?:$|[_-])", re.IGNORECASE)
_GRAPH_FIELDS = {"version", "name", "nodes", "edges", "warnings", "truncated", "summary", "unresolved"}
_NODE_FIELDS = {"id", "name", "kind", "path", "summary", "confidence", "line", "connections"}
_EDGE_FIELDS = {"source", "target", "relation", "confidence", "line", "count"}
_GRAPH_KINDS = {"module", "file", "function", "class", "external"}
_GRAPH_EVIDENCE = {"parsed", "observed", "inferred", "illustrative", "aggregated"}
MAX_REVIEW_NODES = 300
MAX_REVIEW_EDGES = 900
MAX_GOAL_CHARS = 2_000
MAX_REVIEW_GRAPH_BYTES = 2 * 1024 * 1024
MAX_COMPILED_PLAN_BYTES = 1024 * 1024
MAX_OUTPUT_TOKENS = 600


def _canonical(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                          allow_nan=False)
    except (TypeError, ValueError, RecursionError) as exc:
        raise DelegationPlanError("Problem and adapter mappings must be finite JSON data.") from exc


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _record(value: Any, label: str, allowed: set[str], required: set[str] = frozenset()) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise DelegationPlanError(f"{label} must be a JSON object.")
    if set(value) - allowed or required - set(value):
        raise DelegationPlanError(f"{label} contains missing or unsupported fields.")
    return value


def _options(value: Any, label: str) -> tuple[ModelOption, ...]:
    if not isinstance(value, (tuple, list)):
        raise DelegationPlanError(f"{label} must be a list.")
    result = []
    for index, raw in enumerate(value):
        option = _record(raw, f"{label}[{index}]",
                         {"model", "estimated_cost_microusd", "duration_estimate", "eligible"},
                         {"model", "duration_estimate"})
        result.append(ModelOption(option["model"], option.get("estimated_cost_microusd"),
                                  option["duration_estimate"], option.get("eligible", True)))
    return tuple(result)


def _parse_problem(value: Any) -> tuple[dict[str, Any], tuple[DagTask, ...], tuple[ModelOption, ...]]:
    problem = _record(value, "problem", _PROBLEM_FIELDS,
                      {"tasks", "budget_microusd", "capacities"})
    raw_tasks = problem["tasks"]
    if not isinstance(raw_tasks, (tuple, list)) or not raw_tasks:
        raise DelegationPlanError("problem.tasks must contain at least one task.")
    tasks = []
    for index, raw in enumerate(raw_tasks):
        item = _record(raw, f"problem.tasks[{index}]", _TASK_FIELDS, {"id"})
        if not isinstance(item["id"], str) or not item["id"].strip() or len(item["id"]) > 128 or "\x00" in item["id"]:
            raise DelegationPlanError(f"problem.tasks[{index}].id must be a stable non-empty string.")
        dependencies = item.get("dependencies", ())
        if not isinstance(dependencies, (tuple, list)) or any(not isinstance(dep, str) for dep in dependencies):
            raise DelegationPlanError(f"Task {item['id']!r} dependencies must be a list.")
        tasks.append(DagTask(item["id"], tuple(dependencies), item.get("duration_estimate", 0.0),
                             _options(item.get("options", ()), f"Task {item['id']!r} options"),
                             item.get("deadline")))
    options = _options(problem.get("model_options", ()), "problem.model_options")
    return problem, tuple(tasks), options


def _safe_reference(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
        raise DelegationPlanError(f"{label} must be a stable exact identifier.")
    return value


def _binding(model: str, raw: Any, *, declared_capacity: Any,
             scheduled_cost: int) -> dict[str, Any]:
    binding = _record(raw, f"model_bindings[{model!r}]", _BINDING_FIELDS,
                      _BINDING_FIELDS)
    if binding["configured"] is not True:
        raise DelegationPlanError(f"Model {model!r} has no explicitly configured adapter mapping.")
    adapter = _safe_reference(binding["adapterId"], "adapterId")
    operation = _safe_reference(binding["operation"], "operation")
    configured_model = _safe_reference(binding["modelId"], "modelId")
    resource = _safe_reference(binding["resourceId"], "resourceId")
    tool = _safe_reference(binding["toolId"], "toolId")
    if tool != f"integration:{adapter}:{operation}":
        raise DelegationPlanError(f"Model {model!r} toolId must exactly match its adapter and operation.")
    if type(binding["costMicrousd"]) is not int or binding["costMicrousd"] < 0:
        raise DelegationPlanError(f"Model {model!r} requires a known non-negative integer cost mapping.")
    if binding["costMicrousd"] != scheduled_cost:
        raise DelegationPlanError(f"Model {model!r} schedule cost does not match its configured cost mapping.")
    if type(declared_capacity) is not int or declared_capacity < 1:
        raise DelegationPlanError(f"Selected model {model!r} has no positive declared capacity.")
    if type(binding["maxParallel"]) is not int or binding["maxParallel"] < declared_capacity:
        raise DelegationPlanError(f"Model {model!r} declared capacity exceeds its configured adapter capacity.")
    return {"adapterId": adapter, "operation": operation, "modelId": configured_model,
            "resourceId": resource, "toolId": tool,
            "costMicrousd": binding["costMicrousd"], "maxParallel": binding["maxParallel"]}


def _review_input(raw: Any, task_id: str) -> dict[str, Any]:
    value = _record(raw, f"task_inputs[{task_id!r}]", {"goal", "graph", "parameters"},
                    {"goal", "graph"})
    goal = value["goal"]
    if not isinstance(goal, str) or not 1 <= len(goal.strip()) <= MAX_GOAL_CHARS:
        raise DelegationPlanError(f"task_inputs[{task_id!r}].goal must contain 1–2,000 non-whitespace characters.")
    graph = _record(value["graph"], f"task_inputs[{task_id!r}].graph", _GRAPH_FIELDS,
                    {"version", "name", "nodes", "edges"})
    if type(graph["version"]) is not int or graph["version"] < 1:
        raise DelegationPlanError(f"Task {task_id!r} graph version must be a positive integer.")
    if not isinstance(graph["name"], str) or len(graph["name"]) > 500:
        raise DelegationPlanError(f"Task {task_id!r} graph name is invalid.")
    nodes, edges = graph["nodes"], graph["edges"]
    if not isinstance(nodes, list) or len(nodes) > MAX_REVIEW_NODES:
        raise DelegationPlanError(f"Task {task_id!r} graph must contain at most {MAX_REVIEW_NODES} nodes.")
    if not isinstance(edges, list) or len(edges) > MAX_REVIEW_EDGES:
        raise DelegationPlanError(f"Task {task_id!r} graph must contain at most {MAX_REVIEW_EDGES} edges.")
    node_ids: set[str] = set()
    for index, raw_node in enumerate(nodes):
        node = _record(raw_node, f"graph.nodes[{index}]", _NODE_FIELDS,
                       {"id", "name", "kind", "path", "confidence"})
        if (not _bounded_string(node["id"], 2_000, nonempty=True)
                or node["id"] in node_ids
                or not _bounded_string(node["name"], 2_000)
                or not _bounded_string(node["path"], 4_000)
                or not isinstance(node["kind"], str) or node["kind"] not in _GRAPH_KINDS
                or not isinstance(node["confidence"], str) or node["confidence"] not in _GRAPH_EVIDENCE
                or not _bounded_string(node.get("summary", ""), 10_000)):
            raise DelegationPlanError(f"Task {task_id!r} graph contains an invalid or duplicate node.")
        if "line" in node and (type(node["line"]) is not int or node["line"] < 1):
            raise DelegationPlanError(f"Task {task_id!r} graph node line must be a positive integer.")
        if "connections" in node and (type(node["connections"]) is not int or node["connections"] < 0):
            raise DelegationPlanError(f"Task {task_id!r} graph node connections must be non-negative.")
        node_ids.add(node["id"])
    for index, raw_edge in enumerate(edges):
        edge = _record(raw_edge, f"graph.edges[{index}]", _EDGE_FIELDS,
                       {"source", "target", "relation", "confidence"})
        if (not _bounded_string(edge["source"], 2_000, nonempty=True)
                or not _bounded_string(edge["target"], 2_000, nonempty=True)
                or edge["source"] not in node_ids or edge["target"] not in node_ids
                or not _bounded_string(edge["relation"], 100, nonempty=True)
                or not isinstance(edge["confidence"], str) or edge["confidence"] not in _GRAPH_EVIDENCE):
            raise DelegationPlanError(f"Task {task_id!r} graph contains an invalid edge or dangling endpoint.")
        if "line" in edge and (type(edge["line"]) is not int
                                or (edge["line"] < 1 and not (edge["line"] == 0 and edge["relation"] == "contains"))):
            raise DelegationPlanError(f"Task {task_id!r} graph edge line is invalid.")
        if "count" in edge and (type(edge["count"]) is not int or edge["count"] < 1):
            raise DelegationPlanError(f"Task {task_id!r} graph edge count must be positive.")
    if "warnings" in graph and (not isinstance(graph["warnings"], list) or len(graph["warnings"]) > 1_000
                                 or any(not _bounded_string(item, 10_000) for item in graph["warnings"])):
        raise DelegationPlanError(f"Task {task_id!r} graph warnings are invalid.")
    if "truncated" in graph and type(graph["truncated"]) is not bool:
        raise DelegationPlanError(f"Task {task_id!r} graph truncated must be boolean.")
    if "summary" in graph:
        summary = graph["summary"]
        if not isinstance(summary, dict) or ("unresolved" in summary and
                (type(summary["unresolved"]) is not int or summary["unresolved"] < 0)):
            raise DelegationPlanError(f"Task {task_id!r} graph summary is invalid.")
    if "unresolved" in graph:
        unresolved = graph["unresolved"]
        if (not isinstance(unresolved, list) or len(unresolved) > 200
                or any(not isinstance(row, dict) or set(row) != {"path", "line", "expression"}
                       or not _bounded_string(row["path"], 4_000)
                       or type(row["line"]) is not int or row["line"] < 1
                       or not _bounded_string(row["expression"], 2_000)
                       for row in unresolved)):
            raise DelegationPlanError(f"Task {task_id!r} graph unresolved references are invalid.")
    parameters = value.get("parameters", {})
    if not isinstance(parameters, dict) or set(parameters) - {"maxOutputTokens"}:
        raise DelegationPlanError(f"Task {task_id!r} review parameters only support maxOutputTokens.")
    output_tokens = parameters.get("maxOutputTokens", MAX_OUTPUT_TOKENS)
    if type(output_tokens) is not int or not 100 <= output_tokens <= MAX_OUTPUT_TOKENS:
        raise DelegationPlanError(f"Task {task_id!r} maxOutputTokens must be from 100 to 600.")
    normalized = {"goal": goal.strip(), "graph": graph,
                  "parameters": {"maxOutputTokens": output_tokens}}
    _reject_secret_keys(normalized, task_id)
    if len(_canonical(normalized).encode("utf-8")) > MAX_REVIEW_GRAPH_BYTES:
        raise DelegationPlanError(f"Task {task_id!r} review input exceeds the 2 MB integration limit.")
    return normalized


def _bounded_string(value: Any, maximum: int, *, nonempty: bool = False) -> bool:
    return isinstance(value, str) and len(value) <= maximum and (not nonempty or bool(value))


def _reject_secret_keys(value: Any, task_id: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str) and _SECRET_KEY.search(key) and not key.lower().endswith(("_ref", "-ref")):
                raise DelegationPlanError(f"Task {task_id!r} review input must not contain credential fields.")
            _reject_secret_keys(child, task_id)
    elif isinstance(value, list):
        for child in value:
            _reject_secret_keys(child, task_id)


def compile_delegation_plan(problem: Mapping[str, Any],
                            model_bindings: Mapping[str, Mapping[str, Any]], *,
                            task_inputs: Mapping[str, Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Recompute a feasible schedule and return a strict ControlStore plan.

    `problem` uses the `schedule_dag` JSON fields. Each selected schedule model
    must have a configured binding with exact tool/resource/model identifiers,
    a matching known per-task cost, and sufficient configured parallelism.
    The returned `plan` is compile-only metadata unless explicit `task_inputs`
    are provided for every scheduled task. Execution-enabled plans carry a
    bounded graph-review contract and require configured resource capacity at
    activation; compilation never creates a run or dispatches a provider call.
    """
    try:
        normalized_problem, tasks, global_options = _parse_problem(problem)
        if not isinstance(model_bindings, dict) or any(not isinstance(k, str) for k in model_bindings):
            raise DelegationPlanError("model_bindings must be a JSON object keyed by exact schedule model IDs.")
        budget = normalized_problem["budget_microusd"]
        capacities = normalized_problem["capacities"]
        if not isinstance(capacities, Mapping):
            raise DelegationPlanError("problem.capacities must be a model-to-integer mapping.")
        schedule = schedule_dag(
            tasks,
            model_options=global_options,
            budget_microusd=budget,
            capacities=capacities,
            deadline_seconds=normalized_problem.get("deadline_seconds"),
            exact_max_tasks=normalized_problem.get("exact_max_tasks", 8),
        )
    except (OptimizationInputError, TypeError, KeyError, OverflowError) as exc:
        raise DelegationPlanError(f"Invalid constrained schedule problem: {exc}") from exc
    if schedule.status != "feasible" or schedule.feasible is not True:
        raise DelegationPlanError(f"No verified feasible schedule is available (status={schedule.status}).")
    if not schedule.assignments or schedule.total_cost_microusd is None:
        raise DelegationPlanError("A dispatch plan requires at least one fully assigned task and known cost.")

    task_by_id = {task.id: task for task in tasks}
    task_ids = {task_id: f"task-{hashlib.sha256(task_id.encode('utf-8')).hexdigest()}"
                for task_id in task_by_id}
    assigned_models = {assignment.model for assignment in schedule.assignments}
    bindings: dict[str, dict[str, Any]] = {}
    agent_for_model: dict[str, str] = {}
    for model in sorted(assigned_models):
        if model not in model_bindings:
            raise DelegationPlanError(f"Selected model {model!r} has no explicit configured adapter mapping.")
        costs = {a.cost_microusd for a in schedule.assignments if a.model == model}
        if len(costs) != 1:
            raise DelegationPlanError(f"Model {model!r} must have one configured per-task cost for this plan.")
        try:
            bindings[model] = _binding(model, model_bindings[model],
                                       declared_capacity=capacities.get(model),
                                       scheduled_cost=next(iter(costs)))
        except OptimizationInputError as exc:
            raise DelegationPlanError(f"Invalid mapping for model {model!r}: {exc}") from exc
        binding = bindings[model]
        agent_material = _canonical([binding["adapterId"], binding["modelId"], binding["resourceId"]])
        agent_for_model[model] = "agent-" + hashlib.sha256(agent_material.encode("utf-8")).hexdigest()

    # A schedule capacity key is only meaningful if it maps to a distinct
    # physical adapter/model/resource. Aliases would let the scheduler count
    # one underlying capacity pool more than once.
    resource_owner: dict[str, str] = {}
    endpoint_owner: dict[tuple[str, str], str] = {}
    for model in sorted(assigned_models):
        binding = bindings[model]
        resource = binding["resourceId"]
        endpoint = (binding["adapterId"], binding["modelId"])
        if resource in resource_owner and resource_owner[resource] != model:
            raise DelegationPlanError(
                f"Selected model IDs {resource_owner[resource]!r} and {model!r} share resource {resource!r}; capacity would be double-counted.")
        if endpoint in endpoint_owner and endpoint_owner[endpoint] != model:
            raise DelegationPlanError(
                f"Selected model IDs {endpoint_owner[endpoint]!r} and {model!r} alias the same adapter/model endpoint; capacity would be double-counted.")
        resource_owner[resource] = model
        endpoint_owner[endpoint] = model

    execution_inputs: dict[str, dict[str, Any]] | None = None
    source_content: dict[str, Any] = {"problem": normalized_problem,
                                      "modelBindings": model_bindings}
    if task_inputs is not None:
        if not isinstance(task_inputs, Mapping) or any(not isinstance(key, str) for key in task_inputs):
            raise DelegationPlanError("task_inputs must be an object keyed by exact source task IDs.")
        expected_ids = {assignment.task_id for assignment in schedule.assignments}
        if set(task_inputs) != expected_ids:
            raise DelegationPlanError("Execution-enabled task_inputs must exactly cover the scheduled source task IDs.")
        execution_inputs = {}
        for assignment in schedule.assignments:
            binding = bindings[assignment.model]
            if binding["adapterId"] not in {"openrouter", "vllm"} or binding["operation"] != "review":
                raise DelegationPlanError("Execution-enabled plans require pinned OpenRouter or vLLM review bindings.")
            capacity = capacities.get(assignment.model)
            if type(capacity) is not int or not 1 <= capacity <= 10_000:
                raise DelegationPlanError("Execution-enabled model capacity must be an integer from 1 to 10,000.")
            execution_inputs[assignment.task_id] = _review_input(
                task_inputs[assignment.task_id], assignment.task_id)
        source_content["taskInputs"] = execution_inputs
    source_hash = _digest(source_content)

    agents_by_id = {agent_for_model[model]: {
        "id": agent_for_model[model],
        "name": f"{bindings[model]['adapterId']}:{bindings[model]['modelId']}"}
        for model in sorted(assigned_models)}
    plan_tasks = []
    for assignment in schedule.assignments:
        source_task = task_by_id[assignment.task_id]
        binding = bindings[assignment.model]
        task_payload: dict[str, Any] = {
            "sourceTaskId": assignment.task_id,
            "sourcePlanHash": source_hash,
            "scheduleModel": assignment.model,
            "modelId": binding["modelId"],
            "adapterId": binding["adapterId"],
            "operation": binding["operation"],
            "scheduledStartSeconds": assignment.start,
            "scheduledFinishSeconds": assignment.finish,
            "durationEstimateSeconds": assignment.finish - assignment.start,
            "taskDurationEstimateSeconds": source_task.duration_estimate,
            "deadlineEstimateSeconds": source_task.deadline,
        }
        if execution_inputs is not None:
            task_payload["execution"] = {
                "version": 1,
                "integrationId": binding["adapterId"],
                "operation": "review",
                "input": execution_inputs[assignment.task_id],
            }
        task_spec = {
            "id": task_ids[assignment.task_id],
            "agentId": agent_for_model[assignment.model],
            "dependencies": [task_ids[dep] for dep in source_task.dependencies],
            "payload": task_payload,
            "reservedCostMicrousd": assignment.cost_microusd,
            "maxAttempts": 1,
            "executionClass": "external",
            "tool": binding["toolId"],
            "resource": binding["resourceId"],
        }
        if execution_inputs is not None:
            task_spec["requireResourceCapacity"] = True
            task_spec["resourceConcurrencyLimit"] = capacities[assignment.model]
        plan_tasks.append(task_spec)
    if len(task_ids) != len(set(task_ids.values())):
        raise DelegationPlanError("Deterministic source task IDs collided; refusing to compile.")
    plan = {"version": 1, "agents": sorted(agents_by_id.values(), key=lambda agent: agent["id"]),
            "tasks": plan_tasks}
    if len(_canonical(plan).encode("utf-8")) > MAX_COMPILED_PLAN_BYTES:
        raise DelegationPlanError("Compiled plan exceeds the 1 MB durable-plan limit.")
    plan_hash = _digest(plan)
    selected_assignments = [{"sourceTaskId": assignment.task_id,
                             "scheduleModel": assignment.model,
                             "configuredModelId": bindings[assignment.model]["modelId"],
                             "adapterId": bindings[assignment.model]["adapterId"],
                             "operation": bindings[assignment.model]["operation"],
                             "resourceId": bindings[assignment.model]["resourceId"],
                             "toolId": bindings[assignment.model]["toolId"],
                             "startSeconds": assignment.start,
                             "finishSeconds": assignment.finish,
                             "durationEstimateSeconds": assignment.finish - assignment.start,
                             "taskDurationEstimateSeconds": task_by_id[assignment.task_id].duration_estimate,
                             "deadlineEstimateSeconds": task_by_id[assignment.task_id].deadline,
                             "reservedCostMicrousd": assignment.cost_microusd}
                            for assignment in schedule.assignments]
    return {
        "plan": plan,
        "planMode": "executable_review_plan" if execution_inputs is not None else "compile_only_metadata",
        "sourceInputSha256": source_hash,
        "planSha256": plan_hash,
        "budgetMicrousd": budget,
        "schedule": {"status": schedule.status, "feasible": schedule.feasible,
                     "algorithm": schedule.algorithm, "exact": schedule.exact,
                     "limits": list(schedule.limits),
                     "adapterConfigurationEvidence": "caller_asserted_not_independently_verified",
                     "scheduleConstraintsEnforcedByControlStore": ["dependencies", "exact grants", "run and grant budgets"],
                     "scheduleConstraintsNotEnforcedByControlStore": ["scheduled start/finish times", "per-model parallel capacities", "estimated deadlines"],
                     "totalCostMicrousd": schedule.total_cost_microusd,
                     "makespanEstimateSeconds": schedule.makespan,
                     "deadlineEstimateSeconds": normalized_problem.get("deadline_seconds"),
                     "capacities": {model: capacities[model] for model in sorted(capacities)},
                     "assignments": selected_assignments,
                     "optimalityClaim": "bounded-optimal" if schedule.exact else "heuristic-no-optimality-guarantee",
                     "dispatchPerformed": False,
                     "activationRequiresConfiguredResourceCapacity": execution_inputs is not None},
    }
