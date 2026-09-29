"""Policy-as-code engine with OPA/Rego integration and JSON Schema validation.

Zero-dependency Python 3.10+ policy engine for ApexGraphSwarm.
"""
from __future__ import annotations

from .engine import PolicyEngine, PolicyDecision, PolicyResult
from .rules import Rule, RuleType, FieldRule, TimeRule, RateLimitRule, BudgetRule, PrincipalRule
from .schema import SchemaValidator, ValidationError
from .rego import RegoEngine, RegoResult

__all__ = [
    "PolicyEngine",
    "PolicyDecision",
    "PolicyResult",
    "Rule",
    "RuleType",
    "FieldRule",
    "TimeRule",
    "RateLimitRule",
    "BudgetRule",
    "PrincipalRule",
    "SchemaValidator",
    "ValidationError",
    "RegoEngine",
    "RegoResult",
]
