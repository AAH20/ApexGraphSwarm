"""Example 30: Execution graph projection.

Project a ControlStore status snapshot into a bounded explanation
graph with nodes, edges, and cost summaries.
"""
from apexgraphswarm.execution_graph import project_execution_graph

# Create a sample status mapping
status = {
    "run": {
        "id": "run-123",
        "status": "succeeded",
        "budgetMicrousd": 10000,
        "spentMicrousd": 7500,
        "remainingMicrousd": 2500,
        "version": 1,
    },
    "tasks": [
        {
            "taskId": "task-uuid-1",
            "id": "inspect",
            "status": "succeeded",
            "agentId": "agent-1",
            "executionClass": "fixture",
            "reservedCostMicrousd": 0,
            "attempts": 1,
            "maxAttempts": 2,
        },
        {
            "taskId": "task-uuid-2",
            "id": "analyze",
            "status": "succeeded",
            "agentId": "agent-2",
            "executionClass": "external",
            "tool": "integration:openrouter:review",
            "resource": "model-pool-a",
            "reservedCostMicrousd": 5000,
            "attempts": 1,
            "maxAttempts": 3,
            "dependencies": ["inspect"],
        },
    ],
    "agents": [
        {"id": "agent-1", "name": "Inspector"},
        {"id": "agent-2", "name": "Analyzer"},
    ],
    "ledger": {
        "attempts": [
            {
                "attemptId": "attempt-1",
                "taskId": "task-uuid-1",
                "attempt": 1,
                "outcome": "succeeded",
                "actualCostMicrousd": 0,
                "reservedMicrousd": 0,
                "workerId": "worker-1",
                "principalId": "principal-1",
                "tool": None,
                "resource": None,
            },
            {
                "attemptId": "attempt-2",
                "taskId": "task-uuid-2",
                "attempt": 1,
                "outcome": "succeeded",
                "actualCostMicrousd": 4500,
                "reservedMicrousd": 5000,
                "workerId": "worker-2",
                "principalId": "principal-2",
                "tool": "integration:openrouter:review",
                "resource": "model-pool-a",
            },
        ],
        "totalAttempts": 2,
        "knownActualMicrousd": 4500,
        "unresolvedCostCount": 0,
        "allCostsResolved": True,
        "coverageComplete": True,
    },
}

graph = project_execution_graph(status)

print(f"Run ID: {graph['runId']}")
print(f"Nodes: {len(graph['nodes'])}")
print(f"Edges: {len(graph['edges'])}")
print(f"Truncated: {graph['truncated']}")

print("\nSummary:")
for key, value in graph["summary"].items():
    print(f"  {key}: {value}")

print("\nNodes:")
for node in graph["nodes"]:
    print(f"  [{node['kind']}] {node['label']}")
    if "status" in node:
        print(f"    Status: {node['status']}")
    if "actualMicrousd" in node:
        print(f"    Actual: {node['actualMicrousd']} micro-USD")
