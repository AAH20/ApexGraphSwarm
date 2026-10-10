"""Reproducible synthetic benchmark for deterministic optimization helpers.

All costs/durations/telemetry in this report are synthetic fixture values. The
script makes no provider/network calls and makes no public benchmark claim.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import platform
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apexgraphswarm.evaluation import evaluate
from apexgraphswarm.hierarchy import METRIC_PROFILES, plan_hierarchy
from apexgraphswarm.optimization import (
    CodeTask, DagTask, EvidenceItem, ModelOption, TelemetrySample,
    plan_waves, recommend_capacity, schedule_dag, select_evidence,
)


REPORT_VERSION = "apexgraphswarm-synthetic-optimization-v2"
ROOT = Path(__file__).resolve().parents[1]


def _timed(fn):
    started = time.perf_counter()
    value = fn()
    return value, (time.perf_counter() - started) * 1000.0


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _attempt(aid: str, candidate: str, task: str, cost: int) -> dict[str, Any]:
    return {
        "attemptId": aid, "candidateId": candidate, "taskId": task,
        "evaluatorId": "synthetic-exact-fixture", "evaluatorVersion": "1",
        "attemptIndex": 1, "status": "succeeded", "elapsedMs": 25,
        "actualCostMicrousd": cost, "qualityScore": 1.0, "accepted": True,
        "policyViolations": 0,
        "metricScores": {name: 0.9 for name in METRIC_PROFILES["coding"]["weights"]},
    }


def _paired_demo(task_count: int = 64) -> dict[str, Any]:
    """Show the promotion gate on paired deterministic data, not live results."""
    train_ids = ["train-%04d" % i for i in range(128)]
    held_ids = ["held-%05d" % i for i in range(max(task_count, 128))]
    sealed_ids = ["sealed-a"]
    task_ids = train_ids + held_ids
    candidates = [
        {"candidateId": "baseline", "version": "fixture-1", "config": {"capacity": 1}},
        {"candidateId": "candidate", "version": "fixture-1", "config": {"capacity": 2}},
    ]
    attempts = []
    for cid, cost in (("baseline", 50), ("candidate", 20)):
        for task_id in task_ids:
            attempts.append(_attempt(cid + ":" + task_id, cid, task_id, cost))
    payload = {
        "suite": {
            "suiteId": "synthetic-paired-demo", "suiteVersion": "1",
            "tasksetId": "synthetic-fixtures", "tasksetVersion": "1",
            "evaluatorId": "synthetic-exact-fixture", "evaluatorVersion": "1",
            "trainTaskIds": train_ids, "heldoutTaskIds": held_ids,
            "sealedTaskIds": sealed_ids, "qualityFloor": 0.8,
            "maxLatencyMs": 1_000, "maxPolicyViolations": 0,
            "confidenceAlpha": 0.05, "maxAttemptsPerTask": 1,
            "maxCostMicrousdPerTask": 100,
            "costCapEnforcementId": "synthetic-fixture-cap-v1",
            "metricProfile": {"profileId": "coding", "minimumWeightedScore": 0.7,
                              "maxScoreRegression": 0.02},
        },
        "candidates": candidates, "attempts": attempts,
        "baselineCandidateId": "baseline",
    }
    report = evaluate(payload)
    decision = report["promotionDecision"]
    return {
        "synthetic": True, "taskCountHeldout": len(held_ids),
        "baselineCandidateId": "baseline",
        "selectedCandidateId": report["trainingSelection"]["selectedCandidateId"],
        "selectedOn": "training only", "sealedSetUsedForSelection": False,
        "promotionDecision": decision,
        "heldoutSummary": {
            cid: {key: report["candidateReports"][cid]["heldout"][key]
                  for key in ("taskCount", "attemptCount", "acceptedCount", "acceptedRateLowerBound",
                              "knownActualCostMicrousd", "unknownCostAttemptCount", "costPerAcceptedMicrousd",
                              "hardGatesPassed", "gateFailures")}
            for cid in ("baseline", "candidate")
        },
        "weightedMetricSummary": {
            cid: report["candidateReports"][cid]["heldout"]["metricProfileEvaluation"]
            for cid in ("baseline", "candidate")
        },
    }


def _hierarchy_scale_case(task_count: int) -> dict[str, Any]:
    """Measure planner overhead for a synthetic plan; this is not agent execution."""
    profile = METRIC_PROFILES["coding"]["weights"]
    tasks = []
    for index in range(task_count):
        tasks.append({
            "id": "task-%04d" % index,
            "family": "synthetic-review",
            "dependencies": ["task-%04d" % (index - 1)] if index else [],
            "requiredCapabilities": ["fixture-work"], "requiredActions": ["read"],
            "resourceScope": "repo:synthetic", "dataBoundary": "public-fixture",
            "estimatedCostMicrousd": 1, "estimatedLatencyMs": 10,
        })
    agents = [
        {"id": "leader-fixture", "role": "leader", "profileIds": ["coding"],
         "capabilities": ["coordination"], "authorizedActions": ["read"],
         "authorizationGrantId": "benchmark-grant-leader", "resourceScopes": ["repo:synthetic"],
         "dataBoundaries": ["public-fixture"], "metricScores": {name: 0.9 for name in profile}},
        {"id": "worker-fixture", "role": "worker", "profileIds": ["coding"],
         "capabilities": ["fixture-work"], "authorizedActions": ["read"],
         "authorizationGrantId": "benchmark-grant-worker", "resourceScopes": ["repo:synthetic"],
         "dataBoundaries": ["public-fixture"], "maxAssignments": task_count,
         "metricScores": {name: 0.9 for name in profile}},
    ]
    payload = {"profileId": "coding", "tasks": tasks, "agents": agents,
               "limits": {"budgetMicrousd": task_count + 1, "deadlineMs": task_count * 10 + 1,
                           "maxClusterTasks": 16, "maxClusters": 32}}
    result, elapsed_ms = _timed(lambda: plan_hierarchy(payload))
    return {"inputTasks": task_count, "elapsedMs": elapsed_ms,
            "result": {key: result[key] for key in (
                "schemaVersion", "status", "clusterCount", "estimatedCriticalPathMs",
                "estimatedTotalCostMicrousd", "unknownCostTaskIds", "blockers")},
            "synthetic": True, "providerCalls": 0}


def benchmark_report() -> dict[str, Any]:
    """Return a JSON-friendly report with locally measured fixture timings."""
    options = (
        ModelOption("fixture-fast", 8, 1.25),
        ModelOption("fixture-slow", 3, 2.0),
    )
    tasks = (
        DagTask("parse", (), 1.25, options),
        DagTask("map-a", ("parse",), 1.5, options),
        DagTask("map-b", ("parse",), 1.0, options),
        DagTask("join", ("map-a", "map-b"), 1.25, options),
    )
    schedule, schedule_ms = _timed(lambda: schedule_dag(
        tasks, budget_microusd=32, capacities={"fixture-fast": 2, "fixture-slow": 1},
        deadline_seconds=10.0,
    ))

    evidence_items = (
        EvidenceItem("source-a", ("dependency", "entrypoint"), 80, {"dependency": 2.0}),
        EvidenceItem("source-b", ("entrypoint", "risk"), 60, {"risk": 2.0}),
        EvidenceItem("tests", ("risk", "verification"), 70, {"verification": 3.0}),
    )
    evidence, evidence_ms = _timed(lambda: select_evidence(evidence_items, token_budget=150))

    code_tasks = (
        CodeTask("api", (), ("schema.json",), ("api.py",)),
        CodeTask("tests", (), ("api.py",), ("test_api.py",)),
        CodeTask("docs", (), (), ("README.md",)),
    )
    waves, waves_ms = _timed(lambda: plan_waves(code_tasks))

    telemetry = (
        TelemetrySample(1, 8.0, 0.10, 0.44, 0),
        TelemetrySample(2, 13.0, 0.18, 0.71, 1),
        TelemetrySample(4, 19.0, 0.46, 0.91, 5),
    )
    capacity, capacity_ms = _timed(lambda: recommend_capacity(telemetry, target_utilization=0.75))
    paired, paired_ms = _timed(_paired_demo)
    hierarchy_scale = [_hierarchy_scale_case(size) for size in (4, 32, 128, 200)]
    return {
        "benchmarkId": REPORT_VERSION,
        "fixtureSchema": {"version": "1", "scheduleTasks": len(tasks),
                          "evidenceItems": len(evidence_items), "codingTasks": len(code_tasks),
                          "telemetrySamples": len(telemetry), "pairedHeldoutTasks": 128,
                          "pairedTrainingTasks": 128, "hierarchyPlanTaskSizes": [4, 32, 128, 200]},
        "sourceHashes": {
            "optimization.py": _sha256(ROOT / "apexgraphswarm" / "optimization.py"),
            "evaluation.py": _sha256(ROOT / "apexgraphswarm" / "evaluation.py"),
            "hierarchy.py": _sha256(ROOT / "apexgraphswarm" / "hierarchy.py"),
            "benchmark_optimization.py": _sha256(Path(__file__).resolve()),
        },
        "measurementType": "local wall-clock measurements of deterministic synthetic fixtures",
        "environment": {"pythonVersion": platform.python_version(), "platform": platform.platform()},
        "providerCalls": 0,
        "costProvenance": "synthetic fixture values; not prices, estimates, or provider usage",
        "cases": [
            {"id": "dag-scheduling", "synthetic": True, "inputTasks": len(tasks),
             "elapsedMs": schedule_ms, "result": asdict(schedule)},
            {"id": "evidence-selection", "synthetic": True, "inputItems": len(evidence_items),
             "elapsedMs": evidence_ms, "result": asdict(evidence)},
            {"id": "file-conflict-waves", "synthetic": True, "inputTasks": len(code_tasks),
             "elapsedMs": waves_ms, "result": asdict(waves)},
            {"id": "capacity-recommendation", "synthetic": True, "inputTelemetrySamples": len(telemetry),
             "elapsedMs": capacity_ms, "result": asdict(capacity)},
            {"id": "paired-promotion-gate", "synthetic": True, "elapsedMs": paired_ms, "result": paired},
            {"id": "hierarchical-planner-scaling", "synthetic": True,
             "measurementType": "local deterministic plan construction only", "sizes": hierarchy_scale},
        ],
        "limits": [
            "Synthetic task graphs, durations, costs, and telemetry are fixtures only.",
            "No model/provider is called; results do not establish production performance.",
            "Task attempts are supplied deterministic evaluator records, not measured agent work.",
            "Hierarchy scale cases measure planner construction only, not model calls, active workers, swarm quality or production capacity.",
            "Sealed tasks are never used for training selection or promotion selection.",
        ],
    }


def main() -> int:
    print(json.dumps(benchmark_report(), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
