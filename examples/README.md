# ApexGraphSwarm Code Examples

60 code examples covering all major features of the ApexGraphSwarm platform.

## Basic Usage (01-10)

| # | Example | Description |
|---|---------|-------------|
| 01 | `01_basic_imports.py` | Module imports and API discovery |
| 02 | `02_control_store_creation.py` | Creating ControlStore instances |
| 03 | `03_create_simple_run.py` | Creating DAG runs with tasks |
| 04 | `04_claim_and_complete.py` | Claiming and completing tasks |
| 05 | `05_worker_enrollment.py` | Worker enrollment and authentication |
| 06 | `06_access_grants.py` | Capability-based access grants |
| 07 | `07_heartbeat_and_lease.py` | Heartbeats and lease management |
| 08 | `08_run_status_and_events.py` | Run status and event history |
| 09 | `09_budget_and_cost.py` | Budget management and cost tracking |
| 10 | `10_cancellation_and_recovery.py` | Cancellation and expired lease recovery |

## Repository Intelligence (11-12)

| # | Example | Description |
|---|---------|-------------|
| 11 | `11_repository_graph.py` | Building repository graphs |
| 12 | `12_repository_graph_limits.py` | Custom analysis limits |

## Analytics (13-16)

| # | Example | Description |
|---|---------|-------------|
| 13 | `13_analytics_import.py` | Analytics from imported events |
| 14 | `14_analytics_filtering.py` | Filtering and quality metrics |
| 15 | `15_analytics_demo_forecast.py` | Demo mode and forecasting |
| 16 | `16_analytics_live.py` | Live ledger analytics |

## Evaluation (17-18)

| # | Example | Description |
|---|---------|-------------|
| 17 | `17_evaluation.py` | Candidate evaluation with promotion gates |
| 18 | `18_evaluation_metric_profiles.py` | Metric profiles and hard gates |

## Evolution (19)

| # | Example | Description |
|---|---------|-------------|
| 19 | `19_evolution.py` | Bounded algorithm evolution |

## Optimization (20, 41-43)

| # | Example | Description |
|---|---------|-------------|
| 20 | `20_dag_scheduling.py` | DAG scheduling with model options |
| 41 | `41_optimization_waves.py` | Task wave planning |
| 42 | `42_optimization_evidence.py` | Evidence requirements |
| 43 | `43_optimization_capacity.py` | Capacity constraints |

## Hierarchy (21-22)

| # | Example | Description |
|---|---------|-------------|
| 21 | `21_hierarchy_planning.py` | Hierarchical swarm planning |
| 22 | `22_metric_profiles.py` | Metric profiles and weighted scoring |

## Specialist Access (23)

| # | Example | Description |
|---|---------|-------------|
| 23 | `23_specialist_contracts.py` | Specialist access contracts |

## Delegation (24)

| # | Example | Description |
|---|---------|-------------|
| 24 | `24_delegation_plan.py` | Delegation plan compilation |

## Provider Receipts (25-26)

| # | Example | Description |
|---|---------|-------------|
| 25 | `25_openrouter_receipt.py` | OpenRouter receipt normalization |
| 26 | `26_receipt_reconciliation.py` | Receipt reconciliation |

## Telemetry (27)

| # | Example | Description |
|---|---------|-------------|
| 27 | `27_vllm_telemetry.py` | vLLM telemetry collection |

## Repository Conflicts (28)

| # | Example | Description |
|---|---------|-------------|
| 28 | `28_repository_conflicts.py` | Repository conflict planning |

## Request Registry (29)

| # | Example | Description |
|---|---------|-------------|
| 29 | `29_request_registry.py` | Idempotent request registry |

## Execution Graph (30)

| # | Example | Description |
|---|---------|-------------|
| 30 | `30_execution_graph.py` | Execution graph projection |

## Control Plane (31-37)

| # | Example | Description |
|---|---------|-------------|
| 31 | `31_resource_capacity.py` | Resource capacity management |
| 32 | `32_ledger_receipts.py` | Ledger and attempt receipts |
| 33 | `33_generation_ownership.py` | Provider generation ownership |
| 34 | `34_worker_checkpoints.py` | Worker checkpoints and recovery |
| 35 | `35_concurrent_execution.py` | Concurrent task execution |
| 36 | `36_error_handling.py` | Error handling and validation |
| 37 | `37_custom_clock.py` | Custom clock for testing |

## Advanced Analytics (38-40)

| # | Example | Description |
|---|---------|-------------|
| 38 | `38_cohort_economics.py` | Cohort economics |
| 39 | `39_anomaly_detection.py` | Anomaly detection |
| 40 | `40_relationship_graphs.py` | Relationship graphs |

## Governance (44-45)

| # | Example | Description |
|---|---------|-------------|
| 44 | `44_governance_validation.py` | Plan validation and compliance |
| 45 | `45_governance_audit.py` | Audit trail and compliance reporting |

## Deployment (46-50)

| # | Example | Description |
|---|---------|-------------|
| 46 | `46_deployment_production.py` | Production ControlStore setup |
| 47 | `47_deployment_docker.py` | Docker container setup |
| 48 | `48_deployment_kubernetes.py` | Kubernetes configuration |
| 49 | `49_deployment_monitoring.py` | Monitoring and alerting |
| 50 | `50_deployment_backup.py` | Backup and disaster recovery |

## Advanced Usage (51-60)

| # | Example | Description |
|---|---------|-------------|
| 51 | `51_custom_solver.py` | Custom solver integration |
| 52 | `52_multi_model_routing.py` | Multi-model routing |
| 53 | `53_fault_tolerance.py` | Fault tolerance and retry logic |
| 54 | `54_cost_aware_scheduling.py` | Cost-aware task scheduling |
| 55 | `55_external_integration.py` | External system integration |
| 56 | `56_performance_optimization.py` | Performance optimization |
| 57 | `57_custom_metrics.py` | Custom metrics and reporting |
| 58 | `58_workflow_orchestration.py` | Workflow orchestration |
| 59 | `59_security_hardening.py` | Security hardening |
| 60 | `60_testing_patterns.py` | Testing patterns |

## Running the Examples

```bash
# Run a single example
python examples/03_create_simple_run.py

# Run all examples
for f in examples/*.py; do echo "=== $f ==="; python "$f"; done

# Run tests
python -m pytest examples/60_testing_patterns.py -v
```
