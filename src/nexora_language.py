"""NEXORA language: safe, tiny reference interpreter prototype.

This is a deliberately small, deterministic language front end, not a compiler
or a claim of production/UEFI readiness.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from typing import Any

@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    offset: int

_TOKEN_RE = re.compile(
    r"(?P<SPACE>\s+)|(?P<COMMENT>//[^\n]*|\#[^\n]*)|"
    r"(?P<STRING>\"(?:\\.|[^\"\\])*\")|"
    r"(?P<NUMBER>\d+)|"
    r"(?P<IDENT>[^\W\d]\w*)|"
    r"(?P<OP>==|!=|<=|>=|[+*/=();,<>-])",
    re.UNICODE,
)

class NEXORASyntaxError(ValueError):
    pass

class NEXORARuntimeError(ValueError):
    pass

def tokenize(source: str) -> list[Token]:
    """Tokenize bounded UTF-8/Unicode source text; reject unknown characters."""
    try:
        if len(source.encode("utf-8")) > 1_000_000:
            raise NEXORASyntaxError("source byte limit exceeded")
    except UnicodeEncodeError as exc:
        raise NEXORASyntaxError("source contains invalid Unicode scalar values") from exc
    tokens: list[Token] = []
    pos = 0
    while pos < len(source):
        match = _TOKEN_RE.match(source, pos)
        if not match:
            raise NEXORASyntaxError(f"unexpected character at offset {pos}: {source[pos]!r}")
        kind = match.lastgroup or ""
        value = match.group()
        if kind not in ("SPACE", "COMMENT"):
            tokens.append(Token(kind, value, pos))
        pos = match.end()
    tokens.append(Token("EOF", "", len(source)))
    return tokens

@dataclass(frozen=True)
class Node:
    kind: str
    value: Any = None
    children: tuple["Node", ...] = ()

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens, self.i = tokens, 0

    def current(self) -> Token:
        return self.tokens[self.i]

    def accept(self, value: str) -> bool:
        if self.current().value == value:
            self.i += 1
            return True
        return False

    def require(self, value: str) -> Token:
        token = self.current()
        if token.value != value:
            raise NEXORASyntaxError(f"expected {value!r} at offset {token.offset}, got {token.value!r}")
        self.i += 1
        return token

    def parse(self) -> Node:
        statements = []
        while self.current().kind != "EOF":
            statements.append(self.statement())
            self.accept(";")
        return Node("program", children=tuple(statements))

    def statement(self) -> Node:
        token = self.current()
        if token.value == "let":
            self.i += 1
            name = self.current()
            if name.kind != "IDENT" or name.value in {"let", "print", "true", "false"}:
                raise NEXORASyntaxError(f"expected non-reserved identifier at offset {name.offset}")
            self.i += 1
            self.require("=")
            return Node("let", name.value, (self.expression(),))
        if token.value == "print":
            self.i += 1
            self.require("(")
            expr = self.expression()
            self.require(")")
            return Node("print", children=(expr,))
        return Node("expr", children=(self.expression(),))

    def expression(self) -> Node:
        node = self.term()
        while self.current().value in ("+", "-"):
            op = self.current().value
            self.i += 1
            node = Node("binary", op, (node, self.term()))
        return node

    def term(self) -> Node:
        node = self.unary()
        while self.current().value in ("*", "/"):
            op = self.current().value
            self.i += 1
            node = Node("binary", op, (node, self.unary()))
        return node

    def unary(self) -> Node:
        if self.accept("-"):
            return Node("unary", "-", (self.unary(),))
        return self.primary()

    def primary(self) -> Node:
        token = self.current()
        if self.accept("("):
            node = self.expression()
            self.require(")")
            return node
        if token.kind == "NUMBER":
            self.i += 1
            if len(token.value) > 1234:
                raise NEXORASyntaxError(f"integer literal exceeds 4096-bit limit at offset {token.offset}")
            return Node("number", int(token.value))
        if token.kind == "STRING":
            self.i += 1
            import json
            try:
                value = json.loads(token.value)
            except json.JSONDecodeError as exc:
                raise NEXORASyntaxError(f"invalid string at offset {token.offset}") from exc
            return Node("string", value)
        if token.kind == "IDENT":
            self.i += 1
            if token.value in ("true", "false"):
                return Node("boolean", token.value == "true")
            return Node("identifier", token.value)
        raise NEXORASyntaxError(f"expected expression at offset {token.offset}, got {token.value!r}")

def parse(source: str) -> Node:
    try:
        return Parser(tokenize(source)).parse()
    except RecursionError as exc:
        raise NEXORASyntaxError("maximum parser nesting depth exceeded") from exc

def run(source: str) -> list[Any]:
    """Interpret a source program and return values passed to print()."""
    tree = parse(source)
    environment: dict[str, Any] = {}
    output: list[Any] = []

    def evaluate(node: Node) -> Any:
        if node.kind in ("number", "string", "boolean"):
            return node.value
        if node.kind == "identifier":
            if node.value not in environment:
                raise NEXORARuntimeError(f"undefined variable: {node.value}")
            return environment[node.value]
        if node.kind == "unary":
            value = evaluate(node.children[0])
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise NEXORARuntimeError("unary '-' requires a number")
            return -value
        if node.kind == "binary":
            import math
            left, right = (evaluate(child) for child in node.children)
            if node.value == "+" and isinstance(left, str) and isinstance(right, str):
                result = left + right
                if len(result.encode("utf-8")) > 1_000_000:
                    raise NEXORARuntimeError("string result exceeds safety limit")
                return result
            numeric = lambda value: isinstance(value, (int, float)) and not isinstance(value, bool)
            if not numeric(left) or not numeric(right):
                raise NEXORARuntimeError(f"operator {node.value} requires numeric operands")
            try:
                if node.value == "+": result = left + right
                elif node.value == "-": result = left - right
                elif node.value == "*": result = left * right
                elif node.value == "/":
                    if right == 0: raise NEXORARuntimeError("division by zero")
                    result = left / right
                else:
                    raise NEXORARuntimeError(f"unsupported operator: {node.value}")
            except OverflowError as exc:
                raise NEXORARuntimeError("numeric operation exceeds supported range") from exc
            if isinstance(result, int) and result.bit_length() > 4096:
                raise NEXORARuntimeError("integer result exceeds 4096-bit limit")
            if isinstance(result, float) and not math.isfinite(result):
                raise NEXORARuntimeError("numeric result is not finite")
            return result
        raise NEXORARuntimeError(f"unsupported node: {node.kind}")

    try:
        for statement in tree.children:
            if statement.kind == "let":
                if statement.value in environment:
                    raise NEXORARuntimeError(f"variable already defined: {statement.value}")
                environment[statement.value] = evaluate(statement.children[0])
            elif statement.kind == "print":
                output.append(evaluate(statement.children[0]))
            elif statement.kind == "expr":
                evaluate(statement.children[0])
            else:
                raise NEXORARuntimeError(f"unsupported statement: {statement.kind}")
    except RecursionError as exc:
        raise NEXORARuntimeError("maximum evaluation depth exceeded") from exc
    return output
