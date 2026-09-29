"""Example 39: Analytics anomaly detection.

Detect unusual patterns in cost, latency, or success rates.
"""
from apexgraphswarm.analytics import build_analytics
from datetime import datetime, timezone

now = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)
events = []

# Normal pattern
for i in range(20):
    start = datetime(2026, 9, 20 + i % 5, 10, 0, tzinfo=timezone.utc).timestamp()
    events.append({
        "attemptId": f"normal-{i}",
        "taskId": f"t-{i}",
        "tool": "model:test",
        "resource": "pool-a",
        "startedAt": start,
        "settledAt": start + 10,
        "outcome": "succeeded",
        "actualCostMicrousd": 100,
    })

# Anomaly: sudden cost spike
for i in range(3):
    start = datetime(2026, 9, 26, 10, 0, tzinfo=timezone.utc).timestamp()
    events.append({
        "attemptId": f"anomaly-{i}",
        "taskId": f"anomaly-t-{i}",
        "tool": "model:test",
        "resource": "pool-a",
        "startedAt": start,
        "settledAt": start + 10,
        "outcome": "succeeded",
        "actualCostMicrousd": 5000,  # 50x normal cost
    })

result = build_analytics(
    {"source": "import", "days": 30, "rows": events},
    now=now,
)

print(f"Total attempts: {result['kpis']['attempts']}")
print(f"Anomalies detected: {len(result.get('anomalies', []))}")

for anomaly in result.get("anomalies", []):
    print(f"  Anomaly: {anomaly.get('type', 'unknown')}")
    print(f"    Description: {anomaly.get('description', 'N/A')}")
    print(f"    Severity: {anomaly.get('severity', 'unknown')}")

# Correlation analysis
corr = result.get("correlation", {})
print(f"\nCorrelation: n={corr.get('n', 0)}, r={corr.get('pearsonR', 'N/A')}")
