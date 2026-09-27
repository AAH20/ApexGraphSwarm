"""Bounded, read-only projection of control-plane history into an explanation graph.

The projection exposes identifiers, states, safe accounting summaries and relationship
edges. It deliberately never copies task payloads, result bodies, errors, receipts,
checkpoints or lease credentials into the graph.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import threading
from pathlib import Path
from typing import Any, Mapping

from .control import ControlStore

DEFAULT_MAX_NODES = 500
DEFAULT_MAX_EDGES = 1000
MAX_NODES = 5000
MAX_EDGES = 10000
MAX_SOURCE_ROWS = 20000
MAX_ID_LENGTH = 256

_LIMITATIONS = [
    "This is a projection of persisted control-store status and ledger receipts, not a live execution trace.",
    "Attempts without persisted ledger rows are reported as missing coverage; no historical attempt or cost is fabricated.",
    "Known actual cost includes only recorded integer micro-USD receipts; unresolved liabilities remain unknown.",
    "Payloads, results, errors, receipts, checkpoint bodies, lease tokens and credentials are excluded.",
]


def project_execution_graph(
    status: Mapping[str, Any],
    ledger: Mapping[str, Any] | None = None,
    *,
    max_nodes: int = DEFAULT_MAX_NODES,
    max_edges: int = DEFAULT_MAX_EDGES,
) -> dict[str, Any]:
    """Project a ControlStore status mapping and optional ledger view to bounded JSON data.

    Nodes are prioritized as run, tasks, persisted attempts, then attribution/resource
    identities. Edges whose endpoints are absent because of truncation are omitted.
    """
    if type(max_nodes) is not int or not 1 <= max_nodes <= MAX_NODES:
        raise ValueError(f"max_nodes must be an integer from 1 to {MAX_NODES}.")
    if type(max_edges) is not int or not 0 <= max_edges <= MAX_EDGES:
        raise ValueError(f"max_edges must be an integer from 0 to {MAX_EDGES}.")
    if not isinstance(status, Mapping):
        raise ValueError("status must be a mapping.")
    run = status.get("run")
    tasks = status.get("tasks", ())
    agents = status.get("agents", ())
    if not isinstance(run, Mapping) or not _valid_id(run.get("id")):
        raise ValueError("status.run.id is required.")
    _sequence(tasks, "status.tasks")
    _sequence(agents, "status.agents")
    if len(tasks) > MAX_SOURCE_ROWS or len(agents) > MAX_SOURCE_ROWS:
        raise ValueError("status exceeds the bounded source-row limit.")
    ledger_view = ledger if ledger is not None else status.get("ledger", {})
    if not isinstance(ledger_view, Mapping):
        raise ValueError("ledger must be a mapping.")
    attempt_rows = ledger_view.get("attempts", ())
    _sequence(attempt_rows, "ledger.attempts")
    if len(attempt_rows) > MAX_SOURCE_ROWS:
        raise ValueError("ledger exceeds the bounded source-row limit.")

    run_id = run["id"]
    specs: list[dict[str, Any]] = []
    edge_specs: list[tuple[str, str, str, str | None]] = []

    run_explanations: list[str] = []
    if run.get("budgetExceeded") is True:
        run_explanations.append("Run budget is marked exceeded by the control store.")
    if run.get("cancelRequested") is True:
        run_explanations.append("Run cancellation was requested.")
    specs.append(_node(
        f"run:{run_id}", "run", f"Run {run_id}", status=run.get("status"),
        reserved=_integer_or_none(run.get("reservedMicrousd")),
        actual=_integer_or_none(run.get("spentMicrousd")),
        details={key: run[key] for key in ("budgetMicrousd", "remainingMicrousd", "version")
                 if key in run and _json_scalar(run.get(key))},
        explanations=run_explanations,
    ))

    task_by_key: dict[str, str] = {}
    task_rows_by_id: dict[str, Mapping[str, Any]] = {}
    for task in tasks:
        if not isinstance(task, Mapping) or not _valid_id(task.get("taskId")):
            continue
        task_id = task["taskId"]
        if task_id in task_rows_by_id:
            continue
        task_key = task.get("id")
        node_id = f"task:{task_id}"
        if _valid_id(task_key):
            task_by_key[task_key] = node_id
        task_rows_by_id[task_id] = task
        explanations = _task_explanations(task, tasks)
        specs.append(_node(
            node_id, "task", str(task_key) if _valid_id(task_key) else f"Task {task_id}",
            status=task.get("status"), reserved=_integer_or_none(task.get("reservedCostMicrousd")),
            actual=None, details=_task_details(task), explanations=explanations,
        ))
        edge_specs.append((f"run:{run_id}", node_id, "contains", None))
        contract_id = task.get("specialistContractId")
        if _valid_id(contract_id):
            contract_node_id = f"specialist-contract:{contract_id}"
            binding = _specialist_access_details(task.get("payload"), contract_id)
            specs.append(_node(
                contract_node_id, "specialist_contract", f"Specialist contract {contract_id}",
                status="bound", details=binding,
                explanations=["Bound in this task snapshot; this graph does not represent live authorization."],
            ))
            edge_specs.append((node_id, contract_node_id, "governed_by", "bound contract; not live authorization"))
        if _valid_id(task.get("tool")) and _valid_id(task.get("resource")):
            resource_node_id = f"resource:{task['tool']}/{task['resource']}"
            specs.append(_node(resource_node_id, "resource", f"{task['tool']} / {task['resource']}",
                               details={"tool": task["tool"], "resource": task["resource"]}))
            edge_specs.append((node_id, resource_node_id, "requires_resource", "requires exact resource"))

        agent_id = task.get("agentId")
        if _valid_id(agent_id):
            edge_specs.append((node_id, f"agent:{agent_id}", "assigned", "declared agent"))
        dependencies = task.get("dependencies", ())
        if isinstance(dependencies, (list, tuple)):
            for dependency in dependencies:
                if isinstance(dependency, str) and dependency in task_by_key:
                    edge_specs.append((node_id, task_by_key[dependency], "dependency", "depends on"))

    # The caller may pass task status in arbitrary order. Resolve any dependencies
    # which appeared before their predecessor using the complete key map.
    edge_specs = [edge for edge in edge_specs if edge[2] != "dependency"]
    for task in tasks:
        if not isinstance(task, Mapping) or not _valid_id(task.get("taskId")):
            continue
        dependencies = task.get("dependencies", ())
        if isinstance(dependencies, (list, tuple)):
            target = f"task:{task['taskId']}"
            for dependency in dependencies:
                if isinstance(dependency, str) and dependency in task_by_key:
                    edge_specs.append((target, task_by_key[dependency], "dependency", "depends on"))

    for agent in agents:
        if not isinstance(agent, Mapping) or not _valid_id(agent.get("id")):
            continue
        agent_id = agent["id"]
        name = agent.get("name")
        label = name if isinstance(name, str) and 0 < len(name) <= 128 else agent_id
        specs.append(_node(f"agent:{agent_id}", "agent", label))

    attempt_by_id: dict[str, Mapping[str, Any]] = {}
    task_attempts: dict[str, list[Mapping[str, Any]]] = {}
    for attempt in attempt_rows:
        if not isinstance(attempt, Mapping) or not _valid_id(attempt.get("attemptId")):
            continue
        attempt_id = attempt["attemptId"]
        if attempt_id in attempt_by_id:
            continue
        task_id = attempt.get("taskId")
        if not _valid_id(task_id) or task_id not in task_rows_by_id:
            continue
        attempt_by_id[attempt_id] = attempt
        task_attempts.setdefault(task_id, []).append(attempt)
        attempt_node_id = f"attempt:{attempt_id}"
        actual = _integer_or_none(attempt.get("actualCostMicrousd"))
        reserved = _integer_or_none(attempt.get("reservedMicrousd"))
        cost_state = "unknown" if actual is None else "known"
        explanations = ["Actual attempt cost is unresolved."] if actual is None else []
        specs.append(_node(
            attempt_node_id, "attempt", f"{task_rows_by_id[task_id].get('id', task_id)} / attempt {attempt.get('attempt')}",
            status=attempt.get("outcome"), reserved=reserved, actual=actual,
            details={"attempt": _integer_or_none(attempt.get("attempt")),
                     "costState": cost_state,
                     "startedAt": _number_or_none(attempt.get("startedAt")),
                     "settledAt": _number_or_none(attempt.get("settledAt"))},
            explanations=explanations,
        ))
        task_node_id = f"task:{task_id}"
        edge_specs.append((attempt_node_id, task_node_id, "attempt_of", "execution attempt"))

        worker_id = attempt.get("workerId")
        if _valid_id(worker_id):
            worker_node_id = f"worker:{worker_id}"
            specs.append(_node(worker_node_id, "worker", worker_id,
                               details={"identityType": "execution_worker"}))
            edge_specs.append((attempt_node_id, worker_node_id, "executed", "executed by"))
        principal_id = attempt.get("principalId")
        if _valid_id(principal_id):
            principal_node_id = f"principal:{principal_id}"
            specs.append(_node(principal_node_id, "principal", principal_id))
            edge_specs.append((attempt_node_id, principal_node_id, "attributed_to", "principal"))
        grant_id = attempt.get("grantId")
        if _valid_id(grant_id):
            grant_node_id = f"grant:{grant_id}"
            specs.append(_node(grant_node_id, "grant", f"Grant {grant_id}"))
            edge_specs.append((attempt_node_id, grant_node_id, "authorized", "authorized by"))
            if _valid_id(principal_id):
                edge_specs.append((grant_node_id, f"principal:{principal_id}", "granted_to", "granted to"))
        tool = attempt.get("tool")
        resource = attempt.get("resource")
        if _valid_id(tool) or _valid_id(resource):
            safe_tool = tool if _valid_id(tool) else "unknown-tool"
            safe_resource = resource if _valid_id(resource) else "unknown-resource"
            resource_node_id = f"resource:{safe_tool}/{safe_resource}"
            specs.append(_node(resource_node_id, "resource", f"{safe_tool} / {safe_resource}",
                               details={"tool": safe_tool, "resource": safe_resource}))
            edge_specs.append((attempt_node_id, resource_node_id, "uses_resource", "uses"))

    # Task aggregate actual cost is derived from real attempt receipts only. A task
    # with absent or unresolved expected rows has unknown actual, never a guessed zero.
    attempts_expected = {task_id: _nonnegative_int(task.get("attempts"))
                         for task_id, task in task_rows_by_id.items()}
    missing_expected = 0
    for task_id, task in task_rows_by_id.items():
        recorded = task_attempts.get(task_id, [])
        expected = attempts_expected[task_id]
        missing_expected += max(0, expected - len(recorded))
        actual_values = [_integer_or_none(item.get("actualCostMicrousd")) for item in recorded]
        if expected == len(recorded) and all(value is not None for value in actual_values):
            task_actual = sum(value for value in actual_values if value is not None)
        elif expected == 0:
            task_actual = 0
        else:
            task_actual = None
        for node in specs:
            if node["id"] == f"task:{task_id}":
                if task_actual is not None:
                    node["actualMicrousd"] = task_actual
                if task_actual is None:
                    node["explanations"].append(
                        "Task actual cost is incomplete because one or more persisted attempt receipts are unresolved or absent.")
                break

    selected_nodes = _dedupe_nodes(specs)
    kept_nodes = selected_nodes[:max_nodes]
    kept_ids = {node["id"] for node in kept_nodes}
    all_node_ids = {node["id"] for node in selected_nodes}
    omitted_nodes = max(0, len(selected_nodes) - len(kept_nodes))

    # Missing source endpoints are genuinely dangling and excluded. Edges removed
    # because a bounded node page omitted an endpoint count toward truncation.
    unique_edges: list[tuple[str, str, str, str | None]] = []
    seen_edges: set[tuple[str, str, str]] = set()
    for source, target, kind, label in edge_specs:
        key = (source, target, kind)
        if key in seen_edges or source not in all_node_ids or target not in all_node_ids:
            continue
        seen_edges.add(key)
        unique_edges.append((source, target, kind, label))
    endpoint_edges = [edge for edge in unique_edges
                      if edge[0] in kept_ids and edge[1] in kept_ids]
    omitted_for_nodes = len(unique_edges) - len(endpoint_edges)
    kept_edges = endpoint_edges[:max_edges]
    edges = [{"id": f"edge:{index + 1}", "source": source, "target": target,
              "kind": kind, **({"label": label} if label else {})}
             for index, (source, target, kind, label) in enumerate(kept_edges)]
    omitted_edges = omitted_for_nodes + max(0, len(endpoint_edges) - len(edges))

    expected_attempts = sum(attempts_expected.values())
    returned_attempts = len(attempt_by_id)
    total_attempts = _nonnegative_int(ledger_view.get("totalAttempts"))
    if "totalAttempts" not in ledger_view:
        total_attempts = returned_attempts
    missing_attempts = (max(0, expected_attempts - total_attempts)
                        if "totalAttempts" in ledger_view else missing_expected)
    omitted_attempts = max(0, total_attempts - _nonnegative_int(
        ledger_view.get("returnedAttempts", returned_attempts)))
    unknown_recorded = sum(1 for item in attempt_by_id.values()
                           if _integer_or_none(item.get("actualCostMicrousd")) is None)
    observed_actual = sum(_integer_or_none(item.get("actualCostMicrousd")) or 0
                          for item in attempt_by_id.values())
    aggregate_actual = _integer_or_none(ledger_view.get("knownActualMicrousd"))
    known_actual = aggregate_actual if aggregate_actual is not None else observed_actual
    unresolved_count = _nonnegative_int(ledger_view.get("unresolvedCostCount"))
    if "unresolvedCostCount" not in ledger_view:
        unresolved_count = unknown_recorded + missing_attempts
    all_costs_resolved = (unresolved_count == 0 and missing_attempts == 0
                          and (ledger_view.get("allCostsResolved") is True
                               if "allCostsResolved" in ledger_view else unknown_recorded == 0))
    coverage_complete = (ledger_view.get("coverageComplete") is True and missing_attempts == 0
                         if "coverageComplete" in ledger_view else missing_attempts == 0)
    source_truncated = ledger_view.get("truncated") is True or omitted_attempts > 0
    summary = {
        "nodeCount": len(kept_nodes), "edgeCount": len(edges),
        "omittedNodes": omitted_nodes, "omittedEdges": omitted_edges,
        "omittedAttempts": omitted_attempts,
        "attemptCoverage": {"expected": expected_attempts, "recorded": total_attempts,
                            "returned": returned_attempts, "missing": missing_attempts,
                            "complete": coverage_complete},
        "allCostsResolved": all_costs_resolved,
        "knownActualMicrousd": known_actual,
        "knownActualIsPartial": aggregate_actual is None and omitted_attempts > 0,
        "unknownCostAttempts": unresolved_count,
    }
    return {"version": 1, "runId": run_id, "nodes": kept_nodes, "edges": edges,
            "summary": summary, "limitations": list(_LIMITATIONS),
            "truncated": bool(omitted_nodes or omitted_edges or source_truncated)}


def read_only_execution_graph(db_path: str, run_id: str, *,
                              max_nodes: int = DEFAULT_MAX_NODES,
                              max_edges: int = DEFAULT_MAX_EDGES) -> dict[str, Any] | None:
    """Read one status snapshot through SQLite read-only mode and project it.

    This bypasses `ControlStore.__init__`, which performs schema initialization and may
    migrate a database. A single read transaction keeps status and ledger consistent.
    """
    if not isinstance(db_path, str) or not db_path:
        raise ValueError("db_path is required.")
    if not _valid_id(run_id):
        raise ValueError("run_id is invalid.")
    path = Path(db_path).expanduser().resolve()
    uri = path.as_uri() + "?mode=ro"
    db = sqlite3.connect(uri, uri=True, timeout=2.0, isolation_level=None)
    db.row_factory = sqlite3.Row
    store = ControlStore.__new__(ControlStore)
    store._db = db
    store._lock = threading.RLock()
    try:
        db.execute("PRAGMA query_only=ON")
        db.execute("BEGIN")
        status = store.status(run_id)
        if status is None:
            db.execute("ROLLBACK")
            return None
        ledger = status.get("ledger", {})
        result = project_execution_graph(status, ledger,
                                         max_nodes=max_nodes, max_edges=max_edges)
        db.execute("COMMIT")
        return result
    except sqlite3.Error:
        if db.in_transaction:
            db.execute("ROLLBACK")
        raise
    finally:
        db.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Project one control-store run as a bounded explanation graph.")
    parser.add_argument("dbPath", nargs="?", help="Path to the existing ControlStore SQLite database (read only).")
    parser.add_argument("runId", nargs="?", help="Run identifier to project.")
    parser.add_argument("--max-nodes", type=int, default=DEFAULT_MAX_NODES)
    parser.add_argument("--max-edges", type=int, default=DEFAULT_MAX_EDGES)
    args = parser.parse_args(argv)
    try:
        db_path, run_id = args.dbPath, args.runId
        if db_path is None and run_id is None:
            raw = sys.stdin.read(16_385)
            if len(raw) > 16_384:
                raise ValueError("stdin request too large")
            request = json.loads(raw)
            if not isinstance(request, dict) or set(request) != {"dbPath", "runId"}:
                raise ValueError("stdin request must contain dbPath and runId")
            db_path, run_id = request["dbPath"], request["runId"]
        if db_path is None or run_id is None:
            raise ValueError("both dbPath and runId are required")
        graph = read_only_execution_graph(db_path, run_id,
                                          max_nodes=args.max_nodes, max_edges=args.max_edges)
        if graph is None:
            print(json.dumps({"error": "run not found"}, separators=(",", ":")))
            return 1
        print(json.dumps(graph, ensure_ascii=False, allow_nan=False, separators=(",", ":")))
        return 0
    except (ValueError, TypeError, json.JSONDecodeError, sqlite3.Error):
        # Do not serialize database paths or untrusted exception text.
        print(json.dumps({"error": "execution graph could not be read"}, separators=(",", ":")))
        return 2


def _node(node_id: str, kind: str, label: str, *, status: Any = None,
          reserved: int | None = None, actual: int | None = None,
          details: Mapping[str, Any] | None = None,
          explanations: list[str] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"id": node_id, "kind": kind, "label": label[:512]}
    if isinstance(status, str) and len(status) <= 128:
        result["status"] = status
    if reserved is not None:
        result["reservedMicrousd"] = reserved
    if actual is not None:
        result["actualMicrousd"] = actual
    if details:
        result["details"] = dict(details)
    result["explanations"] = list(explanations or [])
    return result


def _task_details(task: Mapping[str, Any]) -> dict[str, Any]:
    fields = ("executionClass", "tool", "resource", "attempts", "maxAttempts",
              "leaseExpiresAt", "claimedAt", "completedAt")
    result = {key: task[key] for key in fields if key in task and _json_scalar(task.get(key))}
    for key in ("requireResourceCapacity", "resourceConcurrencyLimit"):
        if key in task and _json_scalar(task[key]):
            result[key] = task[key]
    capacity = task.get("resourceCapacity")
    if isinstance(capacity, Mapping):
        result["resourceCapacity"] = {key: capacity[key] for key in
            ("globalLimit", "globalOccupied", "runOccupied", "runLimit", "effectiveLimit", "availableCount")
            if key in capacity and (capacity[key] is None or type(capacity[key]) is int)}
    return result


def _specialist_access_details(payload: Any, contract_id: str) -> dict[str, Any]:
    """Return only bounded scalar provenance from the explicit contract binding."""
    if not isinstance(payload, Mapping):
        return {}
    binding = payload.get("specialistAccess")
    if not isinstance(binding, Mapping) or binding.get("contractId") != contract_id:
        return {}
    scalar_fields = ("contractId", "designId", "specialistId", "nodeId", "action", "audience",
                     "purpose", "modelId", "adapterId", "toolId", "resourceId")
    result = {key: value for key in scalar_fields
              if isinstance((value := binding.get(key)), str) and 0 < len(value) <= 256 and "\x00" not in value}
    for key in ("designSha256", "skillBindingsSha256", "mcpBindingsSha256", "executionInputSha256"):
        value = binding.get(key)
        if isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value):
            result[key] = value
    return result


def _task_explanations(task: Mapping[str, Any], tasks: Any) -> list[str]:
    explanations: list[str] = []
    status = task.get("status")
    capacity = task.get("resourceCapacity")
    if task.get("requireResourceCapacity") is True:
        explanations.append("An administrator-configured exact resource cap is required before this task can be claimed.")
    if isinstance(capacity, Mapping) and capacity.get("globalLimit") is not None:
        explanations.append("Capacity is a persisted database snapshot; ambiguous external effects retain slots until reconciliation.")
        if status == "pending" and capacity.get("availableCount") == 0:
            explanations.append("No resource slot was available at this snapshot; the claim transaction checks capacity again.")

    if status == "blocked":
        explanations.append("Task is blocked by a failed or cancelled dependency.")
    elif status == "needs_reconciliation":
        explanations.append("Task needs cost or outcome reconciliation before it can be treated as settled.")
    elif status == "failed":
        explanations.append("Task is failed; detailed error text is intentionally omitted.")
    elif status == "cancelled":
        explanations.append("Task was cancelled.")
    deps = task.get("dependencies", ())
    status_by_key = {item.get("id"): item.get("status") for item in tasks
                     if isinstance(item, Mapping) and isinstance(item.get("id"), str)}
    if isinstance(deps, (list, tuple)):
        waiting = [dep for dep in deps if status_by_key.get(dep) != "succeeded"]
        if waiting and status == "pending":
            explanations.append("Waiting for dependency task(s): " + ", ".join(str(dep)[:128] for dep in waiting[:20]) + ".")
    return explanations


def _dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    indexes: dict[str, int] = {}
    for node in nodes:
        node_id = node["id"]
        if node_id not in indexes:
            indexes[node_id] = len(result)
            result.append(node)
    return result


def _sequence(value: Any, label: str) -> None:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} must be a list or tuple.")


def _valid_id(value: Any) -> bool:
    return isinstance(value, str) and 0 < len(value) <= MAX_ID_LENGTH and "\x00" not in value


def _integer_or_none(value: Any) -> int | None:
    return value if type(value) is int and 0 <= value <= 2**63 - 1 else None


def _nonnegative_int(value: Any) -> int:
    return value if type(value) is int and value >= 0 else 0


def _number_or_none(value: Any) -> int | float | None:
    if type(value) is int:
        return value
    if type(value) is float and value == value and abs(value) != float("inf"):
        return value
    return None


def _json_scalar(value: Any) -> bool:
    return value is None or type(value) in (str, int, float, bool)


if __name__ == "__main__":
    raise SystemExit(main())
