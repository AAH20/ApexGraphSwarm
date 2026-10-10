"""Example 14: Analytics with filtering and quality metrics.

Filter by tool, resource, or outcome. Quality metrics track
unknown costs and coverage.
"""
from apexgraphswarm.analytics import build_analytics
from datetime import datetime, timezone

now = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)
events = []
for i in range(30):
    start = datetime(2026, 9, 20 + i % 7, 10, 0, tzinfo=timezone.utc).timestamp()
    events.append({
        "attemptId": f"a-{i}",
        "taskId": f"t-{i}",
        "tool": "model:gpt-4" if i % 3 == 0 else "model:claude",
        "resource": "pool-a",
        "startedAt": start,
        "settledAt": start + 5 + i * 2,
        "outcome": "succeeded" if i % 5 else "failed",
        "actualCostMicrousd": None if i % 11 == 0 else 200 + i * 5,
    })

# Filter by tool
filtered = build_analytics(
    {"source": "import", "days": 30, "tool": "model:gpt-4", "rows": events},
    now=now,
)
print(f"Filtered to model:gpt-4: {filtered['kpis']['attempts']} attempts")
print(f"Quality: {filtered['quality']}")

# Check unknown cost tracking
print(f"\nUnknown cost rows: {filtered['quality']['unknownCostRows']}")
print(f"Selection known coverage: {filtered['quality']['selectionKnownCoverage']}")

# Full dataset
full = build_analytics(
    {"source": "import", "days": 30, "rows": events},
    now=now,
)
print(f"\nFull dataset: {full['kpis']['attempts']} attempts")
print(f"Cost per success: {full['kpis']['costPerSuccessMicrousd']}")
