"""Example 01: Basic imports and module discovery.

Shows how to import the main ApexGraphSwarm modules and inspect
their public APIs.
"""
from apexgraphswarm import (
    ControlStore,
    build_repository_graph,
    build_analytics,
    evaluate_candidate,
    schedule_dag,
    plan_hierarchy,
    run_evolution,
    compile_delegation_plan,
    normalize_openrouter_receipt,
    collect_configured_telemetry,
    plan_repository_conflicts,
    register_hashed_request,
    project_execution_graph,
)

print("All core modules imported successfully.")
print(f"ControlStore: {ControlStore}")
print(f"build_repository_graph: {build_repository_graph}")
print(f"build_analytics: {build_analytics}")
