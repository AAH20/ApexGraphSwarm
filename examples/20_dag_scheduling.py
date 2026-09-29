"""Example 20: DAG scheduling with model options and capacities.

The optimizer chooses model options for DAG tasks under budget,
capacity, and deadline constraints.
"""
from apexgraphswarm.optimization import (
    DagTask,
    ModelOption,
    schedule_dag,
)

# Define model options
options = [
    ModelOption("gpt-4", 500, 2.0, True),
    ModelOption("claude-3", 300, 1.5, True),
    ModelOption("local-small", 50, 0.5, True),
    ModelOption("expensive-model", 2000, 5.0, False),  # ineligible
]

# Define DAG tasks
tasks = [
    DagTask("extract", (), 0.0, (
        ModelOption("gpt-4", 500, 2.0, True),
        ModelOption("claude-3", 300, 1.5, True),
    )),
    DagTask("analyze", ("extract",), 0.0, (
        ModelOption("gpt-4", 800, 3.0, True),
        ModelOption("local-small", 100, 1.0, True),
    )),
    DagTask("summarize", ("analyze",), 0.0, (
        ModelOption("claude-3", 200, 1.0, True),
    ), deadline=10.0),
]

# Schedule with budget and capacities
result = schedule_dag(
    tasks,
    budget_microusd=2000,
    capacities={"gpt-4": 2, "claude-3": 3, "local-small": 5},
    deadline_seconds=15.0,
    model_options=options,
)

print(f"Status: {result.status}")
print(f"Feasible: {result.feasible}")
print(f"Algorithm: {result.algorithm}")
print(f"Exact: {result.exact}")
print(f"Total cost: {result.total_cost_microusd} micro-USD")
print(f"Makespan: {result.makespan:.1f}s")
print(f"Limits: {result.limits}")

print("\nAssignments:")
for a in result.assignments:
    print(f"  {a.task_id}: {a.model} [{a.start:.1f} - {a.finish:.1f}] ${a.cost_microusd}")
