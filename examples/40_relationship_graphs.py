"""Example 40: Analytics relationship graphs.

Visualize relationships between tools, resources, and outcomes
as a bounded graph structure.
"""
from apexgraphswarm.analytics import build_analytics
from datetime import datetime, timezone

now = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)
events = []

# Generate events with clear tool-resource relationships
for i in range(30):
    start = datetime(2026, 9, 20 + i % 5, 10, 0, tzinfo=timezone.utc).timestamp()
    events.append({
        "attemptId": f"a-{i}",
        "taskId": f"t-{i}",
        "tool": "model:gpt-4" if i % 2 else "model:claude-3",
        "resource": "pool-a" if i % 3 else "pool-b",
        "startedAt": start,
        "settledAt": start + 10,
        "outcome": "succeeded" if i % 4 else "failed",
        "actualCostMicrousd": 100 + i * 10,
    })

result = build_analytics(
    {"source": "import", "days": 30, "rows": events},
    now=now,
)

graph = result.get("graph", {})
print(f"Graph nodes: {len(graph.get('nodes', []))}")
print(f"Graph edges: {len(graph.get('edges', []))}")

print("\nNodes:")
for node in graph.get("nodes", [])[:10]:
    print(f"  [{node.get('kind', 'unknown')}] {node.get('label', node.get('id', 'unknown'))}")

print("\nEdges:")
for edge in graph.get("edges", [])[:10]:
    print(f"  {edge.get('source', '?')} -> {edge.get('target', '?')} "
          f"({edge.get('relation', 'related')})")

# Scatter plot data
scatter = result.get("scatter", [])
print(f"\nScatter points: {len(scatter)}")
if scatter:
    print(f"  Sample: {scatter[0]}")
