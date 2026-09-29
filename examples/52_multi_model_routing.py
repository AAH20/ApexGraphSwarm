"""Example 52: Advanced - multi-model routing.

Route tasks to different models based on complexity, cost,
and latency requirements.
"""
from apexgraphswarm.optimization import DagTask, ModelOption, schedule_dag

# Define tasks with different complexity levels
tasks = [
    # Simple task: use cheap model
    DagTask("classify", (), 0.0, (
        ModelOption("local-small", 10, 0.2, True),
        ModelOption("claude-3", 100, 0.5, True),
    )),
    # Medium task: use mid-tier model
    DagTask("summarize", ("classify",), 0.0, (
        ModelOption("claude-3", 300, 1.5, True),
        ModelOption("gpt-4", 500, 2.0, True),
    )),
    # Complex task: use best model
    DagTask("reason", ("summarize",), 0.0, (
        ModelOption("gpt-4", 1000, 5.0, True),
    ), deadline=10.0),
]

# Schedule with cost optimization
result = schedule_dag(
    tasks,
    budget_microusd=2000,
    capacities={"local-small": 10, "claude-3": 5, "gpt-4": 2},
    deadline_seconds=15.0,
)

print("Multi-model routing result:")
print(f"  Status: {result.status}")
print(f"  Feasible: {result.feasible}")
print(f"  Total cost: {result.total_cost_microusd} micro-USD")
print(f"  Makespan: {result.makespan:.1f}s")

print("\nRouting decisions:")
for a in result.assignments:
    print(f"  {a.task_id}: {a.model} (${a.cost_microusd}, {a.finish - a.start:.1f}s)")

# Analyze cost distribution
costs = {}
for a in result.assignments:
    costs[a.model] = costs.get(a.model, 0) + a.cost_microusd
print("\nCost distribution:")
for model, cost in costs.items():
    print(f"  {model}: {cost} micro-USD ({cost/result.total_cost_microusd:.1%})")
