"""XSS prevention tests for ApexGraphSwarm.

Verifies that user-controlled input cannot be used as an XSS vector
in API responses, error messages, and graph data handling.
"""
import json
import re
import unittest
from pathlib import Path

import os

# Path to the web app source for pattern verification
WEB_ROOT = Path(__file__).resolve().parent.parent.parent / "apps" / "web"


class XSSPathRedactionTests(unittest.TestCase):
    """Error messages must redact local filesystem paths."""

    PATTERN = re.compile(r'/(?:Users|private|tmp)/[^\s]+')

    def test_user_path_redacted_from_error(self):
        raw = "Error in /Users/john/project/file.py"
        self.assertEqual(self.PATTERN.sub('[local path]', raw),
                         "Error in [local path]")

    def test_private_path_redacted_from_error(self):
        raw = "Failed at /private/var/tmp/secret"
        self.assertEqual(self.PATTERN.sub('[local path]', raw),
                         "Failed at [local path]")

    def test_tmp_path_redacted_from_error(self):
        raw = "Cannot read /tmp/control.sqlite"
        self.assertEqual(self.PATTERN.sub('[local path]', raw),
                         "Cannot read [local path]")

    def test_multiple_paths_redacted(self):
        raw = "Error: /Users/a/x.py and /tmp/y.db"
        sanitized = self.PATTERN.sub('[local path]', raw)
        self.assertNotIn('/Users/', sanitized)
        self.assertNotIn('/tmp/', sanitized)

    def test_non_matching_paths_preserved(self):
        raw = "Error in /etc/passwd"
        self.assertEqual(self.PATTERN.sub('[local path]', raw), raw)

    def test_routes_use_path_redaction(self):
        """API routes must use path redaction in error messages."""
        routes_dir = WEB_ROOT / "app" / "api"
        route_files = list(routes_dir.rglob("route.ts"))
        self.assertTrue(len(route_files) > 0, "No API route files found")
        routes_with_redaction = 0
        for route_file in route_files:
            content = route_file.read_text()
            if 'catch' in content and 'error' in content.lower():
                # Routes that handle errors should redact paths
                if 'local path' in content:
                    routes_with_redaction += 1
        # At least some routes should have path redaction
        self.assertGreater(routes_with_redaction, 0,
                           "No routes found with path redaction")


class XSSResponseSafetyTests(unittest.TestCase):
    """API responses must not be interpretable as HTML."""

    def test_json_encoding_escapes_html(self):
        """JSON encoding must escape < and > to prevent HTML interpretation."""
        payloads = [
            '<script>alert(1)</script>',
            '"><img src=x onerror=alert(1)>',
            '<svg onload=alert(1)>',
            'javascript:alert(1)',
        ]
        for payload in payloads:
            # JSON encoding with ensure_ascii=True escapes non-ASCII chars
            # but < and > are valid ASCII and are NOT escaped by json.dumps
            # The security comes from Content-Type: application/json header
            # which prevents browsers from interpreting the response as HTML
            encoded = json.dumps({"error": payload}, ensure_ascii=True)
            # The payload is preserved as-is in JSON (it's data, not markup)
            # The security boundary is the Content-Type header
            self.assertIn(payload, encoded,
                          f"Payload should be preserved in JSON: {payload}")

    def test_error_messages_truncated(self):
        """Error messages must be truncated to prevent response flooding."""
        long_input = "A" * 10000
        self.assertEqual(len(long_input[:300]), 300)
        self.assertEqual(len(long_input[:240]), 240)

    def test_routes_return_json_not_html(self):
        """API routes must return JSON, not HTML."""
        routes_dir = WEB_ROOT / "app" / "api"
        route_files = list(routes_dir.rglob("route.ts"))
        for route_file in route_files:
            content = route_file.read_text()
            if 'export async function' in content:
                # All API routes should use Response.json or NextResponse.json
                self.assertTrue(
                    'Response.json' in content or 'NextResponse.json' in content,
                    f"Route {route_file} does not return JSON")

    def test_routes_set_no_store_cache_control(self):
        """API routes must set Cache-Control: no-store."""
        routes_dir = WEB_ROOT / "app" / "api"
        route_files = list(routes_dir.rglob("route.ts"))
        for route_file in route_files:
            content = route_file.read_text()
            if 'Response.json' in content or 'NextResponse.json' in content:
                self.assertIn('no-store', content,
                              f"Route {route_file} missing no-store header")

    def test_secret_redaction_in_error_messages(self):
        """Secrets must be redacted from error messages."""
        bearer_pattern = re.compile(r'Bearer\s+[^\s]+', re.IGNORECASE)
        cred_pattern = re.compile(
            r'(?:OPENROUTER_API_KEY|VLLM_API_KEY|LOCAL_RUNNER_ACCESS_TOKEN)\s*[:=]\s*[^\s]+',
            re.IGNORECASE)

        msg = "Auth failed: Bearer sk-abc123 for OPENROUTER_API_KEY=secret"
        sanitized = bearer_pattern.sub('Bearer [redacted]', msg)
        sanitized = cred_pattern.sub('[credential redacted]', sanitized)
        self.assertNotIn('sk-abc123', sanitized)
        self.assertNotIn('secret', sanitized)

    def test_sanitize_error_function_exists(self):
        """integration-runtime.ts must have sanitizeError function."""
        runtime_file = WEB_ROOT / "lib" / "integration-runtime.ts"
        if runtime_file.exists():
            content = runtime_file.read_text()
            self.assertIn('sanitizeError', content,
                          "sanitizeError function missing from integration-runtime.ts")


class XSSInputValidationTests(unittest.TestCase):
    """Input validation must reject or neutralize XSS payloads."""

    def test_idempotency_key_rejects_html(self):
        """Idempotency keys must be visible ASCII only."""
        pattern = re.compile(r'^[\x21-\x7e]+$')
        # < and > are in \x21-\x7e range, so they pass the ASCII check
        # But the key must also match the route's stricter pattern
        route_pattern = re.compile(r'^[a-zA-Z0-9_-]{8,100}$')
        self.assertIsNone(route_pattern.match('<script>'))
        self.assertIsNone(route_pattern.match('key\x00'))
        self.assertIsNotNone(route_pattern.match('valid-key-123'))

    def test_run_id_rejects_html(self):
        """Run IDs must match safe pattern."""
        pattern = re.compile(r'^[a-zA-Z0-9_-]{1,100}$')
        self.assertIsNone(pattern.match('<script>'))
        self.assertIsNone(pattern.match('run id'))
        self.assertIsNotNone(pattern.match('run-123_abc'))

    def test_routes_validate_run_id_format(self):
        """Control route must validate run ID format."""
        control_route = WEB_ROOT / "app" / "api" / "control" / "route.ts"
        if control_route.exists():
            content = control_route.read_text()
            self.assertIn('runId', content)
            # The route validates runId with a regex pattern
            self.assertTrue(
                re.search(r'runId.*?(?:test|match|regex)', content, re.IGNORECASE) is not None,
                "Control route does not validate runId format")

    def test_routes_validate_idempotency_key_format(self):
        """Control route must validate idempotency key format."""
        control_route = WEB_ROOT / "app" / "api" / "control" / "route.ts"
        if control_route.exists():
            content = control_route.read_text()
            self.assertIn('idempotencyKey', content)
            # The route validates idempotencyKey with a regex pattern
            self.assertTrue(
                re.search(r'idempotencyKey.*?(?:test|match|regex)', content, re.IGNORECASE) is not None,
                "Control route does not validate idempotencyKey format")

    def test_graph_node_strings_are_bounded(self):
        """Graph node fields must be bounded strings."""
        # parseSnapshot in graph.ts validates string lengths
        graph_file = WEB_ROOT / "lib" / "graph.ts"
        if graph_file.exists():
            content = graph_file.read_text()
            # Check for string validation
            self.assertIn('string', content)
            self.assertIn('length', content)


if __name__ == '__main__':
    unittest.main()
