#!/usr/bin/env python3
"""Measure the durable SQLite scheduler with deterministic, zero-cost fixture work."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sqlite3
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apexgraphswarm.control import ControlStore, LeaseError  # noqa: E402


DEFAULT_COUNTS = (1, 10, 30, 100, 300)
MAX_LOGICAL_AGENTS = 300


def percentile(values: list[float], fraction: float) -> float:
    """Nearest-rank percentile, stable for small deterministic fixtures."""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) * fraction + 0.999999) - 1)))
    return round(ordered[index], 3)


def fixture_work(payload: dict[str, Any]) -> dict[str, str]:
    """Harmless fixed CPU fixture; no repository writes, tools, or model calls."""
    value = str(payload["value"]).encode("utf-8")
    rounds = int(payload.get("rounds", 64))
    digest = value
    for _ in range(rounds):
        digest = hashlib.sha256(digest).digest()
    return {"fixture": "sha256-chain-v1", "digest": digest.hex()}


def _status(store: ControlStore, run_id: str) -> dict[str, Any]:
    result = store.status(run_id)
    if result is None:
        raise RuntimeError("ControlStore lost the benchmark run.")
    return result


def _run_wave(
    store: ControlStore,
    run_id: str,
    worker_count: int,
    *,
    scenario_id: str,
    phase: str,
    submitted_at: float,
    task_delay_ms: int,
    stop_after: int | None = None,
) -> dict[str, Any]:
    lock = threading.Lock()
    stopped = threading.Event()
    active = 0
    peak_active = 0
    completed = 0
    errors: list[str] = []
    queue_ms: list[float] = []
    service_ms: list[float] = []
    end_to_end_ms: list[float] = []
    completed_ids: list[str] = []

    def worker(index: int) -> None:
        nonlocal active, peak_active, completed
        worker_id = f"bench-{scenario_id}-{phase}-{index:03d}"
        while not stopped.is_set():
            try:
                lease = store.claim(run_id, worker_id, lease_seconds=30)
            except Exception as exc:  # benchmark reports the fault in its artifact
                with lock:
                    errors.append(f"claim: {type(exc).__name__}: {exc}")
                stopped.set()
                return
            if lease is None:
                state = _status(store, run_id)
                if all(task["status"] in {"succeeded", "failed", "cancelled"} for task in state["tasks"]):
                    return
                time.sleep(0.001)
                continue

            claim_time = time.perf_counter()
            task_id = lease["taskId"]
            with lock:
                active += 1
                peak_active = max(peak_active, active)
                queue_ms.append((claim_time - submitted_at) * 1000)

            service_start = time.perf_counter()
            try:
                result = fixture_work(lease["payload"])
                if task_delay_ms:
                    # A fixed local wait makes overlap observable; it is not model latency.
                    time.sleep(task_delay_ms / 1000)
                service_end = time.perf_counter()
                store.complete(task_id, lease["leaseToken"], result, actual_cost_microusd=0)
                completed_at = time.perf_counter()
                with lock:
                    service_ms.append((service_end - service_start) * 1000)
                    end_to_end_ms.append((completed_at - submitted_at) * 1000)
                    completed_ids.append(task_id)
                    completed += 1
                    active -= 1
                    if stop_after is not None and completed >= stop_after:
                        stopped.set()
            except Exception as exc:  # pragma: no cover - surfaced as artifact failure
                with lock:
                    errors.append(f"complete: {type(exc).__name__}: {exc}")
                    active -= 1
                stopped.set()

    threads = [threading.Thread(target=worker, args=(index,), name=f"apex-bench-{index}", daemon=False)
               for index in range(max(1, worker_count))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return {
        "completed": completed,
        "observedPeakActive": peak_active,
        "queueMs": queue_ms,
        "serviceMs": service_ms,
        "endToEndMs": end_to_end_ms,
        "completedIds": completed_ids,
        "errors": errors,
    }


def _restart_recovery_check(db_path: Path, scenario_id: str) -> dict[str, Any]:
    """Prove persistence and stale-lease fencing across store reopen, using fake time."""
    clock_value = [time.time()]
    clock = lambda: clock_value[0]
    run_id = ""
    lease: dict[str, Any] | None = None
    with ControlStore(db_path, max_active=1, max_registered_agents=1, clock=clock) as store:
        created = store.create_run({
            "version": 1,
            "agents": [{"id": "recovery-agent"}],
            "tasks": [{"id": "recovery-task", "agentId": "recovery-agent", "dependencies": [],
                       "payload": {"value": scenario_id, "rounds": 1}, "executionClass": "fixture",
                       "reservedCostMicrousd": 0,
                       "maxAttempts": 2}],
        }, idempotency_key=f"local-bench-recovery-{scenario_id}", budget_microusd=0)
        run_id = created["run"]["id"]
        lease = store.claim(run_id, "crash-simulated-worker", lease_seconds=5)
        if lease is None:
            raise RuntimeError("Recovery fixture task was not claimable.")

    # The control process and its SQLite connection are gone. Advance only the
    # injected test clock; do not sleep or write future timestamps to the host.
    clock_value[0] += 6
    with ControlStore(db_path, max_active=1, max_registered_agents=1, clock=clock) as restarted:
        before = _status(restarted, run_id)
        persisted_running = sum(task["status"] == "running" for task in before["tasks"])
        recovered = restarted.recover_expired()
        stale_fenced = False
        try:
            restarted.complete(lease["taskId"], lease["leaseToken"], {"wrong": True}, actual_cost_microusd=0)
        except LeaseError:
            stale_fenced = True
        second = restarted.claim(run_id, "after-restart-worker", lease_seconds=5)
        if second is None:
            raise RuntimeError("Recovered task was not claimable after restart.")
        restarted.complete(second["taskId"], second["leaseToken"], fixture_work(second["payload"]), actual_cost_microusd=0)
        final = _status(restarted, run_id)
        return {
            "reopened": True,
            "persistedRunning": persisted_running,
            "leaseRecoveries": recovered["requeued"],
            "staleLeaseFenced": stale_fenced,
            "completedAfterRestart": sum(task["status"] == "succeeded" for task in final["tasks"]),
            "costConsistent": final["run"]["spentMicrousd"] == 0 and final["run"]["budgetExceeded"] is False,
        }


def run_scenario(agent_count: int, *, workers_cap: int, tasks_per_agent: int,
                 task_delay_ms: int, db_dir: Path, seed: int) -> dict[str, Any]:
    if not 1 <= agent_count <= MAX_LOGICAL_AGENTS:
        raise ValueError("logical agent count must be from 1 through 300")
    worker_limit = min(agent_count, workers_cap)
    scenario_id = f"a{agent_count}-s{seed}"
    db_path = db_dir / f"{scenario_id}.sqlite3"
    recovery_path = db_dir / f"{scenario_id}-recovery.sqlite3"
    if db_path.exists():
        db_path.unlink()
    if recovery_path.exists():
        recovery_path.unlink()

    agents = [{"id": f"agent-{index:03d}", "name": f"Fixture agent {index:03d}"}
              for index in range(agent_count)]
    tasks = [{"id": f"task-{agent['id']}-{task_index:02d}", "agentId": agent["id"],
              "dependencies": [], "executionClass": "fixture",
              "payload": {"value": f"seed:{seed}:{agent['id']}:{task_index}", "rounds": 64},
              "reservedCostMicrousd": 0, "maxAttempts": 1}
             for agent in agents for task_index in range(tasks_per_agent)]
    plan = {"version": 1, "agents": agents, "tasks": tasks}
    run_budget = 0
    submitted_at = time.perf_counter()
    started_at = submitted_at
    phase_one_complete = 0
    phase_one_peak = 0
    phase_one_queue: list[float] = []
    phase_one_service: list[float] = []
    phase_one_total: list[float] = []
    reopen_verified = False
    errors: list[str] = []

    with ControlStore(db_path, max_active=worker_limit,
                      max_registered_agents=MAX_LOGICAL_AGENTS,
                      max_run_cost_microusd=max(1, run_budget)) as store:
        created = store.create_run(plan, idempotency_key=f"local-benchmark-{scenario_id}",
                                   budget_microusd=run_budget)
        run_id = created["run"]["id"]
        # Complete a first slice, then close and reopen the actual SQLite-backed
        # queue before the rest of the deterministic fixture is processed.
        first_target = max(1, len(tasks) // 4)
        first = _run_wave(store, run_id, min(worker_limit, 4), scenario_id=scenario_id,
                          phase="before-restart", submitted_at=submitted_at,
                          task_delay_ms=task_delay_ms, stop_after=first_target)
        phase_one_complete = first["completed"]
        phase_one_peak = first["observedPeakActive"]
        phase_one_queue.extend(first["queueMs"])
        phase_one_service.extend(first["serviceMs"])
        phase_one_total.extend(first["endToEndMs"])
        errors.extend(first["errors"])

    # Connection/process-level restart: instantiate a new store over the same DB.
    with ControlStore(db_path, max_active=worker_limit,
                      max_registered_agents=MAX_LOGICAL_AGENTS,
                      max_run_cost_microusd=max(1, run_budget)) as restarted:
        after_open = _status(restarted, run_id)
        persisted_count = sum(task["status"] == "succeeded" for task in after_open["tasks"])
        reopen_verified = persisted_count == phase_one_complete
        rest = _run_wave(restarted, run_id, worker_limit, scenario_id=scenario_id,
                         phase="after-restart", submitted_at=submitted_at,
                         task_delay_ms=task_delay_ms)
        errors.extend(rest["errors"])
        final = _status(restarted, run_id)
        events = final["events"]
        completed_events = sum(event["type"] == "task.completed" for event in events)
        successful_tasks = [task for task in final["tasks"] if task["status"] == "succeeded"]
        total_elapsed_ms = (time.perf_counter() - started_at) * 1000
        unique_completed = len({task["taskId"] for task in successful_tasks})
        duplicate_events = max(0, completed_events - unique_completed)
        completed = len(successful_tasks)
        accounting = final["run"]
        reserved = sum(task["reservedCostMicrousd"] for task in final["tasks"])
        actual = sum(task["actualCostMicrousd"] for task in final["tasks"])
        queue_values = phase_one_queue + rest["queueMs"]
        service_values = phase_one_service + rest["serviceMs"]
        total_values = phase_one_total + rest["endToEndMs"]
        recovery = _restart_recovery_check(recovery_path, scenario_id)
        return {
            "logicalAgents": agent_count,
            "activeWorkerLimit": worker_limit,
            "observedPeakActive": max(phase_one_peak, rest["observedPeakActive"]),
            "taskCount": len(tasks),
            "completed": completed,
            "failed": len(final["tasks"]) - completed,
            "throughputTasksPerSecond": round(completed / (total_elapsed_ms / 1000), 3) if total_elapsed_ms else 0,
            "elapsedMs": round(total_elapsed_ms, 3),
            "latencyMs": {
                "queueP50": percentile(queue_values, 0.50), "queueP95": percentile(queue_values, 0.95),
                "serviceP50": percentile(service_values, 0.50), "serviceP95": percentile(service_values, 0.95),
                "endToEndP50": percentile(total_values, 0.50), "endToEndP95": percentile(total_values, 0.95),
            },
            "duplicateCompletions": duplicate_events,
            "restart": {"reopened": reopen_verified, "persistedCompleted": persisted_count,
                        "leaseRecoveries": recovery["leaseRecoveries"], "staleLeaseFenced": recovery["staleLeaseFenced"],
                        "recoveryTaskCompleted": recovery["completedAfterRestart"]},
            "cost": {"reservedMicrousd": reserved, "actualMicrousd": actual,
                     "budgetMicrousd": accounting["budgetMicrousd"],
                     "spentMicrousd": accounting["spentMicrousd"],
                     "consistent": reserved == 0 and actual == 0 and accounting["spentMicrousd"] == 0
                     and accounting["budgetExceeded"] is False,
                     "providerCalls": 0},
            "events": {"taskCompleted": completed_events,
                       "taskLeaseExpired": sum(event["type"] == "task.lease_expired" for event in events),
                       "taskRequeued": sum(event["type"] == "task.requeued" for event in events)},
            "errors": errors,
        }


def build_artifact(*, counts: tuple[int, ...] = DEFAULT_COUNTS, workers_cap: int = 32,
                   tasks_per_agent: int = 2, task_delay_ms: int = 2, seed: int = 20260927,
                   db_dir: Path | None = None) -> dict[str, Any]:
    if not 1 <= workers_cap <= 64:
        raise ValueError("workers cap must be between 1 and the ControlStore maximum of 64")
    if not 1 <= tasks_per_agent <= 10:
        raise ValueError("tasks per agent must be between 1 and 10")
    if not 0 <= task_delay_ms <= 100:
        raise ValueError("task delay must be between 0 and 100 milliseconds")
    if not counts or any(type(count) is not int or not 1 <= count <= MAX_LOGICAL_AGENTS for count in counts):
        raise ValueError("each logical agent count must be from 1 through 300")

    temporary = tempfile.TemporaryDirectory(prefix="apex-swarm-bench-") if db_dir is None else None
    directory = Path(temporary.name) if temporary else db_dir
    directory.mkdir(parents=True, exist_ok=True)
    try:
        scenarios = [run_scenario(count, workers_cap=workers_cap, tasks_per_agent=tasks_per_agent,
                                  task_delay_ms=task_delay_ms, db_dir=directory, seed=seed)
                     for count in counts]
    finally:
        if temporary:
            temporary.cleanup()
    script_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {
        "schemaVersion": 1,
        "measuredAt": datetime.now(timezone.utc).isoformat(),
        "classification": "deterministic_local_queue_fixture",
        "note": "Measured with the SQLite ControlStore and deterministic SHA-256 fixture work. No LLM, network, repository mutation, or provider calls. Timing varies by local machine and is not a model-quality result.",
        "provenance": {"controlPlane": "apexgraphswarm.control.ControlStore (SQLite)",
                       "controlSourceSha256": hashlib.sha256((ROOT / "apexgraphswarm" / "control.py").read_bytes()).hexdigest(),
                       "scriptSha256": script_hash, "python": platform.python_version(),
                       "sqlite": sqlite3.sqlite_version, "platform": platform.platform(),
                       "machine": platform.machine()},
        "config": {"logicalAgentCounts": list(counts), "activeWorkerCap": workers_cap,
                   "tasksPerLogicalAgent": tasks_per_agent,
                   "fixture": f"sha256-chain-v1-64 rounds + {task_delay_ms}ms fixed local wait",
                   "seed": seed, "budget": "0 micro-USD known local fixture work", "providerCalls": 0,
                   "restart": "Close and reopen SQLite after first task slice; separately verify expired-lease recovery and stale-token fencing with injected clock."},
        "scenarios": scenarios,
        "proposedTargets": [
            {"label": "Graph correctness", "value": "100% schema-valid and referentially valid on hidden deterministic fixtures", "status": "unmeasured"},
            {"label": "Permission safety", "value": "Zero successful out-of-scope tool actions", "status": "unmeasured"},
            {"label": "Held-out task quality", "value": "Non-inferior to single-agent quality at equal cost", "status": "unmeasured"},
            {"label": "Fault recovery", "value": "At least 99% terminal transitions under fault injection", "status": "unmeasured"},
            {"label": "Live model concurrency", "value": "Not tested by this local fixture; provider limits and cost approval required", "status": "unmeasured"},
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counts", nargs="+", type=int, default=list(DEFAULT_COUNTS))
    parser.add_argument("--workers", type=int, default=32, help="hard cap on Python fixture workers and SQLite leases (max 64)")
    parser.add_argument("--tasks-per-agent", type=int, default=2)
    parser.add_argument("--task-delay-ms", type=int, default=2, help="fixed local fixture wait, not simulated model latency")
    parser.add_argument("--seed", type=int, default=20260927)
    parser.add_argument("--output", type=Path, default=ROOT / "apps" / "web" / "public" / "benchmarks" / "local-swarm.json")
    parser.add_argument("--db-dir", type=Path, help="retain SQLite databases for inspection; temporary and removed by default")
    args = parser.parse_args(argv)
    try:
        artifact = build_artifact(counts=tuple(args.counts), workers_cap=args.workers,
                                  tasks_per_agent=args.tasks_per_agent,
                                  task_delay_ms=args.task_delay_ms, seed=args.seed, db_dir=args.db_dir)
    except Exception as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"artifact": str(args.output), "scenarios": [
        {"logicalAgents": row["logicalAgents"], "activeWorkerLimit": row["activeWorkerLimit"],
         "observedPeakActive": row["observedPeakActive"], "completed": row["completed"],
         "elapsedMs": row["elapsedMs"], "throughputTasksPerSecond": row["throughputTasksPerSecond"],
         "queueP95Ms": row["latencyMs"]["queueP95"], "duplicateCompletions": row["duplicateCompletions"],
         "restartVerified": row["restart"]["reopened"], "costConsistent": row["cost"]["consistent"],
         "errors": row["errors"]} for row in artifact["scenarios"]]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
