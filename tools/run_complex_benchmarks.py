#!/usr/bin/env python3
"""Run the complex-first IA benchmark against a local model adapter.

The adapter receives one JSON request on stdin and must emit {"output": ...} on
stdout. No network calls, external models, or cloud services are used by this
runner. It records exact-match scores only for objective JSON tasks.
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_suite(path: Path) -> dict[str, Any]:
    suite = json.loads(path.read_text(encoding="utf-8"))
    if suite.get("schema_version") != 1 or not isinstance(suite.get("tasks"), list):
        raise ValueError("Unsupported benchmark suite schema")
    ids = [task.get("id") for task in suite["tasks"]]
    if len(ids) != len(set(ids)) or any(not isinstance(x, str) or not x for x in ids):
        raise ValueError("Task IDs must be unique non-empty strings")
    for task in suite["tasks"]:
        if not isinstance(task.get("prompt"), str) or "expected_output" not in task:
            raise ValueError(f"Invalid task: {task.get('id')}")
    return suite


def parse_adapter_output(stdout: str) -> Any:
    value = json.loads(stdout)
    if not isinstance(value, dict) or "output" not in value:
        raise ValueError("Adapter stdout must be a JSON object with an 'output' field")
    result = value["output"]
    if isinstance(result, str):
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return result
    return result


def run_task(command: list[str], task: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = {
        "task_id": task["id"],
        "category": task["category"],
        "prompt": task["prompt"],
        "output_schema": "Return only the requested JSON value wrapped in an object with key output.",
    }
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            command, input=json.dumps(request, ensure_ascii=False) + "\n",
            text=True, capture_output=True, timeout=timeout, check=False,
            shell=False,
        )
        elapsed = time.perf_counter() - started
        if proc.returncode != 0:
            return {"task_id": task["id"], "category": task["category"],
                    "status": "FAIL", "reason": "adapter_nonzero_exit",
                    "returncode": proc.returncode, "latency_seconds": round(elapsed, 4),
                    "stderr": proc.stderr[-2000:]}
        try:
            output = parse_adapter_output(proc.stdout)
        except (ValueError, json.JSONDecodeError) as exc:
            return {"task_id": task["id"], "category": task["category"],
                    "status": "FAIL", "reason": "invalid_adapter_json",
                    "detail": str(exc), "latency_seconds": round(elapsed, 4),
                    "stdout": proc.stdout[-2000:]}
        passed = output == task["expected_output"]
        return {"task_id": task["id"], "category": task["category"],
                "status": "PASS" if passed else "FAIL",
                "latency_seconds": round(elapsed, 4),
                "expected": task["expected_output"], "actual": output}
    except subprocess.TimeoutExpired:
        return {"task_id": task["id"], "category": task["category"],
                "status": "FAIL", "reason": "timeout", "timeout_seconds": timeout}
    except OSError as exc:
        return {"task_id": task["id"], "category": task["category"],
                "status": "BLOCKED", "reason": "adapter_not_executable", "detail": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", default="benchmarks/complex_tasks.json")
    parser.add_argument("--command", required=True,
                        help="Local adapter command; receives one JSON request on stdin.")
    parser.add_argument("--timeout", type=float, default=90)
    parser.add_argument("--output", default="reports/complex-benchmark.json")
    parser.add_argument("--list", action="store_true", help="List tasks without executing a model.")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be > 0")
    suite = load_suite(Path(args.suite))
    if args.list:
        for task in suite["tasks"]:
            print(f'{task["id"]}\t{task["category"]}')
        print(f'TOTAL_TASKS={len(suite["tasks"])}')
        return 0

    command = shlex.split(args.command)
    if not command:
        parser.error("--command must name an executable")
    results = [run_task(command, task, args.timeout) for task in suite["tasks"]]
    total = len(results)
    passed = sum(result["status"] == "PASS" for result in results)
    blocked = sum(result["status"] == "BLOCKED" for result in results)
    report = {
        "schema_version": 1,
        "benchmark_id": suite["benchmark_id"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "suite": str(Path(args.suite)),
        "total": total,
        "passed": passed,
        "failed": sum(result["status"] == "FAIL" for result in results),
        "blocked": blocked,
        "score_percent": round(100 * passed / total, 2) if total else 0,
        "competitive_claim": "NOT_ESTABLISHED",
        "results": results,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f'Benchmark: {passed}/{total} PASS; {report["failed"]} FAIL; {blocked} BLOCKED')
    print(f"Score: {report['score_percent']}% (does not establish competitive superiority)")
    print(f"Report: {output_path}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
