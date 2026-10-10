"""Example 12: Repository graph with custom limits.

Control the analysis scope with file and symbol limits.
"""
from apexgraphswarm.repository_graph import build_repository_graph

# Analyze with custom limits
graph = build_repository_graph(
    ".",
    max_files=500,    # Limit to 500 files
    max_symbols=5000,  # Limit to 5000 symbols
)

print(f"Analyzed with limits: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

# Check for truncation
if graph.get("truncated"):
    print("WARNING: Analysis was truncated due to limits")

# Export to JSON for inspection
import json
with open("/tmp/repo-graph.json", "w") as f:
    json.dump(graph, f, indent=2)
print("Graph exported to /tmp/repo-graph.json")
