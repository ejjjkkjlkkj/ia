#!/usr/bin/env python3
"""Bounded local Ollama coding agent. No cloud, shell-generated commands, or auto-push.
Default mode is planning/dry-run. --apply permits a validated unified diff to be
applied to the current clean Git worktree; it never commits, pushes, merges, or
runs commands proposed by the model.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import ipaddress
import os
import re
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from pathlib import Path, PureWindowsPath
from typing import Any
DEFAULT_URL = "http://127.0.0.1:11434/api/chat"
MAX_TASK_CHARS = 12_000
MAX_RESPONSE_BYTES = 2_000_000
MAX_PATCH_BYTES = 500_000
FORBIDDEN_PATH_PARTS = {".git", ".env", "secrets", "credentials", "id_rsa"}
FORBIDDEN_SUFFIXES = {".exe", ".dll", ".so", ".dylib", ".bin", ".pt", ".pth", ".safetensors", ".pem", ".key", ".p12", ".pfx"}
ALLOWED_TEXT_SUFFIXES = {".py", ".rs", ".go", ".js", ".ts", ".tsx", ".jsx", ".c", ".h", ".cc", ".cpp", ".hpp", ".java", ".kt", ".swift", ".cs", ".php", ".rb", ".sh", ".ps1", ".md", ".rst", ".txt"}
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
    except (ValueError, KeyError, TypeError, RecursionError) as exc:
        raise AgentError("Ollama returned invalid response JSON or excessively nested JSON.") from exc
    if not isinstance(result, dict) or not isinstance(result.get("summary"), str) or not isinstance(result.get("patch"), str):
        raise AgentError("Model response must contain string fields 'summary' and 'patch'.")
    if len(result["patch"].encode("utf-8")) > MAX_PATCH_BYTES:
        raise AgentError("Proposed patch exceeds 500 KiB.")
    return result
def validate_patch(patch: str, root: Path) -> None:
    try:
        patch_size = len(patch.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise AgentError("Patch contains invalid Unicode scalar values.") from exc
    if patch_size > MAX_PATCH_BYTES:
        raise AgentError("Proposed patch exceeds 500 KiB.")
    if not patch.strip():
        raise AgentError("Model proposed no patch.")
    if "\x00" in patch or not patch.startswith("diff --git "):
        raise AgentError("Patch is not a standard git unified diff.")
    if re.search(r"(?im)^GIT binary patch$|^Binary files .* differ$", patch):
        raise AgentError("Binary patches are forbidden.")
    if re.search(r"(?im)^(?:new|old) file mode 120000$", patch):
        raise AgentError("Symbolic-link changes are forbidden.")
    paths: list[str] = []
    active_path: str | None = None
    old_header_seen = False
    new_header_seen = False
    old_header_path = ""
    new_header_path = ""
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
            old_header_path = ""
            new_header_path = ""
            continue
        if line.startswith("--- "):
            if active_path is None or old_header_seen:
                raise AgentError("Unexpected or duplicate old-file header.")
            header_path = line[4:].split("\t", 1)[0]
            if header_path not in {"/dev/null", f"a/{active_path}"}:
                raise AgentError("Old-file header does not match the validated diff path.")
            old_header_path = header_path
            old_header_seen = True
        elif line.startswith("+++ "):
            if active_path is None or not old_header_seen or new_header_seen:
                raise AgentError("Unexpected or duplicate new-file header.")
            header_path = line[4:].split("\t", 1)[0]
            if header_path not in {"/dev/null", f"b/{active_path}"}:
                raise AgentError("New-file header does not match the validated diff path.")
            new_header_path = header_path
            new_header_seen = True
            if old_header_path == "/dev/null" and new_header_path == "/dev/null":
                raise AgentError("A patch cannot add and delete /dev/null.")
            if new_header_path == "/dev/null" and active_path.startswith("tests/"):
                raise AgentError("Deleting tests is forbidden; preserve regression coverage.")
    if active_path is not None and not (old_header_seen and new_header_seen):
        raise AgentError(f"Incomplete file headers for: {active_path}")
    if not paths:
        raise AgentError("Patch contains no file changes.")
    # Windows and default macOS filesystems may treat case-only path variants as the same file.
    if len({path.casefold() for path in paths}) != len(paths):
        raise AgentError("Duplicate file paths or case-colliding paths are forbidden.")
    for relative in paths:
        path = Path(relative)
        windows_path = PureWindowsPath(relative)
        parts = path.parts
        windows_reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
        if (
            path.is_absolute()
            or windows_path.is_absolute()
            or windows_path.drive
            or "\\" in relative
            or ":" in relative
            or not parts
            or any(part in {"", ".", ".."} for part in parts)
            or any(part.rstrip(" .").split(".", 1)[0].upper() in windows_reserved for part in parts)
            or any(part.endswith((" ", ".")) for part in parts)
            or any(ord(char) < 32 for char in relative)
        ):
            raise AgentError(f"Unsafe path: {relative}")
        if any(
            part.lower() in FORBIDDEN_PATH_PARTS
            or part.lower().startswith((".env", "credential", "secret", "id_rsa", "id_ed25519"))
            for part in parts
        ):
            raise AgentError(f"Protected path: {relative}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise AgentError(f"Binary/model/credential artifact path forbidden: {relative}")
        if path.suffix.lower() not in ALLOWED_TEXT_SUFFIXES:
            raise AgentError(f"File type is outside the agent allowlist: {relative}")
        allowed_roots = {"src", "tests", "docs", "tools"}
        if len(parts) > 1 and parts[0].lower() not in allowed_roots:
            raise AgentError(f"Path is outside source, tests, docs, and tools: {relative}")
        if len(parts) == 1 and path.suffix.lower() not in {".md", ".rst", ".txt"}:
            raise AgentError(f"Only root-level documentation may be edited: {relative}")
        normalized = relative.casefold()
        if normalized.startswith(".github/") or normalized in {".gitignore", "pyproject.toml", "cargo.lock", "package-lock.json"}:
            raise AgentError(f"Protected configuration path: {relative}")
        candidate = root / path
        current = root.resolve()
        for part in path.parts:
            current = current / part
            if current.is_symlink():
                raise AgentError(f"Symlink path components are forbidden: {relative}")
        resolved = candidate.resolve()
        if root.resolve() not in resolved.parents:
            raise AgentError(f"Path escapes repository: {relative}")
def run_validation_checks(root: Path) -> list[dict[str, Any]]:
    """Run fixed repository checks; never execute commands returned by the model."""
    checks = [
        ("python-source-syntax", [
            sys.executable, "-c",
            "from pathlib import Path; import sys; excluded={'.git','.venv','venv','node_modules','__pycache__'}; files=[p for p in Path('.').rglob('*.py') if not any(part in excluded for part in p.parts)]; errors=[]; "
            "exec('for p in files:\\n try: compile(p.read_text(encoding=\\'utf-8\\'), str(p), \\'exec\\')\\n except Exception as e: errors.append(f\\'{p}: {e}\\')'); "
            "print('checked',len(files),'Python files'); [print(e) for e in errors]; sys.exit(bool(errors))"
        ]),
        ("json-manifests", [
            sys.executable, "-c",
            "from pathlib import Path; import json,sys; excluded={'.git','.venv','venv','node_modules'}; files=[p for p in Path('.').rglob('*.json') if not any(part in excluded for part in p.parts)]; errors=[]; "
            "exec('for p in files:\\n try: json.loads(p.read_text(encoding=\\'utf-8\\'))\\n except Exception as e: errors.append(f\\'{p}: {e}\\')'); "
            "print('checked',len(files),'JSON files'); [print(e) for e in errors]; sys.exit(bool(errors))"
        ]),
        ("pytest", [sys.executable, "-m", "pytest", "-q", "tests"]),
    ]
    results: list[dict[str, Any]] = []
    for name, command in checks:
        try:
            proc = subprocess.run(
                command, cwd=root, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, timeout=900, check=False,
            )
            results.append({"check": name, "command": command, "exit_code": proc.returncode, "output": proc.stdout[-12000:]})
            if proc.returncode:
                break
        except (OSError, subprocess.TimeoutExpired) as exc:
            results.append({"check": name, "command": command, "exit_code": 124, "output": str(exc)})
            break
    return results

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
    parser.add_argument("--verify", action="store_true", help="run fixed syntax, JSON, and pytest checks after --apply; revert patch if checks fail")
    parser.add_argument("--report-file", type=Path, default=Path.home() / ".ia-agent" / "last-run.json", help="write a redacted run-evidence JSON outside the repository")
    args = parser.parse_args(argv)
    if args.verify and not args.apply:
        parser.error("--verify requires --apply")
    root = args.repo.resolve()
    task_path = args.task_file.resolve()
    report: dict[str, Any] = {
        "schema_version": 1,
        "run_id": str(uuid.uuid4()),
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        # Do not persist a local absolute path: it can expose usernames and directory layout.
        "repository_name": root.name,
        "model": args.model,
        "mode": "verify" if args.verify else ("apply" if args.apply else "dry-run"),
        "status": "RUNNING",
        "changed_files": [],
        "checks": [],
    }

    def save_report(status: str, error: str | None = None) -> None:
        report["status"] = status
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        if error:
            report["error"] = error
        try:
            destination = args.report_file.expanduser().resolve()
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=destination.parent,
                    prefix=f".{destination.name}.", suffix=".tmp", delete=False,
                ) as stream:
                    temporary = Path(stream.name)
                    stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, destination)
                temporary = None
            finally:
                if temporary is not None:
                    try:
                        temporary.unlink()
                    except FileNotFoundError:
                        pass
            print(f"REPORT_FILE: {destination}")
        except OSError as report_error:
            print(f"REPORT_NOT_SAVED: {report_error}", file=sys.stderr)

    try:
        if not task_path.is_file():
            raise AgentError(f"Task file not found: {task_path}")
        task = task_path.read_text(encoding="utf-8")
        report["task_sha256"] = hashlib.sha256(task.encode("utf-8")).hexdigest()
        if not task.strip() or len(task) > MAX_TASK_CHARS:
            raise AgentError(f"Task must contain 1..{MAX_TASK_CHARS} characters.")
        clean_worktree(root)
        result = call_ollama(args.url, args.model, task, args.timeout)
        # Model summaries may echo private task content; persist only non-reversible metadata.
        summary_bytes = result["summary"].encode("utf-8", errors="strict")
        report["summary_sha256"] = hashlib.sha256(summary_bytes).hexdigest()
        report["summary_chars"] = len(result["summary"])
        print("RUN_ID:", report["run_id"])
        print("TASK_SHA256:", report.get("task_sha256", "NOT_AVAILABLE"))
        print("SUMMARY:", result["summary"])
        if not result["patch"].strip():
            print("STATUS: BLOCKED — model returned no patch")
            save_report("BLOCKED", "Model returned no patch.")
            return 2
        report["patch_sha256"] = hashlib.sha256(result["patch"].encode("utf-8")).hexdigest()
        report["changed_files"] = re.findall(r"(?m)^diff --git a/(.+) b/", result["patch"])
        validate_patch(result["patch"], root)
        print("STATUS: PATCH_VALIDATED")
        print("PATCH_BEGIN")
        print(result["patch"], end="" if result["patch"].endswith("\n") else "\n")
        print("PATCH_END")
        if not args.apply:
            print("MODE: DRY_RUN — no repository files changed")
            save_report("PATCH_VALIDATED")
            return 0
        apply_patch(root, result["patch"])
        if args.verify:
            checks = run_validation_checks(root)
            report["checks"] = checks
            for check in checks:
                print(f"CHECK {check['check']}: {'PASS' if check['exit_code'] == 0 else 'FAIL'} (exit {check['exit_code']})")
                if check["output"]:
                    print(check["output"])
            if any(check["exit_code"] != 0 for check in checks):
                rollback = subprocess.run(
                    ["git", "-C", str(root), "apply", "-R", "--"],
                    input=result["patch"], text=True, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, timeout=30, check=False,
                )
                if rollback.returncode:
                    raise AgentError("Validation failed and automatic patch rollback failed: " + rollback.stderr.strip())
                print("STATUS: FAIL — patch reverted after failed validation")
                save_report("FAIL", "Validation failed; patch was reverted.")
                return 1
            print("STATUS: PASS — patch applied and fixed validation checks passed; no commit/push/merge performed")
            save_report("PASS")
            return 0
        print("STATUS: PATCH_APPLIED — no commit, push, merge, or model-supplied commands executed")
        print("NEXT: run the project's documented test suite and review git diff before committing")
        save_report("PATCH_APPLIED_NOT_VERIFIED")
        return 0
    except (AgentError, OSError, UnicodeError, subprocess.TimeoutExpired) as exc:
        print(f"STATUS: BLOCKED — {exc}", file=sys.stderr)
        save_report("BLOCKED", str(exc))
        return 2
if __name__ == "__main__":
    raise SystemExit(main())