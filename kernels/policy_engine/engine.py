"""Core policy engine that orchestrates rules, schemas, and Rego policies."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

try:
    from .rules import Rule, RuleType
    from .schema import SchemaValidator, ValidationResult, ValidationError
    from .rego import RegoEngine, RegoResult
except ImportError:
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_dir = str(_Path(__file__).resolve().parent)
    if _pkg_dir not in _sys.path:
        _sys.path.insert(0, _pkg_dir)
    from rules import Rule, RuleType
    from schema import SchemaValidator, ValidationResult, ValidationError
    from rego import RegoEngine, RegoResult


class PolicyEffect(Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass
class PolicyDecision:
    """Result of a policy evaluation."""
    allowed: bool
    reason: str
    rule_name: str = ""
    effect: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyResult:
    """Complete result of a policy evaluation."""
    decision: PolicyDecision
    validation: ValidationResult | None = None
    rego_result: RegoResult | None = None
    context: dict[str, Any] = field(default_factory=dict)


class PolicyEngine:
    """Main policy engine for ApexGraphSwarm.

    Combines:
    - JSON Schema validation for input/output
    - Configurable rules (field, time, rate limit, budget, principal)
    - OPA/Rego policy evaluation
    """

    def __init__(self):
        self._rules: list[Rule] = []
        self._schemas: dict[str, SchemaValidator] = {}
        self._rego = RegoEngine()
        self._default_effect: str = "deny"

    @property
    def rules(self) -> list[Rule]:
        return list(self._rules)

    @property
    def rego(self) -> RegoEngine:
        return self._rego

    def add_rule(self, rule: Rule) -> None:
        """Add a policy rule."""
        self._rules.append(rule)
        # Sort by priority (higher first)
        self._rules.sort(key=lambda r: r.priority, reverse=True)

    def remove_rule(self, name: str) -> bool:
        """Remove a rule by name. Returns True if found and removed."""
        for i, rule in enumerate(self._rules):
            if rule.name == name:
                self._rules.pop(i)
                return True
        return False

    def clear_rules(self) -> None:
        """Remove all rules."""
        self._rules.clear()

    def register_schema(self, name: str, schema: dict[str, Any]) -> None:
        """Register a JSON Schema for validation."""
        self._schemas[name] = SchemaValidator(schema)

    def load_rego_policy(self, name: str, source: str) -> None:
        """Load a Rego policy."""
        self._rego.load_policy(name, source)

    def load_rego_policy_file(self, name: str, path: str | Path) -> None:
        """Load a Rego policy from file."""
        self._rego.load_policy_file(name, path)

    def evaluate(
        self,
        context: dict[str, Any],
        *,
        schema: str | None = None,
        rego_module: str | None = None,
        rego_rule: str = "allow",
    ) -> PolicyResult:
        """Evaluate policy against context.

        Args:
            context: The evaluation context (e.g., request data)
            schema: Optional schema name to validate context against
            rego_module: Optional Rego module to evaluate
            rego_rule: Rule name within the Rego module (default: "allow")

        Returns:
            PolicyResult with decision and details
        """
        # Step 1: Schema validation
        validation_result = None
        if schema and schema in self._schemas:
            validation_result = self._schemas[schema].validate(context)
            if not validation_result.valid:
                return PolicyResult(
                    decision=PolicyDecision(
                        allowed=False,
                        reason=f"Schema validation failed: {'; '.join(validation_result.errors)}",
                        rule_name="schema_validation",
                        effect="deny",
                    ),
                    validation=validation_result,
                    context=context,
                )

        # Step 2: Rule evaluation (skip if no rules configured)
        if self._rules:
            rule_decision = self._evaluate_rules(context)
            if not rule_decision.allowed:
                return PolicyResult(
                    decision=rule_decision,
                    validation=validation_result,
                    context=context,
                )

        # Step 3: Rego evaluation
        rego_result = None
        if rego_module:
            try:
                rego_result = self._rego.evaluate(rego_module, context, rego_rule)
                if not rego_result.allowed:
                    return PolicyResult(
                        decision=PolicyDecision(
                            allowed=False,
                            reason=f"Rego policy denied: {rego_module}.{rego_rule}",
                            rule_name=f"{rego_module}.{rego_rule}",
                            effect="deny",
                        ),
                        validation=validation_result,
                        rego_result=rego_result,
                        context=context,
                    )
            except Exception as exc:
                return PolicyResult(
                    decision=PolicyDecision(
                        allowed=False,
                        reason=f"Rego evaluation error: {exc}",
                        rule_name=f"{rego_module}.{rego_rule}",
                        effect="deny",
                    ),
                    validation=validation_result,
                    context=context,
                )

        # All checks passed
        return PolicyResult(
            decision=PolicyDecision(
                allowed=True,
                reason="All policy checks passed",
                effect="allow",
            ),
            validation=validation_result,
            rego_result=rego_result,
            context=context,
        )

    def _evaluate_rules(self, context: dict[str, Any]) -> PolicyDecision:
        """Evaluate all rules against context."""
        if not self._rules:
            # Default deny if no rules configured
            return PolicyDecision(
                allowed=False,
                reason="No policy rules configured (default deny)",
                rule_name="default",
                effect="deny",
            )

        # Add timestamp if not present
        if "now" not in context:
            context = {**context, "now": time.time()}

        allow_matched = False

        # Evaluate rules in priority order
        for rule in self._rules:
            try:
                matched = rule.evaluate(context)
            except Exception as exc:
                return PolicyDecision(
                    allowed=False,
                    reason=f"Rule {rule.name!r} evaluation error: {exc}",
                    rule_name=rule.name,
                    effect="deny",
                )

            if matched:
                if rule.effect == "deny":
                    return PolicyDecision(
                        allowed=False,
                        reason=f"Denied by rule {rule.name!r}",
                        rule_name=rule.name,
                        effect="deny",
                        metadata={"rule_type": rule.rule_type.value, "description": rule.description},
                    )
                # allow rule matched — continue checking deny rules
                allow_matched = True

        if allow_matched:
            return PolicyDecision(
                allowed=True,
                reason="Allowed by policy rules",
                effect="allow",
            )

        return PolicyDecision(
            allowed=False,
            reason="No matching allow rule",
            effect="deny",
        )

    def validate_against_schema(self, data: Any, schema_name: str) -> ValidationResult:
        """Validate data against a registered schema."""
        if schema_name not in self._schemas:
            raise ValidationError(f"Schema {schema_name!r} not registered")
        return self._schemas[schema_name].validate(data)
