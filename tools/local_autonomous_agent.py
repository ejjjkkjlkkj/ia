#!/usr/bin/env python3
"""Bounded local Ollama coding agent. No cloud, shell-generated commands, or auto-push.

Default mode is planning/dry-run. --apply permits a validated unified diff to be
applied to the current clean Git worktree; it never commits, pushes, merges, or
runs commands proposed by the model.
"""
from __future__ import annotations

import argparse
import json
import ipaddress
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from pathlib import Path
from typing import Any

DEFAULT_URL = "http://127.0.0.1:11434/api/chat"
MAX_TASK_CHARS = 12_000
MAX_RESPONSE_BYTES = 2_000_000
MAX_PATCH_BYTES = 500_000
FORBIDDEN_PATH_PARTS = {".git", ".env", "secrets", "credentials", "id_rsa"}
FORBIDDEN_SUFFIXES = {".exe", ".dll", ".so", ".dylib", ".bin", ".pt", ".pth", ".safetensors"}
SYSTEM_PROMPT = """You are a repository coding assistant working locally. Return ONLY one JSON object:
{"summary":"short explanation","patch":"unified diff or empty string","tests":["test intent"]}
Rules: produce a standard git unified diff with a/ and b/ paths; change only source, tests,
and documentation needed for the task. Never edit workflow/CI files, secrets, credentials,
lockfiles, binary/model weights, or files outside the repository. Do not include shell commands.
Do not claim tests passed. If unsure, return an empty patch and explain the blocker.
The caller validates and previews the patch; do not include markdown fences."""


class AgentError(Exception):
    pass


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        check=False,
    )
    if proc.returncode:
        raise AgentError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def clean_worktree(root: Path) -> None:
    if git(root, "status", "--porcelain"):
        raise AgentError("Worktree is not clean; commit or stash existing changes first.")
    if not git(root, "rev-parse", "--is-inside-work-tree") == "true":
        raise AgentError("Not a Git worktree.")


def validate_local_url(url: str) -> None:
    """Reject non-loopback Ollama endpoints so task/code cannot be sent to a remote host."""
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
        port = parsed.port
        if parsed.scheme != "http" or not host or parsed.username or parsed.password:
            raise ValueError
        if parsed.path not in {"/api/chat", ""} or parsed.query or parsed.fragment:
            raise ValueError
        if host.lower() == "localhost":
            pass
        elif not ipaddress.ip_address(host).is_loopback:
            raise ValueError
        if port is None or not 1 <= port <= 65535:
            raise ValueError
    except (ValueError, TypeError) as exc:
        raise AgentError("Ollama URL must be an HTTP loopback endpoint (localhost/127.0.0.1/::1) on an explicit port, with no credentials, query, or fragment.") from exc


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def call_ollama(url: str, model: str, task: str, timeout: int) -> dict[str, Any]:
    validate_local_url(url)
    if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= 900:
        raise AgentError("Timeout must be an integer from 1 to 900 seconds.")
    payload = json.dumps({
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task},
        ],
        "options": {"temperature": 0, "num_ctx": 8192},
    }).encode("utf-8")
    request = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.build_opener(_NoRedirect()).open(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise AgentError(f"Ollama local endpoint unavailable or timed out: {exc}") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise AgentError("Ollama response exceeded the configured size limit.")
    try:
        outer = json.loads(raw)
        message = outer["message"]["content"]
        result = json.loads(message)
    except (ValueError, KeyError, TypeError) as exc:
        raise AgentError("Ollama returned invalid response JSON.") from exc
    if not isinstance(result, dict) or not isinstance(result.get("summary"), str) or not isinstance(result.get("patch"), str):
        raise AgentError("Model response must contain string fields 'summary' and 'patch'.")
    if len(result["patch"].encode("utf-8")) > MAX_PATCH_BYTES:
        raise AgentError("Proposed patch exceeds 500 KiB.")
    return result


def validate_patch(patch: str, root: Path) -> None:
    if not patch.strip():
        raise AgentError("Model proposed no patch.")
    if "\x00" in patch or not patch.startswith("diff --git "):
        raise AgentError("Patch is not a standard git unified diff.")
    if re.search(r"(?im)^GIT binary patch$|^Binary files .* differ$", patch):
        raise AgentError("Binary patches are forbidden.")
    paths: list[str] = []
    active_path: str | None = None
    old_header_seen = False
    new_header_seen = False
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            if active_path is not None and not (old_header_seen and new_header_seen):
                raise AgentError(f"Incomplete file headers for: {active_path}")
            match = re.fullmatch(r"diff --git a/(.+) b/(.+)", line)
            if not match or match.group(1) != match.group(2):
                raise AgentError("Rename, copy, and non-standard diff paths are forbidden.")
            active_path = match.group(1)
            paths.append(active_path)
            old_header_seen = False
            new_header_seen = False
            continue
        if line.startswith("--- "):
            if active_path is None or old_header_seen:
                raise AgentError("Unexpected or duplicate old-file header.")
            header_path = line[4:].split("\\t", 1)[0]
            if header_path != "/dev/null" and header_path != f"a/{active_path}":
                raise AgentError("Old-file header does not match the validated diff path.")
            old_header_seen = True
        elif line.startswith("+++ "):
            if active_path is None or not old_header_seen or new_header_seen:
                raise AgentError("Unexpected or duplicate new-file header.")
            header_path = line[4:].split("\\t", 1)[0]
            if header_path != "/dev/null" and header_path != f"b/{active_path}":
                raise AgentError("New-file header does not match the validated diff path.")
            if header_path == "/dev/null" and line[4:].split("\\t", 1)[0] != "/dev/null":
                raise AgentError("Invalid deletion header.")
            new_header_seen = True
    if active_path is not None and not (old_header_seen and new_header_seen):
        raise AgentError(f"Incomplete file headers for: {active_path}")
    if not paths:
        raise AgentError("Patch contains no file changes.")
    for relative in paths:
        parts = Path(relative).parts
        path = Path(relative)
        if path.is_absolute() or not parts or ".." in parts:
            raise AgentError(f"Unsafe path: {relative}")
        if any(part.lower() in FORBIDDEN_PATH_PARTS for part in parts):
            raise AgentError(f"Protected path: {relative}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise AgentError(f"Binary/model artifact path forbidden: {relative}")
        if relative.startswith(".github/") or relative in {".gitignore", "pyproject.toml", "Cargo.lock", "package-lock.json"}:
            raise AgentError(f"Protected configuration path: {relative}")
        resolved = (root / path).resolve()
        if root.resolve() not in resolved.parents:
            raise AgentError(f"Path escapes repository: {relative}")


def apply_patch(root: Path, patch: str) -> None:
    validate_patch(patch, root)
    check = subprocess.run(
        ["git", "-C", str(root), "apply", "--check", "--"],
        input=patch, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
    )
    if check.returncode:
        raise AgentError(f"git apply --check rejected patch: {check.stderr.strip()}")
    applied = subprocess.run(
        ["git", "-C", str(root), "apply", "--"],
        input=patch, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
    )
    if applied.returncode:
        raise AgentError(f"Patch application failed: {applied.stderr.strip()}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--task-file", type=Path, required=True)
    parser.add_argument("--model", default=os.environ.get("OLLAMA_MODEL", "qwen3-coder:30b"))
    parser.add_argument("--url", default=os.environ.get("OLLAMA_URL", DEFAULT_URL))
    parser.add_argument("--timeout", type=int, default=180, help="Ollama request timeout in seconds (1..900)")
    parser.add_argument("--apply", action="store_true", help="apply validated patch; otherwise dry-run")
    args = parser.parse_args(argv)
    root = args.repo.resolve()
    task_path = args.task_file.resolve()
    try:
        if not task_path.is_file():
            raise AgentError(f"Task file not found: {task_path}")
        task = task_path.read_text(encoding="utf-8")
        if not task.strip() or len(task) > MAX_TASK_CHARS:
            raise AgentError(f"Task must contain 1..{MAX_TASK_CHARS} characters.")
        clean_worktree(root)
        result = call_ollama(args.url, args.model, task, args.timeout)
        print("SUMMARY:", result["summary"])
        if not result["patch"].strip():
            print("STATUS: BLOCKED — model returned no patch")
            return 2
        validate_patch(result["patch"], root)
        print("STATUS: PATCH_VALIDATED")
        print("PATCH_BEGIN")
        print(result["patch"], end="" if result["patch"].endswith("\n") else "\n")
        print("PATCH_END")
        if not args.apply:
            print("MODE: DRY_RUN — no repository files changed")
            return 0
        apply_patch(root, result["patch"])
        print("STATUS: PATCH_APPLIED — no commit, push, merge, or model-supplied commands executed")
        print("NEXT: run the project's documented test suite and review git diff before committing")
        return 0
    except (AgentError, OSError, UnicodeError, subprocess.TimeoutExpired) as exc:
        print(f"STATUS: BLOCKED — {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
