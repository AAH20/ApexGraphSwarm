"""Example 43: Optimization with capacity constraints.

Model capacity limits constrain how many tasks can run
concurrently on each model.
"""
from apexgraphswarm.optimization import optimize

result = optimize({
    "action": "capacity",
    "tasks": [
        {
            "id": f"task-{i}",
            "dependencies": [] if i < 3 else [f"task-{i-3}"],
            "duration_estimate": 2.0 + i * 0.5,
            "options": [
                {"model": "gpt-4", "estimated_cost_microusd": 200 + i * 50, "duration_estimate": 2.0, "eligible": True},
                {"model": "claude-3", "estimated_cost_microusd": 150 + i * 30, "duration_estimate": 1.5, "eligible": True},
            ],
        }
        for i in range(8)
    ],
    "budget_microusd": 3000,
    "capacities": {"gpt-4": 2, "claude-3": 3},
})

print(f"Status: {result.get('status', 'unknown')}")
print(f"Feasible: {result.get('feasible', 'unknown')}")

if "capacity" in result:
    print("\nCapacity usage:")
    for model, usage in result["capacity"].items():
        print(f"  {model}: {usage}")

if "schedule" in result:
    print(f"\nSchedule:")
    for item in result["schedule"]:
        print(f"  {item}")
