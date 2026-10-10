"""Example 27: vLLM telemetry collection.

Collect configured, read-only Prometheus telemetry from vLLM.
Only the URL from VLLM_METRICS_URL is queried.
"""
from apexgraphswarm.inference_telemetry import (
    collect_configured_telemetry,
    compare_snapshots,
)

# Collect current telemetry
result = collect_configured_telemetry()
print(f"Status: {result.status}")
print(f"Endpoint configured: {result.endpoint_configured}")

if result.snapshot:
    print(f"Series count: {len(result.snapshot.series)}")
    print(f"Metric types: {len(result.snapshot.metric_types)}")

    # Show some metrics
    for series in result.snapshot.series[:5]:
        print(f"  {series.name}{dict(series.labels)} = {series.value}")
else:
    print(f"Error: {result.error}")
    print("Note: Set VLLM_METRICS_URL environment variable to enable")

# Compare two snapshots (would need two collection rounds)
# comparison = compare_snapshots(snapshot1, snapshot2, window_seconds=5.0)
# print(comparison.to_dict())
