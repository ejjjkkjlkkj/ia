#!/usr/bin/env python3
"""Independent oracle checks for the deterministic complex benchmark suite.

This checks published expected outputs against separately implemented algorithms.
It does not execute or score any model adapter.
"""
from __future__ import annotations

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


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("benchmarks/complex_tasks.json")
    suite = json.loads(path.read_text(encoding="utf-8"))
    tasks = suite.get("tasks")
    if not isinstance(tasks, list):
        raise SystemExit("FAIL: tasks must be a list")
    by_id = {task.get("id"): task for task in tasks}
    if len(by_id) != len(tasks):
        raise SystemExit("FAIL: duplicate task IDs")
    failures = []
    for task_id, oracle in ORACLES.items():
        task = by_id.get(task_id)
        if task is None:
            failures.append(f"{task_id}: missing task")
            continue
        actual = oracle()
        expected = task.get("expected_output")
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
        raise SystemExit(1)
    print(f"PASS: {len(ORACLES)} independent oracle checks; adapter/model performance NOT_VALIDATED")


if __name__ == "__main__":
    main()
