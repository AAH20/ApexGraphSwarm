"""Tests for the policy engine."""
import os
import sys
import unittest
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from policy_engine import (
    PolicyEngine,
    PolicyDecision,
    PolicyResult,
    Rule,
    RuleType,
    FieldRule,
    TimeRule,
    RateLimitRule,
    BudgetRule,
    PrincipalRule,
    SchemaValidator,
    ValidationError,
    RegoEngine,
    RegoResult,
)


class FieldRuleTests(unittest.TestCase):
    def test_eq_operator(self):
        rule = FieldRule(name="test", rule_type=RuleType.FIELD, effect="allow",
                         field="user.role", operator="eq", value="admin")
        self.assertTrue(rule.evaluate({"user": {"role": "admin"}}))
        self.assertFalse(rule.evaluate({"user": {"role": "user"}}))

    def test_gt_operator(self):
        rule = FieldRule(name="test", rule_type=RuleType.FIELD, effect="allow",
                         field="age", operator="gt", value=18)
        self.assertTrue(rule.evaluate({"age": 21}))
        self.assertFalse(rule.evaluate({"age": 18}))
        self.assertFalse(rule.evaluate({"age": 15}))

    def test_in_operator(self):
        rule = FieldRule(name="test", rule_type=RuleType.FIELD, effect="allow",
                         field="status", operator="in", value=["active", "pending"])
        self.assertTrue(rule.evaluate({"status": "active"}))
        self.assertTrue(rule.evaluate({"status": "pending"}))
        self.assertFalse(rule.evaluate({"status": "inactive"}))

    def test_contains_operator(self):
        rule = FieldRule(name="test", rule_type=RuleType.FIELD, effect="allow",
                         field="tags", operator="contains", value="urgent")
        self.assertTrue(rule.evaluate({"tags": ["urgent", "review"]}))
        self.assertFalse(rule.evaluate({"tags": ["review"]}))

    def test_regex_operator(self):
        rule = FieldRule(name="test", rule_type=RuleType.FIELD, effect="allow",
                         field="email", operator="regex", value=r"@example\.com$")
        self.assertTrue(rule.evaluate({"email": "user@example.com"}))
        self.assertFalse(rule.evaluate({"email": "user@other.com"}))

    def test_nested_field(self):
        rule = FieldRule(name="test", rule_type=RuleType.FIELD, effect="allow",
                         field="a.b.c", operator="eq", value=42)
        self.assertTrue(rule.evaluate({"a": {"b": {"c": 42}}}))
        self.assertFalse(rule.evaluate({"a": {"b": {"c": 41}}}))

    def test_missing_field(self):
        rule = FieldRule(name="test", rule_type=RuleType.FIELD, effect="allow",
                         field="missing", operator="eq", value="x")
        self.assertFalse(rule.evaluate({}))


class TimeRuleTests(unittest.TestCase):
    def test_time_window(self):
        rule = TimeRule(name="business_hours", rule_type=RuleType.TIME,
                        effect="allow", start_hour=9, end_hour=17)
        # Monday 10:00
        import time
        monday_10am = time.mktime((2024, 1, 15, 10, 0, 0, 0, 0, -1))
        monday_8am = time.mktime((2024, 1, 15, 8, 0, 0, 0, 0, -1))
        monday_6pm = time.mktime((2024, 1, 15, 18, 0, 0, 0, 0, -1))
        self.assertTrue(rule.evaluate({"now": monday_10am}))
        self.assertFalse(rule.evaluate({"now": monday_8am}))
        self.assertFalse(rule.evaluate({"now": monday_6pm}))

    def test_weekend_excluded(self):
        rule = TimeRule(name="weekday_only", rule_type=RuleType.TIME,
                        effect="allow", start_hour=0, end_hour=23,
                        days=(0, 1, 2, 3, 4))  # Mon-Fri
        import time
        saturday_noon = time.mktime((2024, 1, 13, 12, 0, 0, 0, 0, -1))
        monday_noon = time.mktime((2024, 1, 15, 12, 0, 0, 0, 0, -1))
        self.assertFalse(rule.evaluate({"now": saturday_noon}))
        self.assertTrue(rule.evaluate({"now": monday_noon}))


class RateLimitRuleTests(unittest.TestCase):
    def test_rate_limit_allows_under_limit(self):
        rule = RateLimitRule(name="rl", rule_type=RuleType.RATE_LIMIT,
                             effect="allow", key_field="user_id",
                             max_requests=3, window_seconds=60)
        ctx = {"user_id": "alice", "now": 1000.0}
        self.assertTrue(rule.evaluate(ctx))
        self.assertTrue(rule.evaluate(ctx))
        self.assertTrue(rule.evaluate(ctx))

    def test_rate_limit_denies_over_limit(self):
        rule = RateLimitRule(name="rl", rule_type=RuleType.RATE_LIMIT,
                             effect="allow", key_field="user_id",
                             max_requests=2, window_seconds=60)
        ctx = {"user_id": "bob", "now": 1000.0}
        self.assertTrue(rule.evaluate(ctx))
        self.assertTrue(rule.evaluate(ctx))
        self.assertFalse(rule.evaluate(ctx))

    def test_rate_limit_window_expires(self):
        rule = RateLimitRule(name="rl", rule_type=RuleType.RATE_LIMIT,
                             effect="allow", key_field="user_id",
                             max_requests=1, window_seconds=60)
        self.assertTrue(rule.evaluate({"user_id": "carol", "now": 1000.0}))
        self.assertFalse(rule.evaluate({"user_id": "carol", "now": 1000.0}))
        # After window expires
        self.assertTrue(rule.evaluate({"user_id": "carol", "now": 1061.0}))


class BudgetRuleTests(unittest.TestCase):
    def test_budget_allows_under_cap(self):
        rule = BudgetRule(name="budget", rule_type=RuleType.BUDGET,
                          effect="allow", max_budget_microusd=1000)
        self.assertTrue(rule.evaluate({"spent_microusd": 500, "requested_microusd": 400}))

    def test_budget_denies_over_cap(self):
        rule = BudgetRule(name="budget", rule_type=RuleType.BUDGET,
                          effect="allow", max_budget_microusd=1000)
        self.assertFalse(rule.evaluate({"spent_microusd": 500, "requested_microusd": 600}))

    def test_budget_exact_cap(self):
        rule = BudgetRule(name="budget", rule_type=RuleType.BUDGET,
                          effect="allow", max_budget_microusd=1000)
        self.assertTrue(rule.evaluate({"spent_microusd": 500, "requested_microusd": 500}))


class PrincipalRuleTests(unittest.TestCase):
    def test_allowed_principals(self):
        rule = PrincipalRule(name="admins", rule_type=RuleType.PRINCIPAL,
                             effect="allow",
                             allowed_principals=frozenset(["alice", "bob"]))
        self.assertTrue(rule.evaluate({"principal_id": "alice"}))
        self.assertTrue(rule.evaluate({"principal_id": "bob"}))
        self.assertFalse(rule.evaluate({"principal_id": "charlie"}))

    def test_denied_principals(self):
        rule = PrincipalRule(name="blocked", rule_type=RuleType.PRINCIPAL,
                             effect="deny",
                             denied_principals=frozenset(["eve"]))
        self.assertFalse(rule.evaluate({"principal_id": "eve"}))
        self.assertTrue(rule.evaluate({"principal_id": "alice"}))

    def test_custom_principal_field(self):
        rule = PrincipalRule(name="custom", rule_type=RuleType.PRINCIPAL,
                             effect="allow",
                             allowed_principals=frozenset(["admin"]),
                             principal_field="user.name")
        self.assertTrue(rule.evaluate({"user": {"name": "admin"}}))
        self.assertFalse(rule.evaluate({"user": {"name": "user"}}))


class SchemaValidatorTests(unittest.TestCase):
    def test_basic_type_validation(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        validator = SchemaValidator(schema)
        self.assertTrue(validator.is_valid({"name": "Alice"}))
        self.assertFalse(validator.is_valid({"name": 123}))

    def test_required_properties(self):
        schema = {
            "type": "object",
            "required": ["id", "name"],
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
            },
        }
        validator = SchemaValidator(schema)
        self.assertTrue(validator.is_valid({"id": 1, "name": "Alice"}))
        self.assertFalse(validator.is_valid({"id": 1}))
        self.assertFalse(validator.is_valid({"name": "Alice"}))

    def test_string_constraints(self):
        schema = {
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email"},
                "code": {"type": "string", "pattern": "^[A-Z]{3}$"},
            },
        }
        validator = SchemaValidator(schema)
        self.assertTrue(validator.is_valid({"email": "a@b.com", "code": "ABC"}))
        self.assertFalse(validator.is_valid({"email": "not-an-email", "code": "ABC"}))
        self.assertFalse(validator.is_valid({"email": "a@b.com", "code": "abc"}))

    def test_numeric_constraints(self):
        schema = {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
                "score": {"type": "number", "minimum": 0.0, "maximum": 100.0},
            },
        }
        validator = SchemaValidator(schema)
        self.assertTrue(validator.is_valid({"age": 25, "score": 95.5}))
        self.assertFalse(validator.is_valid({"age": -1, "score": 95.5}))
        self.assertFalse(validator.is_valid({"age": 25, "score": 101.0}))

    def test_array_constraints(self):
        schema = {
            "type": "object",
            "properties": {
                "tags": {"type": "array", "items": {"type": "string"},
                          "minItems": 1, "maxItems": 5},
            },
        }
        validator = SchemaValidator(schema)
        self.assertTrue(validator.is_valid({"tags": ["a"]}))
        self.assertTrue(validator.is_valid({"tags": ["a", "b", "c"]}))
        self.assertFalse(validator.is_valid({"tags": []}))
        self.assertFalse(validator.is_valid({"tags": ["a", "b", "c", "d", "e", "f"]}))

    def test_enum_validation(self):
        schema = {
            "type": "object",
            "properties": {
                "status": {"enum": ["active", "inactive", "pending"]},
            },
        }
        validator = SchemaValidator(schema)
        self.assertTrue(validator.is_valid({"status": "active"}))
        self.assertFalse(validator.is_valid({"status": "deleted"}))

    def test_nested_object_validation(self):
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "required": ["id"],
                    "properties": {
                        "id": {"type": "integer"},
                        "profile": {
                            "type": "object",
                            "properties": {
                                "bio": {"type": "string"},
                            },
                        },
                    },
                },
            },
        }
        validator = SchemaValidator(schema)
        self.assertTrue(validator.is_valid({"user": {"id": 1, "profile": {"bio": "hi"}}}))
        self.assertFalse(validator.is_valid({"user": {"profile": {"bio": "hi"}}}))

    def test_additional_properties(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "additionalProperties": False,
        }
        validator = SchemaValidator(schema)
        self.assertTrue(validator.is_valid({"name": "Alice"}))
        self.assertFalse(validator.is_valid({"name": "Alice", "extra": "value"}))

    def test_anyof_validation(self):
        schema = {
            "type": "object",
            "properties": {
                "value": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "integer"},
                    ],
                },
            },
        }
        validator = SchemaValidator(schema)
        self.assertTrue(validator.is_valid({"value": "text"}))
        self.assertTrue(validator.is_valid({"value": 42}))
        self.assertFalse(validator.is_valid({"value": True}))

    def test_oneof_validation(self):
        schema = {
            "type": "object",
            "properties": {
                "value": {
                    "oneOf": [
                        {"type": "number", "minimum": 0},
                        {"type": "number", "maximum": 0},
                    ],
                },
            },
        }
        validator = SchemaValidator(schema)
        self.assertTrue(validator.is_valid({"value": 5}))
        self.assertTrue(validator.is_valid({"value": -5}))
        self.assertFalse(validator.is_valid({"value": 0}))  # matches both

    def test_validation_result_errors(self):
        schema = {
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "integer"}},
        }
        validator = SchemaValidator(schema)
        result = validator.validate({"id": "not_a_number"})
        self.assertFalse(result.valid)
        self.assertTrue(len(result.errors) > 0)


class RegoEngineTests(unittest.TestCase):
    def test_simple_allow_policy(self):
        engine = RegoEngine()
        engine.load_policy("test", """
package test

allow {
    input.user.role == "admin"
}
""")
        result = engine.evaluate("test", {"user": {"role": "admin"}})
        self.assertTrue(result.allowed)

    def test_deny_non_admin(self):
        engine = RegoEngine()
        engine.load_policy("test", """
package test

allow {
    input.user.role == "admin"
}
""")
        result = engine.evaluate("test", {"user": {"role": "user"}})
        self.assertFalse(result.allowed)

    def test_complex_policy_with_and(self):
        engine = RegoEngine()
        engine.load_policy("test", """
package test

allow {
    input.user.role == "admin"
    input.user.active == true
}
""")
        result = engine.evaluate("test", {"user": {"role": "admin", "active": True}})
        self.assertTrue(result.allowed)
        result = engine.evaluate("test", {"user": {"role": "admin", "active": False}})
        self.assertFalse(result.allowed)

    def test_policy_with_or(self):
        engine = RegoEngine()
        engine.load_policy("test", """
package test

allow {
    input.user.role == "admin"
}

allow {
    input.user.role == "superuser"
}
""")
        self.assertTrue(engine.evaluate("test", {"user": {"role": "admin"}}).allowed)
        self.assertTrue(engine.evaluate("test", {"user": {"role": "superuser"}}).allowed)
        self.assertFalse(engine.evaluate("test", {"user": {"role": "user"}}).allowed)

    def test_policy_with_in_operator(self):
        engine = RegoEngine()
        engine.load_policy("test", """
package test

allow {
    input.method in ["GET", "HEAD"]
}
""")
        self.assertTrue(engine.evaluate("test", {"method": "GET"}).allowed)
        self.assertTrue(engine.evaluate("test", {"method": "HEAD"}).allowed)
        self.assertFalse(engine.evaluate("test", {"method": "POST"}).allowed)

    def test_policy_with_count(self):
        engine = RegoEngine()
        engine.load_policy("test", """
package test

allow {
    count(input.allowed_roles) > 0
}
""")
        self.assertTrue(engine.evaluate("test", {"allowed_roles": ["admin"]}).allowed)
        self.assertFalse(engine.evaluate("test", {"allowed_roles": []}).allowed)

    def test_policy_with_comparison(self):
        engine = RegoEngine()
        engine.load_policy("test", """
package test

allow {
    input.age >= 18
}
""")
        self.assertTrue(engine.evaluate("test", {"age": 21}).allowed)
        self.assertFalse(engine.evaluate("test", {"age": 17}).allowed)

    def test_policy_with_negation(self):
        engine = RegoEngine()
        engine.load_policy("test", """
package test

allow {
    not input.blocked
}
""")
        self.assertTrue(engine.evaluate("test", {"blocked": False}).allowed)
        self.assertFalse(engine.evaluate("test", {"blocked": True}).allowed)

    def test_policy_with_nested_ref(self):
        engine = RegoEngine()
        engine.load_policy("test", """
package test

allow {
    input.user.permissions.read == true
}
""")
        self.assertTrue(engine.evaluate("test", {"user": {"permissions": {"read": True}}}).allowed)
        self.assertFalse(engine.evaluate("test", {"user": {"permissions": {"read": False}}}).allowed)

    def test_policy_with_string_contains(self):
        engine = RegoEngine()
        engine.load_policy("test", """
package test

allow {
    contains(input.path, "/api/")
}
""")
        self.assertTrue(engine.evaluate("test", {"path": "/api/users"}).allowed)
        self.assertFalse(engine.evaluate("test", {"path": "/web/page"}).allowed)

    def test_load_policy_file(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rego', delete=False) as f:
            f.write("""
package test

allow {
    input.ok == true
}
""")
            f.flush()
            engine = RegoEngine()
            engine.load_policy_file("filetest", f.name)
            result = engine.evaluate("filetest", {"ok": True})
            self.assertTrue(result.allowed)
        os.unlink(f.name)

    def test_missing_module_raises(self):
        engine = RegoEngine()
        with self.assertRaises(Exception):
            engine.evaluate("nonexistent", {})

    def test_missing_rule_raises(self):
        engine = RegoEngine()
        engine.load_policy("test", """
package test

allow {
    true
}
""")
        with self.assertRaises(Exception):
            engine.evaluate("test", {}, rule="nonexistent")


class PolicyEngineIntegrationTests(unittest.TestCase):
    def test_engine_with_schema_validation(self):
        engine = PolicyEngine()
        engine.register_schema("request", {
            "type": "object",
            "required": ["principal_id", "action"],
            "properties": {
                "principal_id": {"type": "string", "minLength": 1},
                "action": {"enum": ["read", "write", "delete"]},
            },
        })
        engine.add_rule(FieldRule(
            name="valid_request", rule_type=RuleType.FIELD, effect="allow",
            field="principal_id", operator="gte", value="",
        ))
        result = engine.evaluate(
            {"principal_id": "alice", "action": "read"},
            schema="request",
        )
        self.assertTrue(result.decision.allowed)

    def test_engine_schema_validation_failure(self):
        engine = PolicyEngine()
        engine.register_schema("request", {
            "type": "object",
            "required": ["principal_id", "action"],
            "properties": {
                "principal_id": {"type": "string", "minLength": 1},
                "action": {"enum": ["read", "write", "delete"]},
            },
        })
        result = engine.evaluate(
            {"principal_id": "", "action": "read"},
            schema="request",
        )
        self.assertFalse(result.decision.allowed)
        self.assertIn("Schema validation failed", result.decision.reason)

    def test_engine_with_rules(self):
        engine = PolicyEngine()
        engine.add_rule(FieldRule(
            name="admin_only", rule_type=RuleType.FIELD, effect="allow",
            field="role", operator="eq", value="admin",
        ))
        result = engine.evaluate({"role": "admin"})
        self.assertTrue(result.decision.allowed)

        result = engine.evaluate({"role": "user"})
        self.assertFalse(result.decision.allowed)

    def test_engine_deny_rule_precedence(self):
        engine = PolicyEngine()
        engine.add_rule(FieldRule(
            name="allow_all", rule_type=RuleType.FIELD, effect="allow",
            field="id", operator="gte", value=0, priority=1,
        ))
        engine.add_rule(FieldRule(
            name="deny_blocked", rule_type=RuleType.FIELD, effect="deny",
            field="id", operator="eq", value=42, priority=10,
        ))
        # Blocked ID should be denied despite allow rule
        result = engine.evaluate({"id": 42})
        self.assertFalse(result.decision.allowed)
        self.assertEqual(result.decision.rule_name, "deny_blocked")

        # Other IDs should be allowed
        result = engine.evaluate({"id": 1})
        self.assertTrue(result.decision.allowed)

    def test_engine_with_rego(self):
        engine = PolicyEngine()
        engine.load_rego_policy("auth", """
package auth

allow {
    input.user.verified == true
}
""")
        result = engine.evaluate(
            {"user": {"verified": True}},
            rego_module="auth",
        )
        self.assertTrue(result.decision.allowed)

        result = engine.evaluate(
            {"user": {"verified": False}},
            rego_module="auth",
        )
        self.assertFalse(result.decision.allowed)

    def test_engine_combined_schema_rules_rego(self):
        engine = PolicyEngine()
        engine.register_schema("request", {
            "type": "object",
            "required": ["principal_id"],
            "properties": {
                "principal_id": {"type": "string"},
            },
        })
        engine.add_rule(PrincipalRule(
            name="known_users", rule_type=RuleType.PRINCIPAL, effect="allow",
            allowed_principals=frozenset(["alice", "bob"]),
        ))
        engine.load_rego_policy("extra", """
package extra

allow {
    input.extra_check == true
}
""")
        # Should pass all three stages
        result = engine.evaluate(
            {"principal_id": "alice", "extra_check": True},
            schema="request",
            rego_module="extra",
        )
        self.assertTrue(result.decision.allowed)

        # Should fail at schema stage
        result = engine.evaluate(
            {"extra_check": True},
            schema="request",
            rego_module="extra",
        )
        self.assertFalse(result.decision.allowed)

        # Should fail at rule stage
        result = engine.evaluate(
            {"principal_id": "charlie", "extra_check": True},
            schema="request",
            rego_module="extra",
        )
        self.assertFalse(result.decision.allowed)

        # Should fail at rego stage
        result = engine.evaluate(
            {"principal_id": "alice", "extra_check": False},
            schema="request",
            rego_module="extra",
        )
        self.assertFalse(result.decision.allowed)

    def test_engine_no_rules_allows_by_default(self):
        engine = PolicyEngine()
        result = engine.evaluate({"any": "thing"})
        self.assertTrue(result.decision.allowed)

    def test_engine_remove_rule(self):
        engine = PolicyEngine()
        engine.add_rule(FieldRule(
            name="test_rule", rule_type=RuleType.FIELD, effect="allow",
            field="x", operator="eq", value=1,
        ))
        self.assertTrue(engine.remove_rule("test_rule"))
        self.assertFalse(engine.remove_rule("test_rule"))
        # After removal, no rules remain so request is allowed
        result = engine.evaluate({"x": 1})
        self.assertTrue(result.decision.allowed)

    def test_engine_clear_rules(self):
        engine = PolicyEngine()
        engine.add_rule(FieldRule(
            name="r1", rule_type=RuleType.FIELD, effect="allow",
            field="x", operator="eq", value=1,
        ))
        engine.clear_rules()
        self.assertEqual(len(engine.rules), 0)

    def test_engine_rule_priority_ordering(self):
        engine = PolicyEngine()
        engine.add_rule(FieldRule(
            name="low", rule_type=RuleType.FIELD, effect="allow",
            field="x", operator="eq", value=1, priority=1,
        ))
        engine.add_rule(FieldRule(
            name="high", rule_type=RuleType.FIELD, effect="deny",
            field="x", operator="eq", value=1, priority=10,
        ))
        # High priority deny should match first
        result = engine.evaluate({"x": 1})
        self.assertFalse(result.decision.allowed)
        self.assertEqual(result.decision.rule_name, "high")

    def test_engine_validate_against_schema(self):
        engine = PolicyEngine()
        engine.register_schema("test", {"type": "object"})
        result = engine.validate_against_schema({"any": "thing"}, "test")
        self.assertTrue(result.valid)
        result = engine.validate_against_schema("string", "test")
        self.assertFalse(result.valid)

    def test_engine_validate_unregistered_schema(self):
        engine = PolicyEngine()
        with self.assertRaises(Exception):
            engine.validate_against_schema({}, "nonexistent")


if __name__ == "__main__":
    unittest.main()
