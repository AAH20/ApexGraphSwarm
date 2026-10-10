"""Policy rule definitions for the ApexGraphSwarm policy engine."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class RuleType(Enum):
    FIELD = "field"
    TIME = "time"
    RATE_LIMIT = "rate_limit"
    BUDGET = "budget"
    PRINCIPAL = "principal"


@dataclass(frozen=True)
class Rule:
    """Base policy rule."""
    name: str
    rule_type: RuleType
    effect: str  # "allow" or "deny"
    priority: int = 0
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Return True if this rule matches the context."""
        raise NotImplementedError


@dataclass(frozen=True)
class FieldRule(Rule):
    """Rule that checks a field value against a predicate."""
    field: str = ""
    operator: str = "eq"  # eq, ne, gt, lt, gte, lte, in, contains, regex
    value: Any = None

    def __post_init__(self):
        object.__setattr__(self, "rule_type", RuleType.FIELD)

    def evaluate(self, context: dict[str, Any]) -> bool:
        actual = _get_nested(context, self.field)
        if actual is None:
            return False
        return _compare(actual, self.operator, self.value)


@dataclass(frozen=True)
class TimeRule(Rule):
    """Rule that checks if current time falls within a window."""
    start_hour: int = 0  # 0-23
    end_hour: int = 23  # 0-23
    days: tuple[int, ...] = (0, 1, 2, 3, 4, 5, 6)  # Monday=0

    def __post_init__(self):
        object.__setattr__(self, "rule_type", RuleType.TIME)

    def evaluate(self, context: dict[str, Any]) -> bool:
        now = context.get("now", time.time())
        t = time.localtime(now)
        return t.tm_wday in self.days and self.start_hour <= t.tm_hour <= self.end_hour


@dataclass(frozen=True)
class RateLimitRule(Rule):
    """Rule that enforces a rate limit on a key."""
    key_field: str = "principal_id"
    max_requests: int = 100
    window_seconds: int = 60
    _counters: dict[str, list[float]] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "rule_type", RuleType.RATE_LIMIT)

    def evaluate(self, context: dict[str, Any]) -> bool:
        key = str(_get_nested(context, self.key_field, ""))
        now = context.get("now", time.time())
        window_start = now - self.window_seconds

        if key not in self._counters:
            self._counters[key] = []

        # Prune old entries
        self._counters[key] = [t for t in self._counters[key] if t > window_start]

        if len(self._counters[key]) >= self.max_requests:
            return False

        self._counters[key].append(now)
        return True


@dataclass(frozen=True)
class BudgetRule(Rule):
    """Rule that enforces a budget cap."""
    max_budget_microusd: int = 0
    spent_field: str = "spent_microusd"

    def __post_init__(self):
        object.__setattr__(self, "rule_type", RuleType.BUDGET)

    def evaluate(self, context: dict[str, Any]) -> bool:
        spent = _get_nested(context, self.spent_field, 0)
        requested = context.get("requested_microusd", 0)
        return (spent + requested) <= self.max_budget_microusd


@dataclass(frozen=True)
class PrincipalRule(Rule):
    """Rule that checks principal membership."""
    allowed_principals: frozenset[str] = frozenset()
    denied_principals: frozenset[str] = frozenset()
    principal_field: str = "principal_id"

    def __post_init__(self):
        object.__setattr__(self, "rule_type", RuleType.PRINCIPAL)

    def evaluate(self, context: dict[str, Any]) -> bool:
        principal = str(_get_nested(context, self.principal_field, ""))
        if principal in self.denied_principals:
            return False
        if self.allowed_principals and principal not in self.allowed_principals:
            return False
        return True


def _get_nested(obj: dict[str, Any], path: str, default: Any = None) -> Any:
    """Get a nested field value using dot notation."""
    parts = path.split(".")
    current: Any = obj
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return default
        if current is None:
            return default
    return current


def _compare(actual: Any, operator: str, expected: Any) -> bool:
    """Compare actual value against expected using the given operator."""
    if operator == "eq":
        return actual == expected
    if operator == "ne":
        return actual != expected
    if operator == "gt":
        return actual is not None and actual > expected
    if operator == "lt":
        return actual is not None and actual < expected
    if operator == "gte":
        return actual is not None and actual >= expected
    if operator == "lte":
        return actual is not None and actual <= expected
    if operator == "in":
        return actual in expected if isinstance(expected, (list, tuple, set, frozenset)) else False
    if operator == "contains":
        return expected in actual if isinstance(actual, (str, list, tuple, set, frozenset)) else False
    if operator == "regex":
        import re
        return bool(re.search(expected, str(actual))) if actual is not None else False
    return False
