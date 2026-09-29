"""Example 13: Building analytics from imported events.

Analytics provides KPIs, latency stats, daily breakdowns,
cohort economics, and forecasts from attempt records.
"""
from apexgraphswarm.analytics import build_analytics
from datetime import datetime, timezone

# Create sample events
now = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)
events = []
for i in range(20):
    start = datetime(2026, 9, 20 + i % 7, 10, i % 60, tzinfo=timezone.utc).timestamp()
    events.append({
        "attemptId": f"attempt-{i}",
        "taskId": f"task-{i}",
        "tool": "model:test-small" if i % 2 else "integration:review",
        "resource": "pool-a" if i % 3 else "pool-b",
        "startedAt": start,
        "settledAt": start + 10 + i,
        "outcome": "failed" if i % 7 == 0 else "succeeded",
        "actualCostMicrousd": 100 + i * 10,
    })

result = build_analytics(
    {"source": "import", "days": 30, "rows": events},
    now=now,
)

print(f"Attempts: {result['kpis']['attempts']}")
print(f"Succeeded: {result['kpis']['succeeded']}")
print(f"Failed: {result['kpis']['failed']}")
print(f"Success rate: {result['kpis']['successRate']:.2%}")
print(f"Known cost: {result['kpis']['knownCostMicrousd']} micro-USD")
print(f"Cost per success: {result['kpis']['costPerSuccessMicrousd']}")
print(f"Latency p50: {result['latency']['p50']:.1f}s")
print(f"Latency p95: {result['latency']['p95']:.1f}s")
print(f"Daily data points: {len(result['daily'])}")
print(f"Forecast status: {result['forecast']['status']}")
