"""Example 42: Optimization with evidence requirements.

Tasks can require specific evidence before execution.
"""
from apexgraphswarm.optimization import optimize

result = optimize({
    "action": "evidence",
    "tasks": [
        {
            "id": "fetch-data",
            "dependencies": [],
            "duration_estimate": 2.0,
            "options": [
                {"model": "local", "estimated_cost_microusd": 50, "duration_estimate": 2.0, "eligible": True},
            ],
        },
        {
            "id": "analyze-data",
            "dependencies": ["fetch-data"],
            "duration_estimate": 5.0,
            "options": [
                {"model": "gpt-4", "estimated_cost_microusd": 500, "duration_estimate": 5.0, "eligible": True},
            ],
        },
    ],
    "budget_microusd": 1000,
    "capacities": {"local": 5, "gpt-4": 2},
})

print(f"Status: {result.get('status', 'unknown')}")

if "evidence" in result:
    print("\nEvidence requirements:")
    for ev in result["evidence"]:
        print(f"  Task: {ev.get('task_id', 'unknown')}")
        print(f"    Required: {ev.get('required', [])}")
        print(f"    Satisfied: {ev.get('satisfied', False)}")

if "plan" in result:
    print(f"\nPlan: {result['plan']}")
