"""Versioned, bounded JSON intermediate representation for the NEXORA prototype.

This is a serialization contract for the current AST subset, not machine code.
"""
from __future__ import annotations

import json
from typing import Any

IR_VERSION = 1
MAX_IR_BYTES = 1_000_000
MAX_NODES = 20_000
MAX_DEPTH = 256

class NEXORAIRError(ValueError):
    """Raised when NEXORA IR is malformed or exceeds safety bounds."""

def _node_to_object(node: Any, depth: int = 0, budget: list[int] | None = None) -> dict[str, Any]:
    from nexora_language import Node
    if budget is None:
        budget = [MAX_NODES]
    if depth > MAX_DEPTH:
        raise NEXORAIRError("IR nesting limit exceeded")
    budget[0] -= 1
    if budget[0] < 0:
        raise NEXORAIRError("IR node limit exceeded")
    if not isinstance(node, Node):
        raise NEXORAIRError("expected NEXORA AST node")
    return {
        "kind": node.kind,
        "value": node.value,
        "children": [_node_to_object(child, depth + 1, budget) for child in node.children],
    }

def _validate_node(obj: Any, depth: int, budget: list[int]) -> dict[str, Any]:
    if depth > MAX_DEPTH:
        raise NEXORAIRError("IR nesting limit exceeded")
    budget[0] -= 1
    if budget[0] < 0:
        raise NEXORAIRError("IR node limit exceeded")
    if not isinstance(obj, dict) or set(obj) != {"kind", "value", "children"}:
        raise NEXORAIRError("each IR node must contain exactly kind, value, children")
    kind, value, children = obj["kind"], obj["value"], obj["children"]
    if not isinstance(kind, str) or not isinstance(children, list):
        raise NEXORAIRError("invalid IR node field types")
    allowed = {
        "program": (None, None), "let": ("str", 1), "print": (None, 1),
        "expr": (None, 1), "number": ("number", 0), "string": ("str", 0),
        "boolean": ("bool", 0), "identifier": ("str", 0),
        "unary": ("unary_op", 1), "binary": ("binary_op", 2),
    }
    if kind not in allowed:
        raise NEXORAIRError(f"unknown IR node kind: {kind}")
    expected_value, expected_children = allowed[kind]
    if expected_value == "str" and not isinstance(value, str):
        raise NEXORAIRError(f"{kind} value must be a string")
    if expected_value == "number" and (not isinstance(value, int) or isinstance(value, bool)):
        raise NEXORAIRError("number value must be an integer")
    if expected_value == "bool" and not isinstance(value, bool):
        raise NEXORAIRError("boolean value must be a boolean")
    if expected_value == "unary_op" and value != "-":
        raise NEXORAIRError("unsupported unary operator")
    if expected_value == "binary_op" and value not in {"+", "-", "*", "/"}:
        raise NEXORAIRError("unsupported binary operator")
    if expected_value is None and value is not None:
        raise NEXORAIRError(f"{kind} node value must be null")
    if expected_children is not None and len(children) != expected_children:
        raise NEXORAIRError(f"{kind} node requires {expected_children} children")
    if kind == "program" and value is not None:
        raise NEXORAIRError("program value must be null")
    return {"kind": kind, "value": value,
            "children": [_validate_node(child, depth + 1, budget) for child in children]}

def encode_ast(ast: Any) -> str:
    """Serialize a parsed NEXORA AST to canonical, versioned JSON."""
    obj = _node_to_object(ast)
    validated = _validate_node(obj, 0, [MAX_NODES])
    envelope = {"format": "nexora-ir", "version": IR_VERSION, "ast": validated}
    data = json.dumps(envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(data.encode("utf-8")) > MAX_IR_BYTES:
        raise NEXORAIRError("IR byte limit exceeded")
    return data

def decode_ir(data: str) -> dict[str, Any]:
    """Validate a versioned IR document and return its AST object."""
    if not isinstance(data, str):
        raise NEXORAIRError("IR input must be text")
    if len(data.encode("utf-8")) > MAX_IR_BYTES:
        raise NEXORAIRError("IR byte limit exceeded")
    try:
        envelope = json.loads(data)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise NEXORAIRError("invalid IR JSON") from exc
    if not isinstance(envelope, dict) or set(envelope) != {"format", "version", "ast"}:
        raise NEXORAIRError("invalid IR envelope")
    if envelope["format"] != "nexora-ir" or envelope["version"] != IR_VERSION:
        raise NEXORAIRError("unsupported IR format or version")
    return _validate_node(envelope["ast"], 0, [MAX_NODES])


def execute_ir(data: str) -> list[Any]:
    """Execute validated IR using the same deliberately small semantics as NEXORA.

    No Python eval/exec, imports, filesystem, process, or network access are used.
    The IR is fully validated before execution; execution also has a statement
    budget so an oversized program cannot run indefinitely.
    """
    from nexora_language import NEXORARuntimeError

    ast = decode_ir(data)
    if ast["kind"] != "program":
        raise NEXORAIRError("IR root must be a program")

    environment: dict[str, Any] = {}
    output: list[Any] = []
    steps = [MAX_NODES]

    def step() -> None:
        steps[0] -= 1
        if steps[0] < 0:
            raise NEXORAIRError("IR execution step limit exceeded")

    def evaluate(node: dict[str, Any]) -> Any:
        step()
        kind, value, children = node["kind"], node["value"], node["children"]
        if kind in ("number", "string", "boolean"):
            return value
        if kind == "identifier":
            if value not in environment:
                raise NEXORARuntimeError(f"undefined variable: {value}")
            return environment[value]
        if kind == "unary":
            operand = evaluate(children[0])
            if not isinstance(operand, int) or isinstance(operand, bool):
                raise NEXORARuntimeError("unary '-' requires an integer")
            return -operand
        if kind == "binary":
            left, right = evaluate(children[0]), evaluate(children[1])
            if value == "+" and isinstance(left, str) and isinstance(right, str):
                result = left + right
                if len(result.encode("utf-8")) > MAX_IR_BYTES:
                    raise NEXORARuntimeError("string result exceeds IR safety limit")
                return result
            if (not isinstance(left, int) or isinstance(left, bool)
                    or not isinstance(right, int) or isinstance(right, bool)):
                raise NEXORARuntimeError(f"operator {value} requires integer operands")
            if value == "+": result = left + right
            elif value == "-": result = left - right
            elif value == "*": result = left * right
            elif value == "/":
                if right == 0:
                    raise NEXORARuntimeError("division by zero")
                return left / right
            else:
                raise NEXORAIRError("unsupported validated operator")
            if result.bit_length() > 4096:
                raise NEXORARuntimeError("integer result exceeds 4096-bit limit")
            return result
        raise NEXORAIRError(f"node {kind} is not an expression")

    for statement in ast["children"]:
        step()
        kind = statement["kind"]
        if kind == "let":
            name = statement["value"]
            if not isinstance(name, str) or not __import__("re").fullmatch(r"[^\\W\\d]\\w*", name, __import__("re").UNICODE):
                raise NEXORAIRError("invalid variable identifier")
            if name in environment:
                raise NEXORARuntimeError(f"variable already defined: {name}")
            environment[name] = evaluate(statement["children"][0])
        elif kind == "print":
            output.append(evaluate(statement["children"][0]))
        elif kind == "expr":
            evaluate(statement["children"][0])
        else:
            raise NEXORAIRError(f"node {kind} is not a statement")
    return output
