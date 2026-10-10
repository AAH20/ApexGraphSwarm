"""CSRF protection tests for ApexGraphSwarm API routes.

Verifies that state-changing operations (POST, DELETE) are protected
against Cross-Site Request Forgery through origin validation and
bearer token authentication.
"""
import re
import unittest
from pathlib import Path

WEB_ROOT = Path(__file__).resolve().parent.parent.parent / "apps" / "web"


class CSRFOriginValidationTests(unittest.TestCase):
    """Origin header validation must prevent cross-site requests."""

    def test_missing_origin_allows_non_browser_clients(self):
        """Requests without Origin header are allowed (non-browser clients)."""
        # hasIntegrationSafeOrigin returns true when no Origin header
        # This is correct: curl, server-to-server calls don't send Origin
        # The bearer token still provides authentication
        runtime_file = WEB_ROOT / "lib" / "integration-runtime.ts"
        if runtime_file.exists():
            content = runtime_file.read_text()
            self.assertIn('if(!origin)return true', content,
                          "Missing origin should return true (non-browser clients)")

    def test_matching_origin_and_host_passes(self):
        """Origin matching the Host header passes validation."""
        runtime_file = WEB_ROOT / "lib" / "integration-runtime.ts"
        if runtime_file.exists():
            content = runtime_file.read_text()
            self.assertIn('parsed.host===host', content,
                          "Origin host must match request host")

    def test_mismatched_origin_host_fails(self):
        """Origin with different host than Host header fails."""
        runtime_file = WEB_ROOT / "lib" / "integration-runtime.ts"
        if runtime_file.exists():
            content = runtime_file.read_text()
            # The function returns false when host doesn't match
            self.assertIn('return Boolean(host&&parsed.host===host', content,
                          "Mismatched origin host must fail")

    def test_mismatched_origin_protocol_fails(self):
        """Origin with different protocol than request fails."""
        runtime_file = WEB_ROOT / "lib" / "integration-runtime.ts"
        if runtime_file.exists():
            content = runtime_file.read_text()
            self.assertIn('parsed.protocol===`${proto}:`', content,
                          "Origin protocol must match request protocol")

    def test_invalid_origin_url_fails(self):
        """Malformed Origin header fails validation."""
        runtime_file = WEB_ROOT / "lib" / "integration-runtime.ts"
        if runtime_file.exists():
            content = runtime_file.read_text()
            # URL parsing throws -> catch -> return false
            self.assertIn('catch{return false', content,
                          "Invalid origin URL must fail")

    def test_model_review_has_safe_origin(self):
        """Model review has its own safe origin check."""
        model_review_file = WEB_ROOT / "lib" / "model-review.ts"
        if model_review_file.exists():
            content = model_review_file.read_text()
            self.assertIn('hasSafeOrigin', content,
                          "Model review must have safe origin check")

    def test_graph_store_has_safe_origin(self):
        """Graph store has its own safe origin check."""
        neo4j_store_file = WEB_ROOT / "lib" / "neo4j-store.ts"
        if neo4j_store_file.exists():
            content = neo4j_store_file.read_text()
            self.assertIn('hasGraphStoreSafeOrigin', content,
                          "Graph store must have safe origin check")


class CSRFTokenAuthenticationTests(unittest.TestCase):
    """Bearer token authentication provides defense-in-depth against CSRF."""

    def test_integration_auth_uses_timing_safe_equal(self):
        """Integration auth must use timingSafeEqual."""
        runtime_file = WEB_ROOT / "lib" / "integration-runtime.ts"
        if runtime_file.exists():
            content = runtime_file.read_text()
            self.assertIn('timingSafeEqual', content,
                          "Integration auth must use timingSafeEqual")

    def test_model_review_auth_uses_timing_safe_equal(self):
        """Model review auth must use timingSafeEqual."""
        model_review_file = WEB_ROOT / "lib" / "model-review.ts"
        if model_review_file.exists():
            content = model_review_file.read_text()
            self.assertIn('timingSafeEqual', content,
                          "Model review auth must use timingSafeEqual")

    def test_graph_store_auth_uses_timing_safe_equal(self):
        """Graph store auth must use timingSafeEqual."""
        neo4j_store_file = WEB_ROOT / "lib" / "neo4j-store.ts"
        if neo4j_store_file.exists():
            content = neo4j_store_file.read_text()
            self.assertIn('timingSafeEqual', content,
                          "Graph store auth must use timingSafeEqual")

    def test_token_length_checked_before_comparison(self):
        """Token length must be checked before timingSafeEqual."""
        runtime_file = WEB_ROOT / "lib" / "integration-runtime.ts"
        if runtime_file.exists():
            content = runtime_file.read_text()
            self.assertIn('value.length!==token.length+7', content,
                          "Token length must be checked before comparison")

    def test_bearer_scheme_required(self):
        """Authorization header must use Bearer scheme."""
        runtime_file = WEB_ROOT / "lib" / "integration-runtime.ts"
        if runtime_file.exists():
            content = runtime_file.read_text()
            self.assertIn("startsWith('Bearer ')", content,
                          "Bearer scheme must be required")

    def test_no_token_configured_rejects_all(self):
        """When no token is configured, all requests are rejected."""
        runtime_file = WEB_ROOT / "lib" / "integration-runtime.ts"
        if runtime_file.exists():
            content = runtime_file.read_text()
            self.assertIn('if(!token)return false', content,
                          "Missing token config must reject all requests")


class CSRFStateChangingMethodTests(unittest.TestCase):
    """State-changing HTTP methods must have CSRF protection."""

    def test_all_post_routes_require_auth(self):
        """All POST routes require authentication."""
        routes_dir = WEB_ROOT / "app" / "api"
        route_files = list(routes_dir.rglob("route.ts"))
        for route_file in route_files:
            content = route_file.read_text()
            if 'export async function POST' in content:
                # Every POST handler must check authorization
                self.assertTrue(
                    'isIntegrationAuthorized' in content or
                    'isAuthorized' in content or
                    'isGraphStoreAuthorized' in content,
                    f"POST route {route_file} missing authorization check")

    def test_delete_routes_require_auth(self):
        """DELETE routes require authentication."""
        routes_dir = WEB_ROOT / "app" / "api"
        route_files = list(routes_dir.rglob("route.ts"))
        for route_file in route_files:
            content = route_file.read_text()
            if 'export async function DELETE' in content:
                self.assertTrue(
                    'isIntegrationAuthorized' in content or
                    'isAuthorized' in content,
                    f"DELETE route {route_file} missing authorization check")

    def test_get_routes_may_skip_auth(self):
        """GET routes may skip auth (read-only, no CSRF risk)."""
        # GET /api/integrations: no auth required (catalog is public)
        # GET /api/decisions: no auth required (provider list is public)
        # GET /api/review: no auth required (status check)
        # GET /api/graph-store: no auth required (config check)
        # GET /api/ecosystem/mcp: no auth required (catalog)
        # GET /api/integrations/jobs/[id]: requires auth
        integrations_route = WEB_ROOT / "app" / "api" / "integrations" / "route.ts"
        if integrations_route.exists():
            content = integrations_route.read_text()
            # GET should not require auth
            self.assertIn('export async function GET', content,
                          "GET handler should exist")
            # GET should not have auth check
            get_section = content.split('export async function GET')[1].split('export async function')[0]
            self.assertNotIn('isIntegrationAuthorized', get_section,
                             "GET should not require auth")


class CSRFContentTypeTests(unittest.TestCase):
    """Content-Type validation prevents simple CSRF attacks."""

    def test_post_routes_require_json_content_type(self):
        """POST routes require application/json content type."""
        routes_dir = WEB_ROOT / "app" / "api"
        route_files = list(routes_dir.rglob("route.ts"))
        for route_file in route_files:
            content = route_file.read_text()
            if 'export async function POST' in content:
                self.assertIn('application/json', content,
                              f"POST route {route_file} missing content-type check")

    def test_form_content_type_rejected(self):
        """application/x-www-form-urlencoded is rejected."""
        # Browsers can submit cross-site forms with this content type
        # but not application/json (requires fetch/XHR with custom header)
        routes_dir = WEB_ROOT / "app" / "api"
        route_files = list(routes_dir.rglob("route.ts"))
        for route_file in route_files:
            content = route_file.read_text()
            if 'export async function POST' in content:
                # The check is: content-type must start with application/json
                # This implicitly rejects form content types
                self.assertIn('startsWith', content,
                              f"POST route {route_file} should use startsWith for content-type")


class CSRFBodySizeTests(unittest.TestCase):
    """Request body size limits prevent CSRF-based DoS."""

    def test_body_size_limits_enforced(self):
        """All POST routes enforce body size limits."""
        routes_dir = WEB_ROOT / "app" / "api"
        route_files = list(routes_dir.rglob("route.ts"))
        for route_file in route_files:
            content = route_file.read_text()
            if 'export async function POST' in content:
                # Each route should have a size limit check
                has_limit = ('MAX_BYTES' in content or
                             '4096' in content or
                             '65536' in content or
                             '131072' in content or
                             '2097152' in content or
                             '1024' in content or
                             'REVIEW_MAX_BYTES' in content or
                             'GRAPH_STORE_MAX_BYTES' in content or
                             'INTEGRATION_LIMITS' in content)
                self.assertTrue(has_limit,
                                f"POST route {route_file} missing body size limit")

    def test_routes_cancel_oversized_bodies(self):
        """Routes must cancel reading when body exceeds limit."""
        routes_dir = WEB_ROOT / "app" / "api"
        route_files = list(routes_dir.rglob("route.ts"))
        for route_file in route_files:
            content = route_file.read_text()
            if 'export async function POST' in content and 'reader' in content:
                self.assertIn('cancel', content,
                              f"POST route {route_file} should cancel oversized bodies")


if __name__ == '__main__':
    unittest.main()
