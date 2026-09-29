"""Example 54: Advanced - cost-aware task scheduling.

Schedule tasks to minimize cost while meeting deadlines.
"""
from apexgraphswarm.optimization import DagTask, ModelOption, schedule_dag

# Tasks with varying complexity and deadlines
tasks = [
    DagTask("quick-win", (), 0.0, (
        ModelOption("local-small", 5, 0.1, True),
        ModelOption("claude-3", 50, 0.5, True),
    ), deadline=1.0),
    DagTask("research", (), 0.0, (
        ModelOption("claude-3", 200, 2.0, True),
        ModelOption("gpt-4", 400, 3.0, True),
    ), deadline=5.0),
    DagTask("deep-analysis", ("research",), 0.0, (
        ModelOption("gpt-4", 800, 5.0, True),
    ), deadline=10.0),
    DagTask("summary", ("deep-analysis",), 0.0, (
        ModelOption("claude-3", 150, 1.0, True),
        ModelOption("local-small", 30, 0.5, True),
    ), deadline=12.0),
]

# Tight budget forces cost-aware selection
result = schedule_dag(
    tasks,
    budget_microusd=500,  # Very tight budget
    capacities={"local-small": 10, "claude-3": 5, "gpt-4": 2},
    deadline_seconds=15.0,
)

print("Cost-aware scheduling:")
print(f"  Status: {result.status}")
print(f"  Feasible: {result.feasible}")
print(f"  Total cost: {result.total_cost_microusd} micro-USD")
print(f"  Makespan: {result.makespan:.1f}s")

print("\nCost-optimized assignments:")
for a in result.assignments:
    print(f"  {a.task_id}: {a.model} (${a.cost_microusd}, {a.finish - a.start:.1f}s)")

# Compare with unlimited budget
result_unlimited = schedule_dag(
    tasks,
    budget_microusd=10000,
    capacities={"local-small": 10, "claude-3": 5, "gpt-4": 2},
    deadline_seconds=15.0,
)

print(f"\nWith unlimited budget:")
print(f"  Total cost: {result_unlimited.total_cost_microusd} micro-USD")
print(f"  Makespan: {result_unlimited.makespan:.1f}s")
print(f"  Cost savings: {result_unlimited.total_cost_microusd - result.total_cost_microusd} micro-USD")
