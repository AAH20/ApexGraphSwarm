"""Example 58: Advanced - workflow orchestration.

Compose multiple control plane operations into complex workflows.
"""
from apexgraphswarm.control import ControlStore
from apexgraphswarm.optimization import DagTask, ModelOption, schedule_dag
import json

class WorkflowOrchestrator:
    """Orchestrate complex multi-step workflows."""

    def __init__(self, store: ControlStore):
        self.store = store

    def create_optimization_workflow(self, tasks_config, budget, capacities):
        """Create a workflow that optimizes task scheduling."""

        # Step 1: Create optimization plan
        dag_tasks = [
            DagTask(
                id=t["id"],
                dependencies=tuple(t.get("dependencies", [])),
                duration_estimate=t.get("duration", 1.0),
                options=tuple(
                    ModelOption(
                        model=o["model"],
                        estimated_cost_microusd=o["cost"],
                        duration_estimate=o.get("duration", 1.0),
                        eligible=o.get("eligible", True),
                    )
                    for o in t.get("options", [])
                ),
                deadline=t.get("deadline"),
            )
            for t in tasks_config
        ]

        schedule = schedule_dag(
            dag_tasks,
            budget_microusd=budget,
            capacities=capacities,
        )

        # Step 2: Create control plane run from schedule
        plan = {
            "version": 1,
            "agents": [{"id": f"agent-{i}"} for i in range(len(capacities))],
            "tasks": [
                {
                    "id": assignment.task_id,
                    "agentId": f"agent-{list(capacities.keys()).index(assignment.model)}",
                    "dependencies": [
                        t["id"] for t in tasks_config
                        if assignment.task_id in t.get("dependencies", [])
                    ],
                    "payload": {
                        "model": assignment.model,
                        "scheduled_start": assignment.start,
                        "scheduled_finish": assignment.finish,
                    },
                    "reservedCostMicrousd": assignment.cost_microusd,
                    "maxAttempts": 2,
                    "executionClass": "external",
                    "tool": f"integration:{assignment.model}:run",
                    "resource": f"pool-{assignment.model}",
                }
                for assignment in schedule.assignments
            ],
        }

        run = self.store.create_run(
            plan,
            idempotency_key=f"workflow-{budget}",
            budget_microusd=budget,
        )

        return {
            "schedule": schedule,
            "run": run,
        }

    def execute_workflow(self, run_id, worker_pool):
        """Execute a workflow with a pool of workers."""
        results = []

        while True:
            # Check if complete
            status = self.store.status(run_id)
            if status["run"]["status"] in ("succeeded", "failed", "cancelled"):
                break

            # Try to claim and execute tasks
            for worker_id in worker_pool:
                claim = self.store.claim(run_id, worker_id, lease_seconds=30)
                if claim:
                    # Execute task (simulated)
                    result = {"task": claim["id"], "worker": worker_id, "status": "completed"}
                    self.store.complete(
                        claim["taskId"],
                        claim["leaseToken"],
                        result,
                        0,
                    )
                    results.append(result)

        return results

# Example usage
store = ControlStore(":memory:")
orchestrator = WorkflowOrchestrator(store)

tasks_config = [
    {
        "id": "fetch",
        "dependencies": [],
        "duration": 1.0,
        "options": [
            {"model": "local", "cost": 50, "duration": 1.0},
        ],
    },
    {
        "id": "process",
        "dependencies": ["fetch"],
        "duration": 3.0,
        "options": [
            {"model": "gpt-4", "cost": 500, "duration": 3.0},
            {"model": "claude-3", "cost": 300, "duration": 2.0},
        ],
    },
    {
        "id": "summarize",
        "dependencies": ["process"],
        "duration": 1.0,
        "options": [
            {"model": "claude-3", "cost": 200, "duration": 1.0},
        ],
    },
]

result = orchestrator.create_optimization_workflow(
    tasks_config,
    budget=1000,
    capacities={"local": 5, "gpt-4": 2, "claude-3": 3},
)

print("Workflow created:")
print(f"  Run ID: {result['run']['run']['id']}")
print(f"  Scheduled tasks: {len(result['schedule'].assignments)}")
print(f"  Total cost: {result['schedule'].total_cost_microusd} micro-USD")

store.close()
