"""OPA/Rego policy engine integration.

Provides a pure-Python Rego parser and evaluator for basic OPA policies.
Supports a practical subset of Rego sufficient for policy-as-code use cases.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class RegoError(Exception):
    """Raised when Rego parsing or evaluation fails."""


@dataclass
class RegoResult:
    """Result of Rego evaluation."""
    allowed: bool
    value: Any = None
    bindings: dict[str, Any] = field(default_factory=dict)


# ── Tokenizer ──────────────────────────────────────────────────────────

@dataclass
class Token:
    type: str
    value: str
    pos: int


_KEYWORDS = {"package", "import", "default", "else", "some", "every", "not", "in"}
_OPERATORS = {"==", "!=", "<=", ">=", "<", ">", "=", ":=", "+", "-", "*", "/", "%"}
_PUNCT = {"{", "}", "[", "]", "(", ")", ",", ";", ".", ":"}


def _tokenize(source: str) -> list[Token]:
    """Tokenize Rego source code."""
    tokens: list[Token] = []
    i = 0
    n = len(source)

    while i < n:
        # Skip whitespace
        if source[i].isspace():
            i += 1
            continue

        # Skip comments
        if source[i] == "#":
            while i < n and source[i] != "\n":
                i += 1
            continue

        # String literals
        if source[i] == '"':
            j = i + 1
            while j < n and source[j] != '"':
                if source[j] == "\\":
                    j += 1
                j += 1
            tokens.append(Token("STRING", source[i:j + 1], i))
            i = j + 1
            continue

        # Numbers
        if source[i].isdigit():
            j = i
            while j < n and (source[j].isdigit() or source[j] == "."):
                j += 1
            tokens.append(Token("NUMBER", source[i:j], i))
            i = j
            continue

        # Identifiers and keywords
        if source[i].isalpha() or source[i] == "_":
            j = i
            while j < n and (source[j].isalnum() or source[j] in "_-"):
                j += 1
            word = source[i:j]
            if word in _KEYWORDS:
                tokens.append(Token("KEYWORD", word, i))
            else:
                tokens.append(Token("IDENT", word, i))
            i = j
            continue

        # Multi-char operators
        if source[i:i + 2] in ("==", "!=", "<=", ">=", ":="):
            tokens.append(Token("OP", source[i:i + 2], i))
            i += 2
            continue

        # Single-char operators
        if source[i] in _OPERATORS:
            tokens.append(Token("OP", source[i], i))
            i += 1
            continue

        # Punctuation
        if source[i] in _PUNCT:
            tokens.append(Token("PUNCT", source[i], i))
            i += 1
            continue

        # Unknown character
        raise RegoError(f"Unexpected character {source[i]!r} at position {i}")

    tokens.append(Token("EOF", "", n))
    return tokens


# ── AST Nodes ──────────────────────────────────────────────────────────

@dataclass
class Node:
    pass


@dataclass
class StringLit(Node):
    value: str


@dataclass
class NumberLit(Node):
    value: int | float


@dataclass
class BoolLit(Node):
    value: bool


@dataclass
class NullLit(Node):
    pass


@dataclass
class ArrayLit(Node):
    items: list[Node]


@dataclass
class ObjectLit(Node):
    pairs: list[tuple[Node, Node]]


@dataclass
class Ref(Node):
    path: list[Any]  # list of str or Node (for array indices)


@dataclass
class Var(Node):
    name: str


@dataclass
class Call(Node):
    func: str
    args: list[Node]


@dataclass
class BinExpr(Node):
    op: str
    left: Node
    right: Node


@dataclass
class NotExpr(Node):
    expr: Node


@dataclass
class RuleBody(Node):
    statements: list[Node]


@dataclass
class Rule:
    name: str
    ref: list[str]
    body: RuleBody
    default: bool = False


@dataclass
class Module:
    package: str
    imports: list[dict[str, str | None]]
    rules: list[Rule]


# ── Parser ─────────────────────────────────────────────────────────────

class _Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, type_: str, value: str | None = None) -> Token:
        tok = self.peek()
        if tok.type != type_ or (value is not None and tok.value != value):
            raise RegoError(f"Expected {type_} {value!r}, got {tok.type} {tok.value!r} at {tok.pos}")
        return self.advance()

    def parse_module(self) -> Module:
        """Parse a complete Rego module."""
        package = ""
        imports: list[dict[str, str | None]] = []
        rules: list[Rule] = []

        while self.peek().type != "EOF":
            tok = self.peek()

            if tok.type == "KEYWORD" and tok.value == "package":
                self.advance()
                package = self._parse_ref_path()
            elif tok.type == "KEYWORD" and tok.value == "import":
                self.advance()
                path = self._parse_ref_path()
                alias = None
                if self.peek().type == "KEYWORD" and self.peek().value == "as":
                    self.advance()
                    alias = self.expect("IDENT").value
                imports.append({"path": path, "alias": alias})
            elif tok.type == "KEYWORD" and tok.value == "default":
                self.advance()
                name = self.expect("IDENT").value
                self.expect("OP", ":=")
                body = self._parse_rule_body()
                rules.append(Rule(name=name, ref=[name], body=body, default=True))
            elif tok.type == "IDENT":
                rule = self._parse_rule()
                rules.append(rule)
            else:
                raise RegoError(f"Unexpected token {tok.type} {tok.value!r} at {tok.pos}")

        return Module(package=package, imports=imports, rules=rules)

    def _parse_ref_path(self) -> str:
        """Parse a dotted reference path like 'input.user.role'."""
        parts = [self.expect("IDENT").value]
        while self.peek().type == "PUNCT" and self.peek().value == ".":
            self.advance()
            parts.append(self.expect("IDENT").value)
        return ".".join(parts)

    def _parse_rule(self) -> Rule:
        """Parse a rule definition."""
        name = self.expect("IDENT").value
        ref = [name]

        # Check for rule arguments
        if self.peek().type == "PUNCT" and self.peek().value == "[":
            self.advance()
            depth = 1
            while depth > 0:
                tok = self.advance()
                if tok.type == "PUNCT" and tok.value == "[":
                    depth += 1
                elif tok.type == "PUNCT" and tok.value == "]":
                    depth -= 1

        # Check for rule value assignment
        if self.peek().type == "OP" and self.peek().value in (":=", "="):
            self.advance()
            body = self._parse_rule_body()
            return Rule(name=name, ref=ref, body=body)

        # Check for rule body with braces
        if self.peek().type == "PUNCT" and self.peek().value == "{":
            body = self._parse_rule_body()
            return Rule(name=name, ref=ref, body=body)

        raise RegoError(f"Expected rule body for {name!r}")

    def _parse_rule_body(self) -> RuleBody:
        """Parse a rule body (inside braces or after :=)."""
        self.expect("PUNCT", "{")

        statements: list[Node] = []
        while not (self.peek().type == "PUNCT" and self.peek().value == "}"):
            if self.peek().type == "EOF":
                raise RegoError("Unexpected EOF in rule body")
            stmt = self._parse_statement()
            statements.append(stmt)
            # Optional semicolon
            if self.peek().type == "PUNCT" and self.peek().value == ";":
                self.advance()

        self.expect("PUNCT", "}")
        return RuleBody(statements=statements)

    def _parse_statement(self) -> Node:
        """Parse a single statement in a rule body."""
        tok = self.peek()

        # Handle 'not' expression
        if tok.type == "KEYWORD" and tok.value == "not":
            self.advance()
            expr = self._parse_expr()
            return NotExpr(expr=expr)

        # Handle 'some' declarations
        if tok.type == "KEYWORD" and tok.value == "some":
            self.advance()
            while self.peek().type == "IDENT":
                self.advance()
                if self.peek().type == "PUNCT" and self.peek().value == ",":
                    self.advance()
            return self._parse_statement()

        # Handle 'every' comprehensions
        if tok.type == "KEYWORD" and tok.value == "every":
            self.advance()
            if self.peek().type == "PUNCT" and self.peek().value == "{":
                return self._parse_rule_body()
            return self._parse_statement()

        return self._parse_expr()

    def _parse_expr(self) -> Node:
        """Parse an expression with operator precedence."""
        return self._parse_or()

    def _parse_or(self) -> Node:
        """Parse || expressions."""
        left = self._parse_and()
        while self.peek().type == "OP" and self.peek().value == "||":
            self.advance()
            right = self._parse_and()
            left = BinExpr(op="||", left=left, right=right)
        return left

    def _parse_and(self) -> Node:
        """Parse && expressions."""
        left = self._parse_comparison()
        while self.peek().type == "OP" and self.peek().value == "&&":
            self.advance()
            right = self._parse_comparison()
            left = BinExpr(op="&&", left=left, right=right)
        return left

    def _parse_comparison(self) -> Node:
        """Parse comparison expressions."""
        left = self._parse_additive()
        while self.peek().type == "OP" and self.peek().value in ("==", "!=", "<", ">", "<=", ">="):
            op = self.advance().value
            right = self._parse_additive()
            left = BinExpr(op=op, left=left, right=right)
        # Handle 'in' operator
        if self.peek().type == "KEYWORD" and self.peek().value == "in":
            self.advance()
            right = self._parse_additive()
            left = BinExpr(op="in", left=left, right=right)
        return left

    def _parse_additive(self) -> Node:
        """Parse + and - expressions."""
        left = self._parse_multiplicative()
        while self.peek().type == "OP" and self.peek().value in ("+", "-"):
            op = self.advance().value
            right = self._parse_multiplicative()
            left = BinExpr(op=op, left=left, right=right)
        return left

    def _parse_multiplicative(self) -> Node:
        """Parse *, /, % expressions."""
        left = self._parse_primary()
        while self.peek().type == "OP" and self.peek().value in ("*", "/", "%"):
            op = self.advance().value
            right = self._parse_primary()
            left = BinExpr(op=op, left=left, right=right)
        return left

    def _parse_primary(self) -> Node:
        """Parse primary expressions."""
        tok = self.peek()

        # Parenthesized expression
        if tok.type == "PUNCT" and tok.value == "(":
            self.advance()
            expr = self._parse_expr()
            self.expect("PUNCT", ")")
            return expr

        # Array literal
        if tok.type == "PUNCT" and tok.value == "[":
            return self._parse_array()

        # Object literal
        if tok.type == "PUNCT" and tok.value == "{":
            return self._parse_object()

        # String literal
        if tok.type == "STRING":
            self.advance()
            raw = tok.value[1:-1]
            raw = raw.replace('\\"', '"').replace("\\\\", "\\").replace("\\n", "\n")
            return StringLit(value=raw)

        # Number literal
        if tok.type == "NUMBER":
            self.advance()
            if "." in tok.value:
                return NumberLit(value=float(tok.value))
            return NumberLit(value=int(tok.value))

        # Boolean literals
        if tok.type == "IDENT" and tok.value == "true":
            self.advance()
            return BoolLit(value=True)
        if tok.type == "IDENT" and tok.value == "false":
            self.advance()
            return BoolLit(value=False)
        if tok.type == "IDENT" and tok.value == "null":
            self.advance()
            return NullLit()

        # Identifier (variable, reference, or function call)
        if tok.type == "IDENT":
            return self._parse_ident()

        raise RegoError(f"Unexpected token {tok.type} {tok.value!r} at {tok.pos}")

    def _parse_ident(self) -> Node:
        """Parse an identifier (variable, reference, or function call)."""
        name = self.expect("IDENT").value

        # Function call
        if self.peek().type == "PUNCT" and self.peek().value == "(":
            self.advance()
            args: list[Node] = []
            if not (self.peek().type == "PUNCT" and self.peek().value == ")"):
                args.append(self._parse_expr())
                while self.peek().type == "PUNCT" and self.peek().value == ",":
                    self.advance()
                    args.append(self._parse_expr())
            self.expect("PUNCT", ")")
            return Call(func=name, args=args)

        # Reference (dotted path)
        path: list[Any] = [name]
        while self.peek().type == "PUNCT" and self.peek().value == ".":
            self.advance()
            path.append(self.expect("IDENT").value)

        # Check for array index
        while self.peek().type == "PUNCT" and self.peek().value == "[":
            self.advance()
            index = self._parse_expr()
            self.expect("PUNCT", "]")
            path.append(index)

        if len(path) == 1:
            return Var(name=name)
        return Ref(path=path)

    def _parse_array(self) -> ArrayLit:
        """Parse an array literal."""
        self.expect("PUNCT", "[")
        items: list[Node] = []
        if not (self.peek().type == "PUNCT" and self.peek().value == "]"):
            items.append(self._parse_expr())
            while self.peek().type == "PUNCT" and self.peek().value == ",":
                self.advance()
                items.append(self._parse_expr())
        self.expect("PUNCT", "]")
        return ArrayLit(items=items)

    def _parse_object(self) -> ObjectLit:
        """Parse an object literal."""
        self.expect("PUNCT", "{")
        pairs: list[tuple[Node, Node]] = []
        if not (self.peek().type == "PUNCT" and self.peek().value == "}"):
            key = self._parse_expr()
            self.expect("PUNCT", ":")
            val = self._parse_expr()
            pairs.append((key, val))
            while self.peek().type == "PUNCT" and self.peek().value == ",":
                self.advance()
                key = self._parse_expr()
                self.expect("PUNCT", ":")
                val = self._parse_expr()
                pairs.append((key, val))
        self.expect("PUNCT", "}")
        return ObjectLit(pairs=pairs)


# ── Evaluator ──────────────────────────────────────────────────────────

class _RegoUndefined(Exception):
    pass


class RegoEngine:
    """Evaluate Rego policies against input data."""

    def __init__(self):
        self._modules: dict[str, Module] = {}

    def load_policy(self, name: str, source: str) -> None:
        """Load a Rego policy from source text."""
        tokens = _tokenize(source)
        parser = _Parser(tokens)
        module = parser.parse_module()
        self._modules[name] = module

    def load_policy_file(self, name: str, path: str | Path) -> None:
        """Load a Rego policy from a file."""
        source = Path(path).read_text(encoding="utf-8")
        self.load_policy(name, source)

    def evaluate(self, module: str, input_data: dict[str, Any], rule: str = "allow") -> RegoResult:
        """Evaluate a Rego rule against input data."""
        if module not in self._modules:
            raise RegoError(f"Module {module!r} not loaded")

        mod = self._modules[module]
        targets = [r for r in mod.rules if r.name == rule]

        if not targets:
            raise RegoError(f"Rule {rule!r} not found in module {module!r}")

        context = {"input": input_data, "data": {}}

        # OPA semantics: multiple rules with the same name are OR'd together
        for target in targets:
            try:
                result = self._eval_body(target.body, context)
                if result:
                    return RegoResult(allowed=True, value=result)
            except _RegoUndefined:
                continue

        return RegoResult(allowed=False, value=False)

    def _eval_body(self, body: RuleBody, context: dict[str, Any]) -> bool:
        """Evaluate a rule body."""
        for stmt in body.statements:
            result = self._eval_node(stmt, context)
            if result is False or result is None:
                raise _RegoUndefined()
        return True

    def _eval_node(self, node: Node, context: dict[str, Any]) -> Any:
        """Evaluate an AST node."""
        if isinstance(node, StringLit):
            return node.value
        if isinstance(node, NumberLit):
            return node.value
        if isinstance(node, BoolLit):
            return node.value
        if isinstance(node, NullLit):
            return None
        if isinstance(node, ArrayLit):
            return [self._eval_node(item, context) for item in node.items]
        if isinstance(node, ObjectLit):
            return {self._eval_node(k, context): self._eval_node(v, context) for k, v in node.pairs}
        if isinstance(node, Var):
            return context.get(node.name)
        if isinstance(node, Ref):
            return self._resolve_ref(node.path, context)
        if isinstance(node, Call):
            return self._eval_call(node, context)
        if isinstance(node, NotExpr):
            try:
                result = self._eval_node(node.expr, context)
                return not result
            except _RegoUndefined:
                return True
        if isinstance(node, BinExpr):
            return self._eval_binexpr(node, context)
        if isinstance(node, RuleBody):
            return self._eval_body(node, context)
        raise RegoError(f"Unknown node type: {type(node).__name__}")

    def _eval_binexpr(self, node: BinExpr, context: dict[str, Any]) -> Any:
        """Evaluate a binary expression."""
        if node.op == "&&":
            left = self._eval_node(node.left, context)
            if left is False or left is None:
                raise _RegoUndefined()
            right = self._eval_node(node.right, context)
            return bool(left and right)
        if node.op == "||":
            try:
                left = self._eval_node(node.left, context)
                if left:
                    return True
            except _RegoUndefined:
                pass
            try:
                right = self._eval_node(node.right, context)
                return bool(right)
            except _RegoUndefined:
                raise _RegoUndefined()

        left = self._eval_node(node.left, context)
        right = self._eval_node(node.right, context)
        if left is None or right is None:
            raise _RegoUndefined()

        if node.op == "==":
            return left == right
        if node.op == "!=":
            return left != right
        if node.op == "<":
            return left < right
        if node.op == "<=":
            return left <= right
        if node.op == ">":
            return left > right
        if node.op == ">=":
            return left >= right
        if node.op == "+":
            return left + right
        if node.op == "-":
            return left - right
        if node.op == "*":
            return left * right
        if node.op == "/":
            return left / right
        if node.op == "%":
            return left % right
        if node.op == "in":
            if isinstance(right, list):
                return left in right
            if isinstance(right, dict):
                return left in right
            if isinstance(right, str):
                return str(left) in right
            raise _RegoUndefined()

        raise RegoError(f"Unknown operator: {node.op}")

    def _eval_call(self, node: Call, context: dict[str, Any]) -> Any:
        """Evaluate a built-in function call."""
        args = [self._eval_node(a, context) for a in node.args]

        if node.func == "count":
            if args and isinstance(args[0], (list, dict, str)):
                return len(args[0])
            return 0
        if node.func == "sum":
            if args and isinstance(args[0], list):
                return sum(args[0])
            return 0
        if node.func == "to_number":
            if args:
                try:
                    return int(args[0])
                except (ValueError, TypeError):
                    try:
                        return float(args[0])
                    except (ValueError, TypeError):
                        raise _RegoUndefined()
            raise _RegoUndefined()
        if node.func == "type_name":
            if not args:
                raise _RegoUndefined()
            val = args[0]
            if val is None:
                return "null"
            if isinstance(val, bool):
                return "boolean"
            if isinstance(val, (int, float)):
                return "number"
            if isinstance(val, str):
                return "string"
            if isinstance(val, list):
                return "array"
            if isinstance(val, dict):
                return "object"
            raise _RegoUndefined()
        if node.func == "contains":
            if len(args) >= 2 and isinstance(args[0], str):
                return args[1] in args[0]
            raise _RegoUndefined()
        if node.func == "startswith":
            if len(args) >= 2 and isinstance(args[0], str):
                return args[0].startswith(str(args[1]))
            raise _RegoUndefined()
        if node.func == "endswith":
            if len(args) >= 2 and isinstance(args[0], str):
                return args[0].endswith(str(args[1]))
            raise _RegoUndefined()

        raise RegoError(f"Unknown function: {node.func}")

    def _resolve_ref(self, path: list[Any], context: dict[str, Any]) -> Any:
        """Resolve a reference path against context."""
        current: Any = context
        for part in path:
            if isinstance(part, Node):
                part = self._eval_node(part, context)
            if isinstance(current, dict):
                current = current.get(str(part))
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    if 0 <= idx < len(current):
                        current = current[idx]
                    else:
                        raise _RegoUndefined()
                except (ValueError, TypeError):
                    raise _RegoUndefined()
            else:
                raise _RegoUndefined()
            if current is None:
                raise _RegoUndefined()
        return current
