#!/usr/bin/env python3
"""Compare our local model with a permitted black-box baseline on identical tasks.

No network access is performed by this runner. Adapter stdout is evaluated in
memory; raw third-party outputs are deliberately not persisted in the report.
This tool measures only the declared suite and does not establish global
superiority or grant rights to reuse the baseline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shlex
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON numeric constant: {value}")


def _json_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without Python's bool/int equality ambiguity."""
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_json_equal(left[k], right[k]) for k in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_json_equal(a, b) for a, b in zip(left, right))
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    return type(left) is type(right) and left == right


MAX_SUITE_BYTES = 4 * 1024 * 1024
MAX_TASKS = 1000
MAX_PROMPT_CHARS = 100_000
MAX_JSON_NESTING = 64


def _check_json_nesting(text: str, max_depth: int = MAX_JSON_NESTING) -> None:
    """Reject deeply nested input before handing it to the recursive JSON parser."""
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > max_depth:
                raise ValueError("Benchmark suite JSON nesting exceeds parser limit")
        elif character in "]}":
            depth -= 1


def load_suite(path: Path) -> tuple[dict[str, Any], bytes]:
    # Check metadata before reading so malformed or accidental huge suites cannot
    # consume unbounded memory in CI or on a developer workstation.
    if path.stat().st_size > MAX_SUITE_BYTES:
        raise ValueError(f"Benchmark suite exceeds {MAX_SUITE_BYTES} bytes")
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="strict")
    _check_json_nesting(text)
    try:
        suite = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
    except RecursionError as exc:
        raise ValueError("Benchmark suite JSON nesting exceeds parser limit") from exc
    if not isinstance(suite, dict):
        raise ValueError("Benchmark suite root must be a JSON object")
    if type(suite.get("schema_version")) is not int or suite["schema_version"] != 1 or not isinstance(suite.get("tasks"), list):
        raise ValueError("Unsupported suite schema; expected schema_version=1 and tasks[]")
    if not suite["tasks"]:
        raise ValueError("Benchmark suite must contain at least one task")
    if len(suite["tasks"]) > MAX_TASKS:
        raise ValueError(f"Benchmark suite exceeds {MAX_TASKS} tasks")
    seen: set[str] = set()
    for i, task in enumerate(suite["tasks"]):
        if not isinstance(task, dict):
            raise ValueError(f"tasks[{i}] must be an object")
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id.strip() or task_id in seen:
            raise ValueError(f"tasks[{i}] requires a unique non-empty id")
        seen.add(task_id)
        if not isinstance(task.get("prompt"), str) or "expected_output" not in task:
            raise ValueError(f"task {task_id!r} requires prompt and expected_output")
        if len(task["prompt"]) > MAX_PROMPT_CHARS:
            raise ValueError(f"task {task_id!r} prompt exceeds {MAX_PROMPT_CHARS} characters")
        try:
            task["prompt"].encode("utf-8", errors="strict")
            task_id.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise ValueError(f"task {task_id!r} contains invalid Unicode") from exc
        if not isinstance(task.get("category", "general"), str):
            raise ValueError(f"task {task_id!r} category must be text")
    return suite, raw


def parse_output(stdout: str) -> Any:
    value = json.loads(stdout, object_pairs_hook=_unique_object, parse_constant=_reject_json_constant)
    if not isinstance(value, dict) or "output" not in value:
        raise ValueError("adapter stdout must be a JSON object containing output")
    output = value["output"]
    if isinstance(output, str):
        try:
            return json.loads(output, object_pairs_hook=_unique_object, parse_constant=_reject_json_constant)
        except json.JSONDecodeError:
            return output
    return output


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(fraction * len(ordered)) - 1)
    return round(ordered[index], 6)


def run_one(command: list[str], task: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = {
        "task_id": task["id"],
        "category": task.get("category", "general"),
        "prompt": task["prompt"],
        "output_schema": "Emit one JSON object with an output field.",
    }
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            command, input=json.dumps(request, ensure_ascii=False) + "\n",
            text=True, capture_output=True, timeout=timeout, check=False, shell=False,
        )
        elapsed = time.perf_counter() - start
        if proc.returncode:
            return {"status": "FAIL", "reason": "nonzero_exit", "latency_seconds": round(elapsed, 6)}
        try:
            output = parse_output(proc.stdout)
        except (ValueError, json.JSONDecodeError):
            return {"status": "FAIL", "reason": "invalid_json_output", "latency_seconds": round(elapsed, 6)}
        return {
            "status": "PASS" if _json_equal(output, task["expected_output"]) else "FAIL",
            "reason": "exact_match" if _json_equal(output, task["expected_output"]) else "exact_mismatch",
            "latency_seconds": round(elapsed, 6),
            "output_sha256": hashlib.sha256(
                json.dumps(output, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
            ).hexdigest(),
        }
    except subprocess.TimeoutExpired:
        return {"status": "BLOCKED", "reason": "timeout", "latency_seconds": None}
    except OSError:
        return {"status": "BLOCKED", "reason": "adapter_not_executable", "latency_seconds": None}


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = [r["latency_seconds"] for r in results if isinstance(r.get("latency_seconds"), (int, float))]
    total = len(results)
    passed = sum(r["status"] == "PASS" for r in results)
    failed = sum(r["status"] == "FAIL" for r in results)
    blocked = sum(r["status"] == "BLOCKED" for r in results)
    return {
        "total_runs": total,
        "passed": passed,
        "failed": failed,
        "blocked": blocked,
        "exact_match_rate_percent": round(100 * passed / total, 3) if total else 0.0,
        "latency_seconds": {
            "median": round(statistics.median(latencies), 6) if latencies else None,
            "p95": percentile(latencies, 0.95),
            "min": round(min(latencies), 6) if latencies else None,
            "max": round(max(latencies), 6) if latencies else None,
        },
    }


def evaluate(command: list[str], tasks: list[dict[str, Any]], repeats: int, timeout: float) -> dict[str, Any]:
    by_task = []
    flat = []
    for task in tasks:
        runs = [run_one(command, task, timeout) for _ in range(repeats)]
        flat.extend(runs)
        by_task.append({
            "task_id": task["id"],
            "category": task.get("category", "general"),
            "summary": summarize(runs),
            "runs": runs,
        })
    categories: dict[str, list[dict[str, Any]]] = {}
    for task_result in by_task:
        categories.setdefault(task_result["category"], []).extend(task_result["runs"])
    return {
        "summary": summarize(flat),
        "categories": {key: summarize(value) for key, value in sorted(categories.items())},
        "tasks": by_task,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", default="benchmarks/complex_tasks.json")
    parser.add_argument("--our-command", required=True, help="Our local adapter command")
    parser.add_argument("--baseline-command", help="Optional permitted black-box comparison adapter")
    parser.add_argument("--our-label", default="project-owned-model")
    parser.add_argument("--baseline-label", default="external-black-box-baseline")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--output", default="reports/tool-comparison.json")
    args = parser.parse_args()
    if args.repeats < 1 or args.repeats > 100:
        parser.error("--repeats must be between 1 and 100")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be a finite number greater than zero")
    try:
        suite, raw_suite = load_suite(Path(args.suite))
        our_command = shlex.split(args.our_command)
        baseline_command = shlex.split(args.baseline_command) if args.baseline_command else None
        if not our_command or (args.baseline_command is not None and not baseline_command):
            parser.error("adapter command cannot be empty")
        if baseline_command and args.our_label == args.baseline_label:
            parser.error("--our-label and --baseline-label must be different")
        if not args.our_label.strip() or (baseline_command and not args.baseline_label.strip()):
            parser.error("system labels cannot be empty")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    tasks = suite["tasks"]
    result: dict[str, Any] = {
        "schema_version": 1,
        "evaluation_id": "tool-comparison-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "suite_id": suite.get("benchmark_id", Path(args.suite).stem),
        "suite_sha256": hashlib.sha256(raw_suite).hexdigest(),
        "suite_path": str(Path(args.suite)),
        "test_count": len(tasks),
        "repeats_per_task": args.repeats,
        "timeout_seconds": args.timeout,
        "method": "project-authored exact-match tasks; identical prompts and budgets; outputs not stored",
        "competitive_claim": "NOT_ESTABLISHED",
        "rights_notice": "Black-box evaluation only; does not authorize import, training, distillation, or redistribution.",
        "systems": {},
    }
    result["systems"][args.our_label] = evaluate(our_command, tasks, args.repeats, args.timeout)
    if baseline_command:
        result["systems"][args.baseline_label] = evaluate(baseline_command, tasks, args.repeats, args.timeout)
        our = result["systems"][args.our_label]["summary"]
        baseline = result["systems"][args.baseline_label]["summary"]
        result["paired_comparison"] = {
            "exact_match_rate_delta_percentage_points": round(
                our["exact_match_rate_percent"] - baseline["exact_match_rate_percent"], 3
            ),
            "interpretation": "Descriptive result for this suite only; not a significance test or global superiority claim.",
        }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Suite SHA-256: {result['suite_sha256']}")
    for label, system in result["systems"].items():
        summary = system["summary"]
        print(f"{label}: {summary['passed']}/{summary['total_runs']} exact matches; "
              f"{summary['failed']} FAIL; {summary['blocked']} BLOCKED; "
              f"median={summary['latency_seconds']['median']}s p95={summary['latency_seconds']['p95']}s")
    print("Competitive claim: NOT_ESTABLISHED")
    print(f"Report: {output}")
    return 0 if all(s["summary"]["blocked"] == 0 and s["summary"]["failed"] == 0 for s in result["systems"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
