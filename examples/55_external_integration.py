"""Example 55: Advanced - integration with external systems.

Example patterns for integrating ApexGraphSwarm with
external APIs, databases, and message queues.
"""
import json
import sqlite3
from apexgraphswarm.control import ControlStore

class ExternalSystemAdapter:
    """Adapter pattern for external system integration."""

    def __init__(self, control_store: ControlStore):
        self.store = control_store

    def sync_tasks_to_external(self, run_id: str, external_api):
        """Sync task status to an external tracking system."""
        status = self.store.status(run_id)

        for task in status["tasks"]:
            external_api.update_task(
                external_id=task["taskId"],
                status=task["status"],
                agent=task["agentId"],
            )

    def import_tasks_from_external(self, external_api, agent_id: str):
        """Import tasks from an external system."""
        external_tasks = external_api.get_pending_tasks()

        plan = {
            "version": 1,
            "agents": [{"id": agent_id}],
            "tasks": [
                {
                    "id": ext_task["id"],
                    "agentId": agent_id,
                    "dependencies": ext_task.get("dependencies", []),
                    "payload": ext_task["payload"],
                    "reservedCostMicrousd": ext_task.get("cost", 0),
                    "maxAttempts": ext_task.get("max_attempts", 3),
                    "executionClass": "external",
                }
                for ext_task in external_tasks
            ],
        }

        return plan

    def export_results(self, run_id: str):
        """Export run results for external consumption."""
        status = self.store.status(run_id)
        ledger = self.store.ledger(run_id)

        return {
            "run_id": run_id,
            "status": status["run"]["status"],
            "tasks": [
                {
                    "id": t["id"],
                    "status": t["status"],
                    "result": t.get("result"),
                }
                for t in status["tasks"]
            ],
            "costs": {
                "total": ledger["knownActualMicrousd"],
                "attempts": len(ledger["attempts"]),
            },
        }

# Example usage
store = ControlStore(":memory:")
adapter = ExternalSystemAdapter(store)

# Create a run
plan = {
    "version": 1,
    "agents": [{"id": "a"}],
    "tasks": [
        {"id": "t1", "agentId": "a", "dependencies": [],
         "payload": {"kind": "fixture"}, "reservedCostMicrousd": 0,
         "maxAttempts": 1, "executionClass": "fixture"},
    ],
}

run = store.create_run(plan, idempotency_key="integration-demo", budget_microusd=0)
run_id = run["run"]["id"]

# Export results
results = adapter.export_results(run_id)
print("Exported results:")
print(json.dumps(results, indent=2))

store.close()
