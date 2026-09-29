"""Example 57: Advanced - custom metrics and reporting.

Define custom metrics and generate detailed reports.
"""
from apexgraphswarm.analytics import build_analytics
from datetime import datetime, timezone
import json

now = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)

# Generate comprehensive test data
events = []
for day in range(30):
    for hour in range(0, 24, 4):
        start = datetime(2026, 9, day + 1, hour, 0, tzinfo=timezone.utc).timestamp()
        for i in range(3):
            events.append({
                "attemptId": f"d{day}-h{hour}-{i}",
                "taskId": f"task-{day}-{hour}-{i}",
                "tool": ["model:gpt-4", "model:claude-3", "model:local"][i % 3],
                "resource": ["pool-a", "pool-b"][i % 2],
                "startedAt": start,
                "settledAt": start + 5 + i * 2,
                "outcome": "succeeded" if (day + hour + i) % 5 else "failed",
                "actualCostMicrousd": 100 + (day * 10) + (hour * 5) + i,
            })

result = build_analytics(
    {"source": "import", "days": 30, "rows": events},
    now=now,
)

# Custom report
report = {
    "generated_at": now.isoformat(),
    "period": "30 days",
    "summary": {
        "total_attempts": result["kpis"]["attempts"],
        "success_rate": result["kpis"]["successRate"],
        "total_cost": result["kpis"]["knownCostMicrousd"],
        "cost_per_success": result["kpis"]["costPerSuccessMicrousd"],
    },
    "performance": {
        "latency_p50": result["latency"]["p50"],
        "latency_p95": result["latency"]["p95"],
        "latency_mean": result["latency"]["mean"],
    },
    "quality": {
        "unknown_cost_rows": result["quality"]["unknownCostRows"],
        "coverage_known": result["quality"]["selectionKnownCoverage"],
    },
    "trends": {
        "forecast_status": result["forecast"]["status"],
        "anomalies_count": len(result.get("anomalies", [])),
    },
    "recommendations": [],
}

# Generate recommendations
if result["kpis"]["successRate"] and result["kpis"]["successRate"] < 0.8:
    report["recommendations"].append("Success rate below 80% - investigate failure patterns")

if result["latency"]["p95"] and result["latency"]["p95"] > 30:
    report["recommendations"].append("P95 latency exceeds 30s - consider optimization")

if result["quality"]["unknownCostRows"] > 0:
    report["recommendations"].append(f"{result['quality']['unknownCostRows']} tasks have unknown costs - reconcile billing")

print("Custom Analytics Report:")
print(json.dumps(report, indent=2))
