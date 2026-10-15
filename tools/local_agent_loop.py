"""Bounded local Ollama coding loop. Requires a disposable, clean Git worktree."""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import time
import urllib.error
import urllib.request
import uuid

ROOT = pathlib.Path(os.environ.get("AGENT_WORKSPACE", ".")).resolve()
OLLAMA = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
MODEL = os.environ.get("OLLAMA_MODEL", "qwen3-coder:30b")
TASK_FILE = ROOT / "AGENT-TASK.md"
LOG_FILE = pathlib.Path(os.environ.get("AGENT_LOG_FILE", str(pathlib.Path.home() / ".ia-agent" / "runs.jsonl"))).expanduser().resolve()
SLEEP_SECONDS = max(60, min(int(os.environ.get("AGENT_SLEEP_SECONDS", "300")), 3600))
MAX_RUNS = max(1, min(int(os.environ.get("AGENT_MAX_RUNS", "12")), 100))
MAX_PATCH_BYTES = 200_000
ALLOWED_TESTS = [["python", "-m", "pytest", "-q"], ["python", "-m", "unittest", "discover", "-s", "tests"]]


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(ROOT), *args], text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=120, check=check)


def record(data: dict) -> None:
    with LOG_FILE.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n")


def clean_workspace() -> None:
    if not (ROOT / ".git").exists():
        raise RuntimeError("workspace is not a Git checkout")
    branch = git("branch", "--show-current").stdout.strip()
    if not branch or branch in {"main", "master"}:
        raise RuntimeError("refusing to work on main/master; use a dedicated branch")
    if git("status", "--porcelain").stdout.strip():
        raise RuntimeError("worktree must be clean before each run")


def ask_model(task: str) -> str:
    prompt = (
        "You are a cautious coding agent. Return ONLY a unified git diff, no markdown. "
        "Do not modify CI permissions, secrets, workflows, release configuration, or this runner. "
        "Do not add network calls, credential access, persistence, or destructive actions. "
        "Make the smallest testable change for this task. If unsafe or unclear, return NO_PATCH.\n"
        f"TASK:\n{task[:12000]}"
    )
    payload = json.dumps({"model": MODEL, "stream": False,
                          "options": {"temperature": 0},
                          "messages": [{"role": "user", "content": prompt}]}).encode()
    request = urllib.request.Request(OLLAMA + "/api/chat", data=payload,
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=180) as response:
        body = json.loads(response.read(2_000_000))
    return body.get("message", {}).get("content", "").strip()


def validate_patch(patch: str) -> None:
    if not patch or patch == "NO_PATCH":
        raise RuntimeError("model returned no patch")
    raw = patch.encode("utf-8")
    if len(raw) > MAX_PATCH_BYTES or not patch.startswith("diff --git "):
        raise RuntimeError("patch format/size rejected")
    for line in patch.splitlines():
        if line.startswith("+++ ") or line.startswith("--- "):
            path = line[4:].split("\t", 1)[0]
            if path == "/dev/null":
                continue
            path = path.removeprefix("a/").removeprefix("b/")
            if pathlib.PurePosixPath(path).is_absolute() or ".." in pathlib.PurePosixPath(path).parts:
                raise RuntimeError("unsafe patch path")
            if path.startswith((".github/workflows/", ".git/")) or path in {"AGENT-TASK.md", "agent-runs.jsonl", ".env", "secrets.json", "credentials.json"}:
                raise RuntimeError("protected path modification rejected")


def run_tests() -> tuple[int, str]:
    tests = ROOT / "tests"
    if not tests.is_dir():
        return 2, "BLOCKED: tests/ directory not found"
    result = subprocess.run(ALLOWED_TESTS[0], cwd=ROOT, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
    if result.returncode == 0:
        return 0, result.stdout[-12000:]
    fallback = subprocess.run(ALLOWED_TESTS[1], cwd=ROOT, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
    return fallback.returncode, (result.stdout + "\n--- unittest fallback ---\n" + fallback.stdout)[-12000:]


def once() -> None:
    run_id = str(uuid.uuid4())
    entry = {"run_id": run_id, "started_unix": int(time.time()), "model": MODEL}
    patch = ""
    applied = False
    try:
        clean_workspace()
        if not TASK_FILE.is_file():
            raise RuntimeError("AGENT-TASK.md missing; no task to execute")
        task = TASK_FILE.read_text(encoding="utf-8").strip()
        if not task:
            raise RuntimeError("AGENT-TASK.md is empty")
        patch = ask_model(task)
        validate_patch(patch)
        check = subprocess.run(["git", "-C", str(ROOT), "apply", "--check", "--"],
                               input=patch, text=True, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=60)
        if check.returncode:
            raise RuntimeError("git apply --check failed: " + check.stdout[-3000:])
        apply = subprocess.run(["git", "-C", str(ROOT), "apply", "--"],
                               input=patch, text=True, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=60)
        if apply.returncode:
            raise RuntimeError("git apply failed: " + apply.stdout[-3000:])
        applied = True
        code, output = run_tests()
        entry.update({"test_exit_code": code, "test_output": output})
        if code:
            rollback = subprocess.run(["git", "-C", str(ROOT), "apply", "-R", "--"],
                                      input=patch, text=True, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT, timeout=60)
            applied = False if rollback.returncode == 0 else True
            raise RuntimeError("tests failed; rollback exit code " + str(rollback.returncode))
        entry["status"] = "PATCH_AND_TESTS_PASS_REQUIRES_REVIEW"
        entry["changed_files"] = git("diff", "--name-only").stdout.splitlines()
        entry["diff_sha256"] = __import__("hashlib").sha256(patch.encode()).hexdigest()
    except Exception as exc:
        entry.update({"status": "BLOCKED_OR_FAILED", "error": str(exc), "patch_applied": applied})
    finally:
        entry["finished_unix"] = int(time.time())
        record(entry)


def main() -> None:
    for _ in range(MAX_RUNS):
        once()
        time.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
    main()
