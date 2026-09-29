#!/usr/bin/env python3
"""CI benchmark runner for ApexGraphSwarm.

Runs all benchmark scripts, collects results, compares against baseline,
and generates a performance report. Exits non-zero if regressions exceed
configured thresholds.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
BASELINE_PATH = REPORTS_DIR / "baseline.json"
REPORT_PATH = REPORTS_DIR / "ci-benchmark-report.json"

# Regression thresholds (percentage increase that triggers failure)
THRESHOLDS = {
    "throughputTasksPerSecond": -20.0,  # 20% throughput drop = failure
    "elapsedMs": 50.0,  # 50% time increase = failure
    "queueP95Ms": 100.0,  # 100% latency increase = failure
    "peakPythonAllocationBytes": 50.0,  # 50% memory increase = failure
    "buildMs": 50.0,  # 50% build time increase = failure
    "layoutMs": 50.0,  # 50% layout time increase = failure
}


def run_command(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a command and return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return result.returncode, result.stdout, result.stderr


def run_swarm_benchmark() -> dict[str, Any]:
    """Run the swarm queue benchmark."""
    print("Running swarm queue benchmark...")
    code, stdout, stderr = run_command([
        sys.executable, "scripts/benchmark_swarm.py",
        "--output", str(REPORTS_DIR / "ci-swarm.json"),
    ])
    if code != 0:
        print(f"  FAILED: {stderr}", file=sys.stderr)
        return {"status": "fail", "error": stderr}
    artifact = json.loads((REPORTS_DIR / "ci-swarm.json").read_text())
    return {
        "status": "pass",
        "scenarios": artifact["scenarios"],
        "config": artifact["config"],
    }


def run_optimization_benchmark() -> dict[str, Any]:
    """Run the optimization benchmark."""
    print("Running optimization benchmark...")
    code, stdout, stderr = run_command([
        sys.executable, "scripts/benchmark_optimization.py",
    ])
    if code != 0:
        print(f"  FAILED: {stderr}", file=sys.stderr)
        return {"status": "fail", "error": stderr}
    report = json.loads(stdout)
    return {
        "status": "pass",
        "cases": report["cases"],
    }


def run_analytics_benchmark() -> dict[str, Any]:
    """Run the analytics benchmark."""
    print("Running analytics benchmark...")
    code, stdout, stderr = run_command([
        sys.executable, "scripts/benchmark_analytics.py",
    ])
    if code != 0:
        print(f"  FAILED: {stderr}", file=sys.stderr)
        return {"status": "fail", "error": stderr}
    return {
        "status": "pass",
        "result": json.loads(stdout),
    }


def run_graph_benchmark() -> dict[str, Any]:
    """Run the graph rendering benchmark."""
    print("Running graph rendering benchmark...")
    script = ROOT / "apps/web/scripts/graph-benchmark.mjs"
    if not script.exists():
        return {"status": "skip", "reason": "graph-benchmark.mjs not found"}
    code, stdout, stderr = run_command(["node", str(script)])
    if code != 0:
        print(f"  FAILED: {stderr}", file=sys.stderr)
        return {"status": "fail", "error": stderr}
    return {
        "status": "pass",
        "result": json.loads(stdout),
    }


def run_python_tests() -> dict[str, Any]:
    """Run Python unit tests."""
    print("Running Python unit tests...")
    code, stdout, stderr = run_command([
        sys.executable, "-m", "unittest", "discover", "tests",
    ])
    # Parse test output
    lines = stdout.strip().split("\n")
    summary_line = lines[-1] if lines else ""
    return {
        "status": "pass" if code == 0 else "fail",
        "output": stdout,
        "summary": summary_line,
    }


def run_web_tests() -> dict[str, Any]:
    """Run web tests."""
    print("Running web tests...")
    package_json = ROOT / "apps/web/package.json"
    if not package_json.exists():
        return {"status": "skip", "reason": "apps/web/package.json not found"}
    code, stdout, stderr = run_command(
        ["npm", "--prefix", "apps/web", "test"],
    )
    return {
        "status": "pass" if code == 0 else "fail",
        "output": stdout[-2000:] if len(stdout) > 2000 else stdout,
    }


def compare_scenarios(
    current: list[dict[str, Any]],
    baseline: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compare current scenarios against baseline."""
    regressions = []
    baseline_map = {s["logicalAgents"]: s for s in baseline}

    for scenario in current:
        agents = scenario["logicalAgents"]
        base = baseline_map.get(agents)
        if not base:
            continue

        # Check throughput
        curr_tps = scenario.get("throughputTasksPerSecond", 0)
        base_tps = base.get("throughputTasksPerSecond", 0)
        if base_tps > 0:
            change_pct = ((curr_tps - base_tps) / base_tps) * 100
            if change_pct < THRESHOLDS["throughputTasksPerSecond"]:
                regressions.append({
                    "scenario": f"{agents} agents",
                    "metric": "throughputTasksPerSecond",
                    "baseline": base_tps,
                    "current": curr_tps,
                    "changePercent": round(change_pct, 2),
                    "threshold": THRESHOLDS["throughputTasksPerSecond"],
                })

        # Check elapsed time
        curr_elapsed = scenario.get("elapsedMs", 0)
        base_elapsed = base.get("elapsedMs", 0)
        if base_elapsed > 0:
            change_pct = ((curr_elapsed - base_elapsed) / base_elapsed) * 100
            if change_pct > THRESHOLDS["elapsedMs"]:
                regressions.append({
                    "scenario": f"{agents} agents",
                    "metric": "elapsedMs",
                    "baseline": base_elapsed,
                    "current": curr_elapsed,
                    "changePercent": round(change_pct, 2),
                    "threshold": THRESHOLDS["elapsedMs"],
                })

        # Check queue P95 latency
        curr_p95 = scenario.get("latencyMs", {}).get("queueP95")
        base_p95 = base.get("latencyMs", {}).get("queueP95")
        if curr_p95 is not None and base_p95 is not None and base_p95 > 0:
            change_pct = ((curr_p95 - base_p95) / base_p95) * 100
            if change_pct > THRESHOLDS["queueP95Ms"]:
                regressions.append({
                    "scenario": f"{agents} agents",
                    "metric": "queueP95Ms",
                    "baseline": base_p95,
                    "current": curr_p95,
                    "changePercent": round(change_pct, 2),
                    "threshold": THRESHOLDS["queueP95Ms"],
                })

    return regressions


def compare_analytics(
    current: dict[str, Any],
    baseline: dict[str, Any],
) -> list[dict[str, Any]]:
    """Compare analytics benchmark against baseline."""
    regressions = []
    base = baseline.get("analytics", {})

    # Check elapsed time
    curr_elapsed = current.get("elapsedSeconds", 0)
    base_elapsed = base.get("elapsedSeconds", 0)
    if base_elapsed > 0:
        change_pct = ((curr_elapsed - base_elapsed) / base_elapsed) * 100
        if change_pct > THRESHOLDS["elapsedMs"]:
            regressions.append({
                "benchmark": "analytics",
                "metric": "elapsedSeconds",
                "baseline": base_elapsed,
                "current": curr_elapsed,
                "changePercent": round(change_pct, 2),
                "threshold": THRESHOLDS["elapsedMs"],
            })

    # Check memory
    curr_mem = current.get("peakPythonAllocationBytes", 0)
    base_mem = base.get("peakPythonAllocationBytes", 0)
    if base_mem > 0:
        change_pct = ((curr_mem - base_mem) / base_mem) * 100
        if change_pct > THRESHOLDS["peakPythonAllocationBytes"]:
            regressions.append({
                "benchmark": "analytics",
                "metric": "peakPythonAllocationBytes",
                "baseline": base_mem,
                "current": curr_mem,
                "changePercent": round(change_pct, 2),
                "threshold": THRESHOLDS["peakPythonAllocationBytes"],
            })

    return regressions


def compare_graph(
    current: dict[str, Any],
    baseline: dict[str, Any],
) -> list[dict[str, Any]]:
    """Compare graph benchmark against baseline."""
    regressions = []
    base = baseline.get("graphRendering", {})

    for metric in ("buildMs", "layoutMs"):
        curr_val = current.get(metric, 0)
        base_val = base.get(metric, 0)
        if base_val > 0:
            change_pct = ((curr_val - base_val) / base_val) * 100
            if change_pct > THRESHOLDS[metric]:
                regressions.append({
                    "benchmark": "graphRendering",
                    "metric": metric,
                    "baseline": base_val,
                    "current": curr_val,
                    "changePercent": round(change_pct, 2),
                    "threshold": THRESHOLDS[metric],
                })

    return regressions


def generate_report(
    results: dict[str, Any],
    regressions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate the final benchmark report."""
    return {
        "schemaVersion": 1,
        "measuredAt": datetime.now(timezone.utc).isoformat(),
        "project": "ApexGraphSwarm",
        "environment": {
            "python": sys.version.split()[0],
            "platform": sys.platform,
            "ci": os.environ.get("CI", "false"),
            "githubRunId": os.environ.get("GITHUB_RUN_ID"),
            "githubSha": os.environ.get("GITHUB_SHA"),
            "githubRef": os.environ.get("GITHUB_REF"),
        },
        "benchmarks": results,
        "regressions": regressions,
        "regressionThresholds": THRESHOLDS,
        "status": "fail" if regressions else "pass",
    }


def main() -> int:
    """Run all benchmarks and generate report."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load baseline
    baseline = {}
    if BASELINE_PATH.exists():
        baseline = json.loads(BASELINE_PATH.read_text())
        print(f"Loaded baseline from {BASELINE_PATH}")
    else:
        print("WARNING: No baseline found, regression checks will be limited")

    # Run benchmarks
    results = {
        "pythonTests": run_python_tests(),
        "webTests": run_web_tests(),
        "swarmQueue": run_swarm_benchmark(),
        "optimization": run_optimization_benchmark(),
        "analytics": run_analytics_benchmark(),
        "graphRendering": run_graph_benchmark(),
    }

    # Compare against baseline
    regressions: list[dict[str, Any]] = []

    if baseline.get("benchmarks", {}).get("swarmQueue", {}).get("scenarios"):
        swarm_current = results.get("swarmQueue", {}).get("scenarios", [])
        swarm_baseline = baseline["benchmarks"]["swarmQueue"]["scenarios"]
        regressions.extend(compare_scenarios(swarm_current, swarm_baseline))

    if baseline.get("benchmarks", {}).get("analytics"):
        analytics_current = results.get("analytics", {}).get("result", {})
        regressions.extend(compare_analytics(analytics_current, baseline["benchmarks"]))

    if baseline.get("benchmarks", {}).get("graphRendering"):
        graph_current = results.get("graphRendering", {}).get("result", {})
        regressions.extend(compare_graph(graph_current, baseline["benchmarks"]))

    # Generate report
    report = generate_report(results, regressions)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")

    # Print summary
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    for name, result in results.items():
        status = result.get("status", "unknown")
        icon = "✓" if status == "pass" else "✗" if status == "fail" else "○"
        print(f"  {icon} {name}: {status}")

    if regressions:
        print(f"\n  ⚠ {len(regressions)} performance regression(s) detected:")
        for reg in regressions:
            print(f"    - {reg.get('scenario', reg.get('benchmark'))}: "
                  f"{reg['metric']} {reg['changePercent']:+.1f}% "
                  f"(threshold: {reg['threshold']:+.1f}%)")
        print(f"\nReport saved to {REPORT_PATH}")
        return 1
    else:
        print("\n  ✓ No performance regressions detected")
        print(f"\nReport saved to {REPORT_PATH}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
