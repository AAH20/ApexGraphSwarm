"""Example 38: Analytics cohort economics.

Analyze cost and success rates by cohort (tool, resource,
or time period).
"""
from apexgraphswarm.analytics import build_analytics
from datetime import datetime, timezone

now = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)
events = []

# Generate events across different tools and resources
tools = ["model:gpt-4", "model:claude-3", "model:local"]
resources = ["pool-a", "pool-b"]

for i in range(50):
    day = 20 + i % 7
    start = datetime(2026, 9, day, 10, i % 60, tzinfo=timezone.utc).timestamp()
    tool = tools[i % 3]
    resource = resources[i % 2]
    cost = 100 + (i % 3) * 200
    outcome = "succeeded" if i % 4 else "failed"

    events.append({
        "attemptId": f"a-{i}",
        "taskId": f"t-{i}",
        "tool": tool,
        "resource": resource,
        "startedAt": start,
        "settledAt": start + 5 + i,
        "outcome": outcome,
        "actualCostMicrousd": cost,
    })

result = build_analytics(
    {"source": "import", "days": 30, "rows": events},
    now=now,
)

print("Cohort economics:")
print(f"  Total attempts: {result['kpis']['attempts']}")
print(f"  Success rate: {result['kpis']['successRate']:.2%}")
print(f"  Cost per success: {result['kpis']['costPerSuccessMicrousd']}")

# Daily breakdown
print("\nDaily breakdown:")
for day in result["daily"][:5]:
    print(f"  {day['date']}: {day['attempts']} attempts, "
          f"{day['succeeded']} succeeded, "
          f"${day['knownCostMicrousd']} cost")

# Cohort analysis
if result.get("cohorts"):
    print("\nCohorts:")
    for cohort in result["cohorts"][:5]:
        print(f"  {cohort.get('cohort', 'unknown')}: "
              f"{cohort.get('attempts', 0)} attempts, "
              f"{cohort.get('successRate', 0):.2%} success")
