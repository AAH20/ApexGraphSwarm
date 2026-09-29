"""Example 11: Building a repository graph.

The repository analyzer creates a source-grounded graph of modules,
files, symbols, and relationships without executing code.
"""
from apexgraphswarm.repository_graph import build_repository_graph

# Analyze the current repository
graph = build_repository_graph(".")

print(f"Graph name: {graph['name']}")
print(f"Nodes: {len(graph['nodes'])}")
print(f"Edges: {len(graph['edges'])}")
print(f"Warnings: {graph.get('warnings', [])}")
print(f"Truncated: {graph.get('truncated', False)}")

# Inspect node types
from collections import Counter
node_kinds = Counter(n["kind"] for n in graph["nodes"])
print(f"\nNode kinds: {dict(node_kinds)}")

# Inspect edge types
edge_relations = Counter(e["relation"] for e in graph["edges"])
print(f"Edge relations: {dict(edge_relations)}")

# Find a specific file
file_nodes = [n for n in graph["nodes"] if n["kind"] == "file"]
if file_nodes:
    print(f"\nSample file node: {file_nodes[0]['id']}")
    print(f"  Summary: {file_nodes[0].get('summary', 'N/A')[:80]}")
