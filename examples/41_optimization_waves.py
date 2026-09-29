"""Example 41: Optimization with evidence and waves.

Plan task waves with dependency ordering and evidence requirements.
"""
from apexgraphswarm.optimization import optimize

result = optimize({
    "action": "waves",
    "tasks": [
        {
            "id": "research",
            "dependencies": [],
            "duration_estimate": 5.0,
            "options": [
                {"model": "gpt-4", "estimated_cost_microusd": 1000, "duration_estimate": 5.0, "eligible": True},
            ],
        },
        {
            "id": "implement",
            "dependencies": ["research"],
            "duration_estimate": 10.0,
            "options": [
                {"model": "gpt-4", "estimated_cost_microusd": 2000, "duration_estimate": 10.0, "eligible": True},
                {"model": "claude-3", "estimated_cost_microusd": 1500, "duration_estimate": 8.0, "eligible": True},
            ],
        },
        {
            "id": "test",
            "dependencies": ["implement"],
            "duration_estimate": 3.0,
            "options": [
                {"model": "local", "estimated_cost_microusd": 100, "duration_estimate": 3.0, "eligible": True},
            ],
        },
    ],
    "budget_microusd": 5000,
    "capacities": {"gpt-4": 2, "claude-3": 2, "local": 5},
})

print(f"Status: {result.get('status', 'unknown')}")
print(f"Feasible: {result.get('feasible', 'unknown')}")

if "waves" in result:
    print(f"\nWaves: {len(result['waves'])}")
    for i, wave in enumerate(result["waves"]):
        print(f"  Wave {i+1}: {wave.get('tasks', [])}")

if "assignments" in result:
    print(f"\nAssignments:")
    for a in result["assignments"]:
        print(f"  {a.task_id}: {a.model} [{a.start:.1f} - {a.finish:.1f}]")

if "total_cost_microusd" in result:
    print(f"\nTotal cost: {result['total_cost_microusd']} micro-USD")
if "makespan" in result:
    print(f"Makespan: {result['makespan']:.1f}s")
