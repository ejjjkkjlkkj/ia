#!/usr/bin/env python3
"""Repository-owned autonomous maintenance agent.

This is a bounded, auditable maintenance agent, not an LLM or a code-generation
model. It runs only a fixed allow-list of local validation tasks. It never
downloads models, calls cloud APIs, executes task-provided shell text, modifies
source files, commits, pushes, or merges. Generative coding remains BLOCKED until
a project-owned model and checkpoint pass their own validation gate.
"""
from __future__ import annotations

import argparse
import json
import os
import py_compile
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MAX_CYCLES = 100
MAX_INTERVAL = 3600


def _run(command: list[str], timeout: int = 300) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command, cwd=ROOT, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, timeout=timeout, check=False, shell=False,
            env={
                **os.environ,
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPATH": os.pathsep.join(
                    part for part in (str(ROOT / "src"), os.environ.get("PYTHONPATH", ""))
                    if part
                ),
            },
        )
        return {
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "returncode": result.returncode,
            "output_tail": result.stdout[-4000:],
        }
    except subprocess.TimeoutExpired:
        return {"status": "BLOCKED", "reason": "timeout", "timeout_seconds": timeout}
    except OSError as exc:
        return {"status": "BLOCKED", "reason": type(exc).__name__}


def run_cycle() -> dict[str, Any]:
    tasks: list[dict[str, Any]] = []
    py_files = sorted(
        p for p in ROOT.rglob("*.py")
        if not any(part in {".git", ".venv", "__pycache__", "build", "dist"} for part in p.parts)
    )
    syntax_errors = []
    for path in py_files:
        try:
            source = path.read_bytes()
            compile(source, str(path), "exec")
        except (OSError, SyntaxError, UnicodeError) as exc:
            syntax_errors.append({"path": str(path.relative_to(ROOT)), "error": type(exc).__name__})
    tasks.append({
        "id": "python-syntax",
        "status": "PASS" if not syntax_errors else "FAIL",
        "files_checked": len(py_files),
        "errors": syntax_errors[:100],
    })

    json_files = sorted(
        p for p in ROOT.rglob("*.json")
        if not any(part in {".git", ".venv", "__pycache__", "build", "dist"} for part in p.parts)
    )
    json_errors = []
    for path in json_files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            json_errors.append({"path": str(path.relative_to(ROOT)), "error": type(exc).__name__})
    tasks.append({
        "id": "json-syntax",
        "status": "PASS" if not json_errors else "FAIL",
        "files_checked": len(json_files),
        "errors": json_errors[:100],
    })

    tests_dir = ROOT / "tests"
    if tests_dir.is_dir():
        tasks.append({
            "id": "python-unittest-discovery",
            **_run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], timeout=900),
        })
    else:
        tasks.append({"id": "python-unittest-discovery", "status": "BLOCKED", "reason": "tests_directory_missing"})

    # Do not silently substitute a third-party model. This repository does not
    # yet expose a validated autonomous coding model/checkpoint contract.
    tasks.append({
        "id": "generative-coding",
        "status": "BLOCKED",
        "reason": "project-owned production model and validated checkpoint gate not implemented",
        "cloud_fallback": False,
        "source_mutation": False,
    })
    overall = "FAIL" if any(t["status"] == "FAIL" for t in tasks) else (
        "BLOCKED" if any(t["status"] == "BLOCKED" for t in tasks) else "PASS"
    )
    return {
        "schema_version": 1,
        "agent": "repository-owned-maintenance-agent",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository_root": str(ROOT),
        "overall_status": overall,
        "safety": {
            "network_access": False,
            "cloud_fallback": False,
            "arbitrary_shell_commands": False,
            "source_mutation": False,
            "git_write_operations": False,
            "hardware_or_firmware_operations": False,
        },
        "tasks": tasks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", default=".maintenance-report/autonomous-agent.json")
    parser.add_argument("--cycles", type=int, default=1, help=f"Number of cycles (1-{MAX_CYCLES})")
    parser.add_argument("--watch", action="store_true", help="Repeat until interrupted")
    parser.add_argument("--interval", type=int, default=300, help=f"Watch interval in seconds (1-{MAX_INTERVAL})")
    args = parser.parse_args()
    if not 1 <= args.cycles <= MAX_CYCLES:
        parser.error(f"--cycles must be between 1 and {MAX_CYCLES}")
    if not 1 <= args.interval <= MAX_INTERVAL:
        parser.error(f"--interval must be between 1 and {MAX_INTERVAL}")
    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = ROOT / report_path
    runs = []
    try:
        while True:
            report = run_cycle()
            runs.append(report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(
                {"schema_version": 1, "runs": runs}, ensure_ascii=False, indent=2
            ) + "\n", encoding="utf-8")
            print(f"{report['generated_at_utc']} overall={report['overall_status']}", flush=True)
            if report["overall_status"] == "FAIL":
                return 1
            if not args.watch and len(runs) >= args.cycles:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Agent stopped by operator; last report preserved.", flush=True)
    return 0 if runs and all(r["overall_status"] == "PASS" for r in runs) else 2


if __name__ == "__main__":
    raise SystemExit(main())
