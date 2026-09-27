"""Bounded JSON interface to local optimization experiments. No tool execution."""
import json
import sys
from typing import Any

MAX_BYTES = 131072


def dispatch(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("A JSON object is required.")
    action = payload.get("action")
    if action == "benchmark":
        if set(payload) != {"action"}:
            raise ValueError("The benchmark accepts no parameters.")
        from scripts.benchmark_optimization import benchmark_report
        return benchmark_report()
    if action == "telemetry":
        if set(payload) - {"action", "windowSeconds"}:
            raise ValueError("Telemetry accepts only a bounded observation window.")
        window = payload.get("windowSeconds", 2)
        if type(window) not in (int, float) or not 1 <= window <= 5:
            raise ValueError("windowSeconds must be from 1 to 5.")
        import time
        from .inference_telemetry import collect_configured_telemetry, compare_snapshots
        previous = collect_configured_telemetry()
        if previous.snapshot is None:
            return previous.to_dict()
        started = time.monotonic()
        time.sleep(window)
        current = collect_configured_telemetry()
        if current.snapshot is None:
            return current.to_dict()
        elapsed = time.monotonic() - started
        return {"source": "configured_vllm_metrics", "observationWindowSeconds": elapsed,
                "comparison": compare_snapshots(previous.snapshot, current.snapshot, window_seconds=elapsed).to_dict(),
                "modelCalls": 0, "limitations": ["HTTP observation times approximate the server counter window.",
                "KV cache occupancy is not GPU utilization.", "Telemetry does not provision or resize a worker fleet."]}
    if action == "evolve":
        from .evolution import run_evolution
        return run_evolution(payload)
    if action == "compileDelegation":
        if set(payload) - {"action", "problem", "modelBindings", "taskInputs"} or not {"problem", "modelBindings"} <= set(payload):
            raise ValueError("Compile delegation requires problem, modelBindings, and optional taskInputs.")
        from .delegation_plan import compile_delegation_plan
        return compile_delegation_plan(payload["problem"], payload["modelBindings"], task_inputs=payload.get("taskInputs"))
    if action in {"repositoryConflicts", "verifyRepositoryConflicts"}:
        import os
        from pathlib import Path
        from .repository_conflicts import plan_repository_conflicts, verify_repository_conflict_plan
        repo_path = os.environ.get("APEX_REPOSITORY_PATH") or str(Path(__file__).resolve().parent.parent)
        if action == "repositoryConflicts":
            if set(payload) != {"action", "baseRevision", "tasks"}:
                raise ValueError("Repository conflicts requires exactly baseRevision and tasks; the repository path is server-configured.")
            tasks = payload["tasks"]
            if not isinstance(tasks, list) or any(not isinstance(task, dict) or
                    set(task) - {"id", "dependencies", "headRevision", "reads"} or
                    not {"id", "headRevision"} <= set(task) for task in tasks):
                raise ValueError("Repository tasks require id and headRevision, with optional dependencies and declared reads.")
            normalized = [{("head_revision" if key == "headRevision" else key): value
                           for key, value in task.items()} for task in tasks]
            return plan_repository_conflicts(repo_path, payload["baseRevision"], normalized)
        if set(payload) != {"action", "plan"}:
            raise ValueError("Repository conflict verification requires only the saved plan.")
        return verify_repository_conflict_plan(repo_path, payload["plan"])
    if action == "evaluate":
        from .evaluation import evaluate
        return evaluate({key: value for key, value in payload.items() if key != "action"})
    if action in {"schedule", "evidence", "waves", "capacity"}:
        from .optimization import optimize
        return optimize(payload)
    raise ValueError("Choose schedule, evidence, waves, capacity, evaluate, evolve, compileDelegation, telemetry or benchmark.")


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("Request exceeds 128 KiB.")
        payload = json.loads(raw, parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite numbers are not accepted.")))
        result = dispatch(payload)
        print(json.dumps(result, allow_nan=False))
        return 0
    except (ValueError, TypeError, KeyError, OverflowError) as error:
        print(json.dumps({"error": str(error)[:300]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
