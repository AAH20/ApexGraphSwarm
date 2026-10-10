"""Example 21: Hierarchical swarm planning.

Plan-only hierarchical assignment of tasks to agents based on
capabilities, scopes, and metric profiles.
"""
from apexgraphswarm.hierarchy import plan_hierarchy

result = plan_hierarchy({
    "profileId": "coding",
    "tasks": [
        {
            "id": "implement-auth",
            "family": "backend",
            "dependencies": [],
            "requiredCapabilities": ["python", "fastapi"],
            "requiredActions": ["write-code"],
            "resourceScope": "repo:auth",
            "dataBoundary": "internal",
            "estimatedCostMicrousd": 5000,
            "estimatedLatencyMs": 30000,
        },
        {
            "id": "write-tests",
            "family": "testing",
            "dependencies": ["implement-auth"],
            "requiredCapabilities": ["pytest"],
            "requiredActions": ["write-code"],
            "resourceScope": "repo:auth",
            "dataBoundary": "internal",
            "estimatedCostMicrousd": 2000,
            "estimatedLatencyMs": 15000,
        },
    ],
    "agents": [
        {
            "id": "backend-lead",
            "role": "leader",
            "profileIds": ["coding"],
            "capabilities": ["python", "fastapi", "pytest"],
            "resourceScopes": ["repo:auth"],
            "dataBoundaries": ["internal"],
            "authorizedActions": ["write-code", "review-code"],
            "authorizationGrantId": "grant-1",
            "maxAssignments": 5,
            "maxClustersLed": 3,
            "metricScores": {
                "correctness": 0.9,
                "test_coverage": 0.85,
                "regression_control": 0.8,
                "evidence_provenance": 0.9,
                "reliability": 0.95,
                "latency": 0.7,
                "cost_efficiency": 0.6,
                "coordination_efficiency": 0.9,
            },
            "estimatedCostMicrousdPerTask": 3000,
        },
    ],
    "limits": {
        "budgetMicrousd": 10000,
        "deadlineMs": 60000,
        "maxClusterTasks": 10,
        "maxClusters": 5,
    },
})

print(f"Profile: {result['profileId']}")
print(f"Tasks: {len(result['tasks'])}")
print(f"Agents: {len(result['agents'])}")
print(f"Assignments: {len(result.get('assignments', []))}")
print(f"Budget: {result['limits']['budgetMicrousd']} micro-USD")
print(f"Deadline: {result['limits']['deadlineMs']}ms")
