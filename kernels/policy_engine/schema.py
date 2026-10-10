"""JSON Schema validation for policy inputs and outputs.

Implements a subset of JSON Schema Draft-2020-12 sufficient for
policy validation without external dependencies.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


class ValidationError(Exception):
    """Raised when data fails schema validation."""

    def __init__(self, message: str, path: str = "", errors: list[str] | None = None):
        self.message = message
        self.path = path
        self.errors = errors or []
        super().__init__(message)


@dataclass
class ValidationResult:
    """Result of schema validation."""
    valid: bool
    errors: list[str] = field(default_factory=list)


class SchemaValidator:
    """Validate data against JSON Schema Draft-2020-12 subset."""

    def __init__(self, schema: dict[str, Any]):
        self.schema = schema

    def validate(self, data: Any, path: str = "") -> ValidationResult:
        """Validate data against the schema."""
        errors: list[str] = []
        self._validate_node(data, self.schema, path, errors)
        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def is_valid(self, data: Any) -> bool:
        """Quick check if data is valid."""
        return self.validate(data).valid

    def _validate_node(self, data: Any, schema: dict[str, Any], path: str, errors: list[str]) -> None:
        """Recursively validate a node."""
        if not isinstance(schema, dict):
            return

        # Type check
        if "type" in schema:
            self._validate_type(data, schema["type"], path, errors)

        # Enum check
        if "enum" in schema:
            if data not in schema["enum"]:
                errors.append(f"{path}: value {data!r} not in enum {schema['enum']}")

        # Const check
        if "const" in schema:
            if data != schema["const"]:
                errors.append(f"{path}: value {data!r} != const {schema['const']!r}")

        # Numeric constraints
        if isinstance(data, (int, float)) and not isinstance(data, bool):
            self._validate_number(data, schema, path, errors)

        # String constraints
        if isinstance(data, str):
            self._validate_string(data, schema, path, errors)

        # Array constraints
        if isinstance(data, list):
            self._validate_array(data, schema, path, errors)

        # Object constraints
        if isinstance(data, dict):
            self._validate_object(data, schema, path, errors)

        # Combinators
        self._validate_combinators(data, schema, path, errors)

    def _validate_type(self, data: Any, expected: str | list[str], path: str, errors: list[str]) -> None:
        """Validate data type."""
        types = expected if isinstance(expected, list) else [expected]
        type_map = {
            "null": lambda x: x is None,
            "boolean": lambda x: isinstance(x, bool),
            "object": lambda x: isinstance(x, dict),
            "array": lambda x: isinstance(x, list),
            "number": lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
            "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
            "string": lambda x: isinstance(x, str),
        }
        for t in types:
            if t in type_map and type_map[t](data):
                return
        errors.append(f"{path}: expected type {expected}, got {type(data).__name__}")

    def _validate_number(self, data: int | float, schema: dict[str, Any], path: str, errors: list[str]) -> None:
        """Validate numeric constraints."""
        if "minimum" in schema and data < schema["minimum"]:
            errors.append(f"{path}: {data} < minimum {schema['minimum']}")
        if "maximum" in schema and data > schema["maximum"]:
            errors.append(f"{path}: {data} > maximum {schema['maximum']}")
        if "exclusiveMinimum" in schema and data <= schema["exclusiveMinimum"]:
            errors.append(f"{path}: {data} <= exclusiveMinimum {schema['exclusiveMinimum']}")
        if "exclusiveMaximum" in schema and data >= schema["exclusiveMaximum"]:
            errors.append(f"{path}: {data} >= exclusiveMaximum {schema['exclusiveMaximum']}")
        if "multipleOf" in schema and schema["multipleOf"] != 0:
            if data % schema["multipleOf"] != 0:
                errors.append(f"{path}: {data} not multiple of {schema['multipleOf']}")

    def _validate_string(self, data: str, schema: dict[str, Any], path: str, errors: list[str]) -> None:
        """Validate string constraints."""
        if "minLength" in schema and len(data) < schema["minLength"]:
            errors.append(f"{path}: length {len(data)} < minLength {schema['minLength']}")
        if "maxLength" in schema and len(data) > schema["maxLength"]:
            errors.append(f"{path}: length {len(data)} > maxLength {schema['maxLength']}")
        if "pattern" in schema:
            if not re.search(schema["pattern"], data):
                errors.append(f"{path}: {data!r} does not match pattern {schema['pattern']!r}")
        if "format" in schema:
            self._validate_format(data, schema["format"], path, errors)

    def _validate_format(self, data: str, fmt: str, path: str, errors: list[str]) -> None:
        """Validate string format."""
        format_patterns = {
            "date-time": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$",
            "date": r"^\d{4}-\d{2}-\d{2}$",
            "time": r"^\d{2}:\d{2}:\d{2}(?:\.\d+)?$",
            "email": r"^[^@]+@[^@]+\.[^@]+$",
            "uri": r"^[a-zA-Z][a-zA-Z0-9+.-]*://",
            "uuid": r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        }
        if fmt in format_patterns:
            if not re.match(format_patterns[fmt], data):
                errors.append(f"{path}: {data!r} is not a valid {fmt}")

    def _validate_array(self, data: list[Any], schema: dict[str, Any], path: str, errors: list[str]) -> None:
        """Validate array constraints."""
        if "minItems" in schema and len(data) < schema["minItems"]:
            errors.append(f"{path}: {len(data)} items < minItems {schema['minItems']}")
        if "maxItems" in schema and len(data) > schema["maxItems"]:
            errors.append(f"{path}: {len(data)} items > maxItems {schema['maxItems']}")
        if schema.get("uniqueItems"):
            seen = set()
            for i, item in enumerate(data):
                key = repr(item)
                if key in seen:
                    errors.append(f"{path}: duplicate item at index {i}")
                seen.add(key)
        if "items" in schema:
            item_schema = schema["items"]
            for i, item in enumerate(data):
                self._validate_node(item, item_schema, f"{path}[{i}]", errors)

    def _validate_object(self, data: dict[str, Any], schema: dict[str, Any], path: str, errors: list[str]) -> None:
        """Validate object constraints."""
        if "required" in schema:
            for req in schema["required"]:
                if req not in data:
                    errors.append(f"{path}: missing required property {req!r}")
        if "minProperties" in schema and len(data) < schema["minProperties"]:
            errors.append(f"{path}: {len(data)} properties < minProperties {schema['minProperties']}")
        if "maxProperties" in schema and len(data) > schema["maxProperties"]:
            errors.append(f"{path}: {len(data)} properties > maxProperties {schema['maxProperties']}")
        if "properties" in schema:
            for key, prop_schema in schema["properties"].items():
                if key in data:
                    self._validate_node(data[key], prop_schema, f"{path}.{key}", errors)
        if "additionalProperties" in schema:
            additional = schema["additionalProperties"]
            known = set(schema.get("properties", {}).keys())
            for key in data:
                if key not in known:
                    if additional is False:
                        errors.append(f"{path}: additional property {key!r} not allowed")
                    elif isinstance(additional, dict):
                        self._validate_node(data[key], additional, f"{path}.{key}", errors)

    def _validate_combinators(self, data: Any, schema: dict[str, Any], path: str, errors: list[str]) -> None:
        """Validate combinators (allOf, anyOf, oneOf, not)."""
        if "allOf" in schema:
            for i, sub in enumerate(schema["allOf"]):
                self._validate_node(data, sub, f"{path}/allOf[{i}]", errors)
        if "anyOf" in schema:
            any_valid = False
            sub_errors: list[str] = []
            for sub in schema["anyOf"]:
                trial: list[str] = []
                self._validate_node(data, sub, path, trial)
                if not trial:
                    any_valid = True
                    break
                sub_errors.extend(trial)
            if not any_valid:
                errors.append(f"{path}: does not match anyOf schema")
                errors.extend(sub_errors)
        if "oneOf" in schema:
            match_count = 0
            for sub in schema["oneOf"]:
                trial: list[str] = []
                self._validate_node(data, sub, path, trial)
                if not trial:
                    match_count += 1
            if match_count != 1:
                errors.append(f"{path}: matches {match_count} oneOf schemas, expected exactly 1")
        if "not" in schema:
            trial: list[str] = []
            self._validate_node(data, schema["not"], path, trial)
            if not trial:
                errors.append(f"{path}: matches 'not' schema")
