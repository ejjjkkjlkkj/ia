#!/usr/bin/env python3
"""Fast, read-only GitHub Actions triage for one exact commit.

Requires GitHub CLI (gh) authenticated for the target repository. It never
starts, cancels, reruns, or modifies workflows. Exit codes: 0 all matching runs
succeeded; 1 at least one run failed; 2 validation is incomplete or blocked.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from typing import Any

MAX_LIMIT = 100
MAX_WATCH_SECONDS = 3600
MAX_INTERVAL_SECONDS = 60
FAILED_CONCLUSIONS = {"failure", "timed_out", "action_required", "startup_failure"}
INCOMPLETE_CONCLUSIONS = {"cancelled", "skipped", "neutral", "stale"}


def fetch_runs(repo: str, sha: str, limit: int = 100) -> list[dict[str, Any]]:
    if not isinstance(repo, str) or repo.count("/") != 1 or any(part.strip() == "" for part in repo.split("/", 1)):
        raise ValueError("repo must use owner/name format")
    if not isinstance(sha, str) or len(sha) not in {40, 64} or any(c not in "0123456789abcdefABCDEF" for c in sha):
        raise ValueError("sha must be a full 40-character SHA-1 or 64-character SHA-256 hex string")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")
    if shutil.which("gh") is None:
        raise RuntimeError("GitHub CLI 'gh' is not installed")
    command = [
        "gh", "run", "list", "--repo", repo, "--commit", sha,
        "--limit", str(limit),
        "--json", "databaseId,name,status,conclusion,headSha,url,workflowName",
    ]
    try:
        result = subprocess.run(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, timeout=30, check=False, shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("gh run list timed out after 30 seconds") from exc
    if result.returncode:
        detail = result.stderr.strip()[-1000:] or f"gh exited with {result.returncode}"
        raise RuntimeError(detail)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("gh returned invalid JSON") from exc
    if not isinstance(payload, list):
        raise RuntimeError("gh returned an unexpected JSON shape")
    return [run for run in payload if isinstance(run, dict) and run.get("headSha") == sha]


def summarize(runs: list[dict[str, Any]]) -> tuple[str, dict[str, int]]:
    counts = {"success": 0, "failure": 0, "pending": 0}
    for run in runs:
        status = str(run.get("status", "")).lower()
        conclusion = str(run.get("conclusion") or "").lower()
        if status == "completed" and conclusion == "success":
            counts["success"] += 1
        elif status == "completed" and conclusion in FAILED_CONCLUSIONS:
            counts["failure"] += 1
        else:
            # Cancelled/skipped/neutral/stale runs did not prove success and
            # are not necessarily product/test failures. Keep them unvalidated.
            counts["pending"] += 1
    if counts["failure"]:
        overall = "FAIL"
    elif counts["pending"] or not runs:
        overall = "PENDING"
    else:
        overall = "PASS"
    return overall, counts


def report(runs: list[dict[str, Any]], sha: str) -> int:
    overall, counts = summarize(runs)
    print(f"commit={sha}")
    print(f"overall={overall} workflows={len(runs)} pass={counts['success']} fail={counts['failure']} pending={counts['pending']}")
    for run in sorted(runs, key=lambda item: str(item.get("name") or item.get("workflowName") or "").casefold()):
        name = run.get("name") or run.get("workflowName") or "unnamed workflow"
        status = str(run.get("status") or "unknown").upper()
        conclusion = str(run.get("conclusion") or "pending").upper()
        url = run.get("url") or ""
        print(f"{status:10} {conclusion:16} {name} {url}".rstrip())
    return {"PASS": 0, "FAIL": 1, "PENDING": 2}[overall]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="GitHub owner/name")
    parser.add_argument("--sha", required=True, help="Exact commit SHA to inspect")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--watch", type=int, default=0, metavar="SECONDS", help="Poll until settled or this many seconds elapse")
    parser.add_argument("--interval", type=int, default=15, help="Polling interval in seconds")
    args = parser.parse_args(argv)
    if not 0 <= args.watch <= MAX_WATCH_SECONDS:
        parser.error(f"--watch must be between 0 and {MAX_WATCH_SECONDS}")
    if not 1 <= args.interval <= MAX_INTERVAL_SECONDS:
        parser.error(f"--interval must be between 1 and {MAX_INTERVAL_SECONDS}")

    deadline = time.monotonic() + args.watch
    while True:
        try:
            runs = fetch_runs(args.repo, args.sha, args.limit)
        except (RuntimeError, ValueError) as exc:
            print(f"BLOCKED: {exc}", file=sys.stderr)
            return 2
        code = report(runs, args.sha)
        if code != 2 or args.watch == 0 or time.monotonic() >= deadline:
            return code
        time.sleep(min(args.interval, max(0, deadline - time.monotonic())))


if __name__ == "__main__":
    raise SystemExit(main())
