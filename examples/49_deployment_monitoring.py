"""Example 49: Deployment - monitoring and alerting.

Set up monitoring for the control plane with key metrics.
"""
from apexgraphswarm.control import ControlStore
import time

store = ControlStore(":memory:")

def collect_metrics(store):
    """Collect key operational metrics."""
    metrics = {
        "timestamp": time.time(),
        "active_tasks": 0,
        "pending_tasks": 0,
        "completed_tasks": 0,
        "failed_tasks": 0,
        "total_runs": 0,
    }

    # This is a simplified example. In practice, you would
    # query the database directly for these metrics.
    return metrics

def check_alerts(metrics):
    """Check for alert conditions."""
    alerts = []

    # Alert: Too many active tasks
    if metrics["active_tasks"] > 50:
        alerts.append({
            "severity": "warning",
            "message": f"High active task count: {metrics['active_tasks']}",
        })

    # Alert: High failure rate
    total = metrics["completed_tasks"] + metrics["failed_tasks"]
    if total > 0:
        failure_rate = metrics["failed_tasks"] / total
        if failure_rate > 0.2:
            alerts.append({
                "severity": "critical",
                "message": f"High failure rate: {failure_rate:.2%}",
            })

    return alerts

# Simulate monitoring loop
print("Monitoring started (simulated):")
for i in range(5):
    metrics = collect_metrics(store)
    alerts = check_alerts(metrics)

    print(f"\n[{i+1}] Metrics: {metrics}")
    if alerts:
        for alert in alerts:
            print(f"  ALERT [{alert['severity']}]: {alert['message']}")
    else:
        print("  No alerts")

    time.sleep(0.1)

store.close()
print("\nMonitoring stopped.")
