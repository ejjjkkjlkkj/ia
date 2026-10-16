#!/usr/bin/env python3
"""Independent oracle checks for the deterministic complex benchmark suite.

This checks published expected outputs against separately implemented algorithms.
It does not execute or score any model adapter.
"""
from __future__ import annotations

import argparse
import heapq
import itertools
import json
from fractions import Fraction
from pathlib import Path
import sys


def shortest_path():
    edges = {
        "A": [("B", 4), ("C", 2)],
        "C": [("B", 1), ("D", 8), ("E", 10)],
        "B": [("D", 5), ("E", 3)],
        "D": [("F", 2)],
        "E": [("F", 1)],
    }
    heap = [(0, 0, ("A",), "A")]
    best = {}
    while heap:
        cost, hops, path, node = heapq.heappop(heap)
        key = (cost, hops, path)
        if node in best and best[node] <= key:
            continue
        best[node] = key
        if node == "F":
            return {"path": list(path), "cost": cost}
        for nxt, weight in edges.get(node, []):
            heapq.heappush(heap, (cost + weight, hops + 1, path + (nxt,), nxt))
    raise AssertionError("F unreachable")


def topo_order():
    deps = {"A": ["C", "B"], "B": ["D"], "C": ["D"],
            "E": ["B", "C"], "F": ["E", "D"]}
    nodes = sorted(set(deps) | {x for values in deps.values() for x in values})
    remaining = {n: set(deps.get(n, [])) for n in nodes}
    result = []
    while remaining:
        available = min((n for n, needs in remaining.items() if not needs), default=None)
        if available is None:
            raise AssertionError("unexpected cycle")
        result.append(available)
        del remaining[available]
        for needs in remaining.values():
            needs.discard(available)
    return {"order": result}


def interval_union():
    intervals = sorted([[-9, -4], [-5, 0], [2, 4], [5, 8],
                        [12, 12], [11, 11], [20, 23], [23, 29]])
    merged = []
    for start, end in intervals:
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return {"intervals": merged}


def grid_paths():
    width, height = 8, 7
    blocked = {(2, 1), (2, 2), (3, 2), (5, 4), (6, 4), (6, 5)}
    dp = [[0] * (height + 1) for _ in range(width + 1)]
    for x in range(width + 1):
        for y in range(height + 1):
            if (x, y) in blocked:
                continue
            if (x, y) == (0, 0):
                dp[x][y] = 1
            else:
                dp[x][y] = (dp[x - 1][y] if x else 0) + (dp[x][y - 1] if y else 0)
    return {"paths": dp[width][height]}


def modular_arithmetic():
    mod = 1_000_000_007
    return {"value": (pow(7, 1_234_567, mod) + pow(11, 7_654_321, mod)) % mod}


def long_context():
    ledger = {"Vega": 23, "Hydra": 41, "Draco": 19, "Lyra": 31,
              "Phoenix": 37, "Cygnus": 29}
    value = (ledger["Vega"] * ledger["Hydra"] + ledger["Draco"] * ledger["Lyra"]) - (ledger["Phoenix"] + ledger["Cygnus"])
    return {"value": value, "used": ["Vega", "Hydra", "Draco", "Lyra", "Phoenix", "Cygnus"]}


def json_transform():
    rows = [{"id":"x3","score":8,"active":True},{"id":"x1","score":8,"active":False},
            {"id":"x2","score":11,"active":True},{"id":"x4","score":3,"active":True},
            {"id":"x5","score":11,"active":False}]
    active = sorted((r for r in rows if r["active"]), key=lambda r: (-r["score"], r["id"]))
    return {"items": [{"id": r["id"], "score": r["score"]} for r in active]}


def minimum_set_cover():
    universe = set("abcdefg")
    sets = {
        "S1": set("abcd"), "S2": set("ae"), "S3": set("bf"),
        "S4": set("cg"), "S5": set("def"), "S6": set("efg"), "S7": set("abg")
    }
    for size in range(1, len(sets) + 1):
        for combo in itertools.combinations(sorted(sets), size):
            if set().union(*(sets[name] for name in combo)) >= universe:
                return {"sets": list(combo)}
    raise AssertionError("no set cover")


def rational_sum():
    value = Fraction(1, 6) + Fraction(5, 14) - Fraction(7, 15) + Fraction(11, 21)
    return {"numerator": value.numerator, "denominator": value.denominator}


def state_machine():
    counter, stack = 0, []
    for command in ["INC", "INC", "PUSH", "ADD 7", "DEC", "PUSH",
                    "ADD -4", "POP", "MUL 3", "POP", "ADD 5", "DEC"]:
        if command == "INC":
            counter += 1
        elif command == "DEC":
            counter -= 1
        elif command == "PUSH":
            stack.append(counter)
        elif command == "POP":
            counter = stack.pop()
        elif command.startswith("ADD "):
            counter += int(command.split()[1])
        elif command.startswith("MUL "):
            counter *= int(command.split()[1])
        else:
            raise AssertionError("unknown command")
    return {"counter": counter, "stack": stack}


ORACLES = {
    "graph_shortest_path_01": shortest_path,
    "dependency_order_02": topo_order,
    "interval_union_03": interval_union,
    "dynamic_programming_04": grid_paths,
    "modular_arithmetic_05": modular_arithmetic,
    "long_context_retrieval_06": long_context,
    "json_schema_transform_07": json_transform,
    "set_cover_exact_08": minimum_set_cover,
    "robust_calculation_09": rational_sum,
    "state_machine_10": state_machine,
}


MAX_BENCHMARK_BYTES = 2_000_000
MAX_JSON_DEPTH = 64


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value):
    raise ValueError(f"non-standard JSON constant: {value}")


def _check_json_nesting(text):
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == chr(92):
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise ValueError("JSON nesting exceeds parser limit")
        elif character in "]}":
            depth -= 1
            if depth < 0:
                raise ValueError("malformed JSON nesting")


def load_suite(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_BENCHMARK_BYTES + 1)
    if len(raw) > MAX_BENCHMARK_BYTES:
        raise ValueError(f"benchmark suite exceeds {MAX_BENCHMARK_BYTES}-byte limit")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("benchmark suite must be valid UTF-8") from exc
    _check_json_nesting(text)
    suite = json.loads(
        text, object_pairs_hook=_unique_json_object, parse_constant=_reject_json_constant
    )
    if not isinstance(suite, dict) or type(suite.get("schema_version")) is not int or suite["schema_version"] != 1:
        raise ValueError("unsupported benchmark suite schema")
    tasks = suite.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("benchmark tasks must be a non-empty list")
    identifiers = []
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise ValueError(f"task at index {index} must be an object")
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError(f"task at index {index} must have a non-empty string id")
        if not isinstance(task.get("category"), str) or not task["category"]:
            raise ValueError(f"task {task_id} must have a non-empty category")
        if not isinstance(task.get("prompt"), str) or not task["prompt"]:
            raise ValueError(f"task {task_id} must have a non-empty prompt")
        if "expected_output" not in task:
            raise ValueError(f"task {task_id} is missing expected_output")
        identifiers.append(task_id)
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("benchmark task IDs must be unique")
    return suite


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", nargs="?", default="benchmarks/complex_tasks.json")
    args = parser.parse_args(argv)
    try:
        suite = load_suite(args.suite)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: invalid benchmark suite: {exc}")
        return 1

    by_id = {task["id"]: task for task in suite["tasks"]}
    failures = []
    for task_id, oracle in ORACLES.items():
        task = by_id.get(task_id)
        if task is None:
            failures.append(f"{task_id}: missing task")
            print(f"FAIL {task_id}: missing task")
            continue
        actual = oracle()
        expected = task["expected_output"]
        if actual != expected:
            failures.append(f"{task_id}: expected={expected!r}; independently_computed={actual!r}")
            print(f"FAIL {task_id}: expected={expected!r}; independently_computed={actual!r}")
        else:
            print(f"PASS {task_id}")
    unknown = sorted(set(by_id) - set(ORACLES))
    if unknown:
        print("FAIL: tasks missing independent oracles: " + ", ".join(unknown))
        failures.extend(f"{task_id}: no independent oracle registered" for task_id in unknown)
    if failures:
        print(f"FAIL: {len(failures)} oracle mismatch(es)")
        return 1
    print(f"PASS: {len(ORACLES)} independent oracle checks; adapter/model performance NOT_VALIDATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
