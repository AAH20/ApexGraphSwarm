import json
import math
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import unittest

from apexgraphswarm.inference_telemetry import (
    TelemetryError,
    collect_configured_telemetry,
    compare_snapshots,
    parse_prometheus,
)


def snapshot_text(*, running=1, waiting=2, kv=0.5, queries=80, hits=50,
                  prompt=100, generated=200, preemptions=1, ttft=(10, 5, 2, 5, 8, 10)):
    count, total_sum, c01, c05, c1, cinf = ttft
    return f'''# HELP vllm:num_requests_running Requests running.
# TYPE vllm:num_requests_running gauge
vllm:num_requests_running{{model_name="private-model"}} {running}
# TYPE vllm:num_requests_waiting gauge
vllm:num_requests_waiting {waiting}
# TYPE vllm:kv_cache_usage_perc gauge
vllm:kv_cache_usage_perc {kv}
# TYPE vllm:prefix_cache_queries counter
vllm:prefix_cache_queries {queries}
# TYPE vllm:prefix_cache_hits counter
vllm:prefix_cache_hits {hits}
# TYPE vllm:prompt_tokens_total counter
vllm:prompt_tokens_total {prompt}
# TYPE vllm:generation_tokens_total counter
vllm:generation_tokens_total {generated}
# TYPE vllm:num_preemptions_total counter
vllm:num_preemptions_total {preemptions}
# TYPE vllm:time_to_first_token_seconds histogram
vllm:time_to_first_token_seconds_bucket{{le="0.1",model_name="private-model"}} {c01}
vllm:time_to_first_token_seconds_bucket{{le="0.5",model_name="private-model"}} {c05}
vllm:time_to_first_token_seconds_bucket{{le="1.0",model_name="private-model"}} {c1}
vllm:time_to_first_token_seconds_bucket{{le="+Inf",model_name="private-model"}} {cinf}
vllm:time_to_first_token_seconds_sum{{model_name="private-model"}} {total_sum}
vllm:time_to_first_token_seconds_count{{model_name="private-model"}} {count}
'''


class ParserTests(unittest.TestCase):
    def test_parse_prometheus_labels_and_types(self):
        parsed = parse_prometheus('# HELP x help\n# TYPE x gauge\nx{model_name="llm\\\"private",engine="0"} 2.5\n')
        self.assertEqual(parsed.series[0].metric_type, "gauge")
        self.assertIn(('model_name', 'llm"private'), parsed.series[0].labels)

    def test_parser_rejects_duplicate_series_and_malformed_labels_but_keeps_nonfinite_samples_explicit(self):
        with self.assertRaisesRegex(TelemetryError, 'duplicate'):
            parse_prometheus('x 1\nx 2\n')
        self.assertTrue(math.isnan(parse_prometheus('# TYPE x gauge\nx NaN\n').series[0].value))
        with self.assertRaisesRegex(TelemetryError, 'label'):
            parse_prometheus('x{a="1",a="2"} 1\n')
        with self.assertRaisesRegex(TelemetryError, 'precede samples'):
            parse_prometheus('x 1\n# TYPE x gauge\n')
        with self.assertRaisesRegex(TelemetryError, 'byte limit'):
            parse_prometheus('x 1\n' * 1_000_000)

    def test_malformed_histogram_is_reported_without_quantiles(self):
        previous = parse_prometheus('# TYPE vllm:time_to_first_token_seconds histogram\n')
        current = parse_prometheus('''# TYPE vllm:time_to_first_token_seconds histogram
vllm:time_to_first_token_seconds_bucket{le="0.5"} 3
vllm:time_to_first_token_seconds_sum 1
vllm:time_to_first_token_seconds_count 2
''')
        result = compare_snapshots(previous, current, window_seconds=30)
        self.assertEqual(result.histograms[0].status, 'invalid_histogram')
        self.assertIsNone(result.histograms[0].p95_upper_bound_seconds)


class WindowComparisonTests(unittest.TestCase):
    def test_rates_cache_ratio_gauges_and_histogram_bounds(self):
        previous = parse_prometheus(snapshot_text())
        current = parse_prometheus(snapshot_text(running=4, waiting=3, kv=0.9, queries=100, hits=70,
                                                 prompt=140, generated=260, preemptions=3,
                                                 ttft=(20, 12, 5, 10, 18, 20)))
        result = compare_snapshots(previous, current, window_seconds=20)
        self.assertEqual(result.status, 'compared')
        gauges = {(item.family, item.series_id): item for item in result.gauges}
        running = next(item for item in result.gauges if item.family == 'requests_running')
        self.assertEqual(running.value, 4)
        cache = next(item for item in result.gauges if item.family == 'kv_cache_usage')
        self.assertEqual(cache.value, 0.9)
        generated = next(item for item in result.counters if item.family == 'generation_tokens')
        self.assertEqual(generated.rate_per_second, 3)
        preemptions = next(item for item in result.counters if item.family == 'preemptions')
        self.assertEqual(preemptions.rate_per_second, 0.1)
        ratio = next(item for item in result.derived if item.family == 'prefix_cache_hit_ratio')
        self.assertEqual(ratio.value, 1.0)
        ttft = result.histograms[0]
        self.assertEqual(ttft.status, 'matched')
        self.assertEqual(ttft.observations, 10)
        self.assertEqual(ttft.mean_seconds, 0.7)
        self.assertEqual(ttft.p50_upper_bound_seconds, 0.5)
        self.assertEqual(ttft.p95_upper_bound_seconds, 1.0)
        self.assertIn('upper bound', ttft.quantile_bound_explanation)
        serialized = json.dumps(result.to_dict())
        self.assertNotIn('private-model', serialized)
        self.assertNotIn('model_name', serialized)

    def test_counter_reset_missing_and_new_series_never_become_zero(self):
        previous = parse_prometheus('''# TYPE vllm:generation_tokens_total counter
vllm:generation_tokens_total{model_name="a"} 100
vllm:generation_tokens_total{model_name="removed"} 4
''')
        current = parse_prometheus('''# TYPE vllm:generation_tokens_total counter
vllm:generation_tokens_total{model_name="a"} 3
vllm:generation_tokens_total{model_name="new"} 5
''')
        result = compare_snapshots(previous, current, window_seconds=10)
        by_id = {row.series_id: row for row in result.counters}
        statuses = {row.status for row in result.counters}
        self.assertEqual(statuses, {'counter_reset', 'unmatched_series'})
        self.assertTrue(all(row.delta is None and row.rate_per_second is None for row in result.counters))
        self.assertEqual(result.status, 'partial_or_reset')

    def test_counter_metric_type_or_documented_alias_change_is_unmatched(self):
        previous = parse_prometheus('''# TYPE vllm:prompt_tokens counter
vllm:prompt_tokens 100
''')
        current = parse_prometheus('''# TYPE vllm:prompt_tokens_total counter
vllm:prompt_tokens_total 120
''')
        renamed = compare_snapshots(previous, current, window_seconds=10)
        self.assertEqual({row.status for row in renamed.counters}, {'unmatched_series'})
        self.assertTrue(all(row.rate_per_second is None for row in renamed.counters))
        wrong_type = parse_prometheus('''# TYPE vllm:prompt_tokens gauge
vllm:prompt_tokens 120
''')
        invalid = compare_snapshots(previous, wrong_type, window_seconds=10)
        self.assertEqual(invalid.counters[0].status, 'invalid_type')
        self.assertIsNone(invalid.counters[0].delta)

    def test_mismatched_series_or_bucket_shapes_do_not_create_histogram_rates(self):
        previous = parse_prometheus('''# TYPE vllm:time_to_first_token_seconds histogram
vllm:time_to_first_token_seconds_bucket{le="0.5",model_name="a"} 1
vllm:time_to_first_token_seconds_bucket{le="+Inf",model_name="a"} 2
vllm:time_to_first_token_seconds_sum{model_name="a"} 0.7
vllm:time_to_first_token_seconds_count{model_name="a"} 2
''')
        current = parse_prometheus('''# TYPE vllm:time_to_first_token_seconds histogram
vllm:time_to_first_token_seconds_bucket{le="1.0",model_name="a"} 2
vllm:time_to_first_token_seconds_bucket{le="+Inf",model_name="a"} 3
vllm:time_to_first_token_seconds_sum{model_name="a"} 1.0
vllm:time_to_first_token_seconds_count{model_name="a"} 3
''')
        result = compare_snapshots(previous, current, window_seconds=60)
        self.assertEqual(result.histograms[0].status, 'unmatched_buckets')
        self.assertIsNone(result.histograms[0].observations)
        with self.assertRaises(TelemetryError):
            compare_snapshots(previous, current, window_seconds=0)

    def test_cache_occupancy_is_never_reported_as_gpu_utilization(self):
        parsed = parse_prometheus('# TYPE vllm:kv_cache_usage_perc gauge\nvllm:kv_cache_usage_perc 1.2\n')
        result = compare_snapshots(parse_prometheus(''), parsed, window_seconds=1)
        gauge = result.gauges[0]
        self.assertEqual(gauge.family, 'kv_cache_usage')
        self.assertEqual(gauge.status, 'invalid_gauge')
        self.assertIsNone(gauge.value)


class CollectorTests(unittest.TestCase):
    def test_unconfigured_and_unsafe_endpoints_are_safe(self):
        self.assertEqual(collect_configured_telemetry({}).status, 'unconfigured')
        cases = (
            'http://example.com/metrics', 'ftp://localhost/metrics',
            'http://localhost/metrics?secret=oops', 'http://user:pass@localhost/metrics',
            'http://localhost/elsewhere',
        )
        for endpoint in cases:
            with self.subTest(endpoint=endpoint):
                result = collect_configured_telemetry({'VLLM_METRICS_URL': endpoint, 'VLLM_METRICS_TOKEN': 'private-token'})
                self.assertEqual(result.status, 'error')
                public = json.dumps(result.to_dict())
                self.assertNotIn(endpoint, public)
                self.assertNotIn('private-token', public)

    def test_loopback_collection_sends_server_secret_and_redacts_endpoint_labels(self):
        body = b'# TYPE vllm:num_requests_running gauge\nvllm:num_requests_running{model_name="private-model"} 4\n'
        seen = {'auth': None, 'target_hits': 0}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                if self.path == '/target':
                    seen['target_hits'] += 1
                if self.path != '/metrics':
                    self.send_response(404)
                    self.end_headers()
                    return
                seen['auth'] = self.headers.get('Authorization')
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; version=0.0.4')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            endpoint = 'http://127.0.0.1:%d/metrics' % server.server_port
            result = collect_configured_telemetry({'VLLM_METRICS_URL': endpoint, 'VLLM_METRICS_TOKEN': 'server-secret'})
            self.assertEqual(result.status, 'collected')
            self.assertEqual(seen['auth'], 'Bearer server-secret')
            public = json.dumps(result.to_dict())
            self.assertNotIn(endpoint, public)
            self.assertNotIn('server-secret', public)
            self.assertNotIn('private-model', public)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_redirect_is_not_followed_and_response_size_is_bounded(self):
        body = b'x 1\n'
        state = {'target_hits': 0}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                if self.path == '/target':
                    state['target_hits'] += 1
                    self.send_response(200)
                    self.end_headers()
                    return
                if self.path == '/metrics':
                    self.send_response(302)
                    self.send_header('Location', 'http://127.0.0.1:%d/target' % self.server.server_port)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header('Content-Length', '4')
                self.end_headers()
                self.wfile.write(body)

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            prefix = 'http://127.0.0.1:%d' % server.server_port
            redirect = collect_configured_telemetry({'VLLM_METRICS_URL': prefix + '/metrics'})
            self.assertEqual(redirect.status, 'error')
            self.assertEqual(state['target_hits'], 0)
            oversized = collect_configured_telemetry({'VLLM_METRICS_URL': prefix + '/large'}, max_bytes=2)
            self.assertEqual(oversized.status, 'error')
            self.assertIsNone(oversized.snapshot)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == '__main__':
    unittest.main()
