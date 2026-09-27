# Configured vLLM telemetry

`apexgraphswarm.inference_telemetry` provides a bounded, read-only Prometheus collector and a comparison of two vLLM scrapes. It does not call inference endpoints, issue paid model requests, recommend autoscaling, or estimate invoice cost. A scrape is a real measurement from the configured server; a rate is derived only from two comparable snapshots and a caller-supplied elapsed window.

Metric names and semantics follow vLLM's [Production Metrics reference](https://docs.vllm.ai/en/latest/usage/metrics/) and [v1 metrics design](https://docs.vllm.ai/en/latest/design/metrics/). Text parsing follows the [Prometheus exposition format](https://prometheus.io/docs/instrumenting/exposition_formats/) and [histogram conventions](https://prometheus.io/docs/practices/histograms/). The current production page documents the `/metrics` endpoint, KV cache usage, request gauges, prefix-cache counters, token counters, preemption counters, and TTFT/queue/request latency histograms. vLLM has used both `vllm:prompt_tokens` and `vllm:prompt_tokens_total` naming across documented versions, so this module accepts only those exact documented aliases for the same family. Similar explicit aliases cover generation tokens, request success, and preemption. Unsupported or renamed fields remain unavailable.

## Configuration and collection

Set `VLLM_METRICS_URL` in the server environment to a vLLM Prometheus `/metrics` endpoint. The collector accepts HTTPS endpoints or plain HTTP only for `localhost` and IP loopback addresses. URLs with credentials, query strings, fragments, unsafe paths, or redirects are rejected. It disables environment proxies and follows no redirects. `VLLM_METRICS_TOKEN` is optional and is sent only as a server-side bearer header; it is never returned or placed in an error.

`collect_configured_telemetry(env=None, timeout_seconds=3.0, max_bytes=2_000_000)` reads only those two named environment values. A mapping can be supplied by trusted server-side code for tests and configuration; request JSON must not supply the endpoint or token. Timeouts are limited to 0.05–15 seconds. Responses are limited to 2 MB and 100,000 lines, with bounded labels and endpoint/token sizes. Errors use generic redacted messages.

```python
from apexgraphswarm.inference_telemetry import collect_configured_telemetry

result = collect_configured_telemetry()
print(result.to_dict())  # safe for JSON output; omits endpoint and labels
```

`python -m apexgraphswarm.inference_telemetry` prints one redacted JSON collection result from the process environment. `CollectionResult.to_dict()` and `TelemetryComparison.to_dict()` redact endpoint URLs, authorization tokens, and raw metric labels. `TelemetrySnapshot` retains labels for exact matching and should not be dumped with `dataclasses.asdict()` or logged.

`parse_prometheus(text)` accepts bounded Prometheus text exposition, including valid `NaN`/infinity sample values; those values remain explicit internally and become invalid/null in public telemetry rather than entering rates or quantiles. Duplicate samples, malformed labels, conflicting or late `TYPE` declarations, and non-finite timestamps are rejected.

## Parsed metric families

The module extracts exact documented names for current running, waiting and swapped requests; waiting-by-reason when available; `vllm:kv_cache_usage_perc` (and the documented legacy `vllm:gpu_cache_usage_perc` alias); local and external prefix-cache hit/query counters; prompt and generation token counters; request-success/finished counters; preemption counters; and the TTFT, queue-time, end-to-end latency, inter-token latency, and request TPOT histograms. The request counter's documented finish-reason semantics vary by vLLM version, so labels are preserved only for series matching and omitted from output; the collector does not relabel them as a success rate.

The family named `kv_cache_usage` measures KV cache block occupancy, not physical GPU utilization. Its accepted range is 0–1. Invalid gauges produce an explicit invalid status and a null value. A missing metric is omitted; it is never synthesized as zero. Counter rates require the exact metric name and label set to appear in both snapshots. New or missing series are `unmatched_series`; decreases are `counter_reset`. Either condition yields null delta/rate for that series. A matched counter with no change has a measured rate of zero. Public output uses per-family ordinal series IDs for matching within one result; it does not expose raw labels or deterministic label hashes.

`compare_snapshots(previous, current, window_seconds=...)` uses the explicit window supplied by the caller; the collector does not infer scrape timestamps or silently choose a rate window. Prefix-cache hit ratio is computed from matched token counters as `hit-token delta / queried-token delta`; zero queries yield `no_queries`, and a ratio over 1 is invalid. Generation-token and request-success rates remain per exact series, with raw labels omitted from public output.

## Histogram windows

For each supported histogram, both snapshots must have matching label identities and bucket edges. Each snapshot must provide finite `_sum`, integer cumulative `_count`, monotonic cumulative buckets, a `+Inf` bucket, and an `_count` matching the `+Inf` bucket. Window bucket counts are counter deltas; resets, changed bucket edges, missing series, or inconsistent histograms never produce a quantile.

The p50 and p95 values are bucket upper bounds: the first finite `le` bucket whose window cumulative count reaches the requested rank. No interpolation is performed. If the selected bucket is `+Inf`, that quantile's upper bound is unknown (`null`) and the histogram status explains that it is unbounded. Means are derived from `_sum` and `_count` deltas. These are server-wide histogram estimates, not per-request latencies or a guaranteed SLO.

## Result limits

Comparison results expose explicit `matched`, `counter_reset`, `unmatched_series`, `unmatched_buckets`, `invalid_histogram`, `unbounded_quantile`, and no-observation states. `TelemetryComparison.status` summarizes whether a scrape is empty, lacks a previous snapshot, has unmatched/reset data, or was compared. `limitations` reiterates that cache occupancy is not physical GPU utilization and histogram quantiles are bucket bounds.

No GPU allocation tariff, cloud price, invoice total, physical GPU utilization, or capacity recommendation is inferred here. Those values require separate caller-supplied evidence and must be labeled as estimates or unknown.
