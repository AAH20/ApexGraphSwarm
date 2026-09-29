# ADR-022: Inference telemetry as read-only Prometheus metrics

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must collect inference metrics from vLLM servers for capacity planning and cost analysis. This must be read-only, bounded, and must not expose endpoint URLs or metric labels in public serializers.

## Decision

**Inference telemetry is read-only Prometheus metrics collection with strict boundaries.** Key characteristics:

- **Configured endpoint only**: The module only fetches the URL held in `VLLM_METRICS_URL`. It never accepts a URL from a request payload.
- **No redirects**: The HTTP client does not follow redirects.
- **No proxy**: No proxy handler is used.
- **Bounded response**: Maximum 2 MiB body, 100,000 metric lines, 64 labels per series, 4,096 chars per label value.
- **Timeout**: Default 3 seconds.
- **Public serializers omit sensitive data**: Endpoint URLs and metric labels are omitted from public serializers.
- **Missing measurements are not zero**: "It never accepts a URL from a request payload, follows redirects, or treats missing measurements as zero."

**Metric families:**
- Gauges: requests_running, requests_waiting, requests_swapped, kv_cache_usage
- Counters: prefix_cache_queries, prefix_cache_hits, prompt_tokens, generation_tokens, preemptions, requests_finished
- Histograms: ttft, request_latency, queue_latency, inter_token_latency, request_tpot

## Alternatives considered

1. **Accept URL from request**: Would be more flexible but would enable SSRF attacks.
2. **Follow redirects**: Would be more convenient but could redirect to internal services.
3. **Store full metric labels**: Would enable more analysis but would expose infrastructure details.

## Consequences

- **Positive**: Read-only safety; bounded resource usage; no SSRF risk; no sensitive data exposure.
- **Negative**: Limited to configured endpoint; missing measurements remain unknown; no historical storage.
- **Critical statement**: "It never accepts a URL from a request payload, follows redirects, or treats missing measurements as zero."

## Related

- ADR-002 (stdlib-only control plane)
- ADR-006 (bounded execution model)
- ADR-012 (explicit adapter pattern)
- ADR-015 (read-only analytics)
