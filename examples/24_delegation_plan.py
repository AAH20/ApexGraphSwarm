"""Example 24: Delegation plan compilation.

Compile a verified constrained model schedule into a control-plane
plan with adapter bindings and task inputs.
"""
from apexgraphswarm.delegation_plan import compile_delegation_plan

problem = {
    "tasks": [
        {
            "id": "review-code",
            "dependencies": [],
            "duration_estimate": 2.0,
            "options": [
                {"model": "gpt-4", "estimated_cost_microusd": 500, "duration_estimate": 2.0, "eligible": True},
                {"model": "claude-3", "estimated_cost_microusd": 300, "duration_estimate": 1.5, "eligible": True},
            ],
        },
        {
            "id": "write-tests",
            "dependencies": ["review-code"],
            "duration_estimate": 1.0,
            "options": [
                {"model": "gpt-4", "estimated_cost_microusd": 400, "duration_estimate": 1.0, "eligible": True},
            ],
        },
    ],
    "model_options": [
        {"model": "gpt-4", "estimated_cost_microusd": 500, "duration_estimate": 2.0, "eligible": True},
        {"model": "claude-3", "estimated_cost_microusd": 300, "duration_estimate": 1.5, "eligible": True},
    ],
    "budget_microusd": 2000,
    "capacities": {"gpt-4": 2, "claude-3": 3},
    "deadline_seconds": 10.0,
}

model_bindings = {
    "gpt-4": {
        "configured": True,
        "adapterId": "adapter-openai",
        "operation": "review",
        "modelId": "gpt-4",
        "resourceId": "model-pool-a",
        "toolId": "integration:adapter-openai:review",
        "costMicrousd": 500,
        "maxParallel": 4,
    },
    "claude-3": {
        "configured": True,
        "adapterId": "adapter-anthropic",
        "operation": "review",
        "modelId": "claude-3",
        "resourceId": "model-pool-b",
        "toolId": "integration:adapter-anthropic:review",
        "costMicrousd": 300,
        "maxParallel": 6,
    },
}

task_inputs = {
    "review-code": {
        "goal": "Review the authentication module for security issues",
        "graph": {
            "version": 1,
            "name": "auth-module",
            "nodes": [
                {"id": "file:auth.py", "name": "auth.py", "kind": "file", "path": "src/auth.py", "confidence": "parsed"},
            ],
            "edges": [],
        },
    },
}

result = compile_delegation_plan(problem, model_bindings, task_inputs=task_inputs)

print(f"Plan version: {result['version']}")
print(f"Plan name: {result['name']}")
print(f"Agents: {len(result['agents'])}")
print(f"Tasks: {len(result['tasks'])}")
print(f"Total cost: {result['totalCostMicrousd']} micro-USD")
print(f"Makespan: {result['makespan']:.1f}s")
print(f"Feasible: {result['feasible']}")
print(f"Algorithm: {result['algorithm']}")
