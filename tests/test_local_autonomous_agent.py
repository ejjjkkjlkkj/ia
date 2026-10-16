import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "local_autonomous_agent.py"
SPEC = importlib.util.spec_from_file_location("local_autonomous_agent", MODULE_PATH)
agent = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(agent)


def diff_for(path, old="old", new="new"):
    return (
        f"diff --git a/{path} b/{path}\n"
        f"--- a/{path}\n+++ b/{path}\n"
        "@@ -1 +1 @@\n"
        f"-{old}\n+{new}\n"
    )


class PatchValidationTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def test_dry_run_writes_redacted_reproducible_report(self):
        task_file = self.root / "task.txt"
        report_file = self.root / "evidence.json"
        task_file.write_text("private task text", encoding="utf-8")
        model_result = {"summary": "proposal", "patch": diff_for("src/a.py")}
        with patch.object(agent, "clean_worktree"), patch.object(agent, "call_ollama", return_value=model_result):
            code = agent.main([
                "--repo", str(self.root), "--task-file", str(task_file),
                "--report-file", str(report_file),
            ])
        self.assertEqual(code, 0)
        report = json.loads(report_file.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "PATCH_VALIDATED")
        self.assertEqual(report["changed_files"], ["src/a.py"])
        self.assertEqual(len(report["task_sha256"]), 64)
        self.assertEqual(len(report["patch_sha256"]), 64)
        self.assertNotIn("private task text", report_file.read_text(encoding="utf-8"))

    def test_verify_requires_apply(self):
        with self.assertRaises(SystemExit) as ctx:
            agent.main(["--task-file", "missing.txt", "--verify"])
        self.assertEqual(ctx.exception.code, 2)

    def test_validation_stops_after_first_failed_check(self):
        class Result:
            returncode = 1
            stdout = "synthetic failure"
        with patch.object(agent.subprocess, "run", return_value=Result()) as run:
            results = agent.run_validation_checks(self.root)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["exit_code"], 1)
        self.assertEqual(run.call_count, 1)
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_accepts_local_ollama_urls(self):
        for url in (
            "http://127.0.0.1:11434/api/chat",
            "http://localhost:11434/api/chat",
            "http://[::1]:11434/api/chat",
        ):
            agent.validate_local_url(url)

    def test_rejects_remote_ollama_urls(self):
        for url in (
            "https://example.com/api/chat",
            "http://192.0.2.10:11434/api/chat",
            "http://127.0.0.1:11434/api/chat?forward=1",
            "http://user:pass@127.0.0.1:11434/api/chat",
            "http://127.0.0.1:11434/api/chat#fragment",
        ):
            with self.subTest(url=url), self.assertRaises(agent.AgentError):
                agent.validate_local_url(url)

    def test_rejects_malformed_ollama_response(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit): return b"{not-json"
        class Opener:
            def open(self, request, timeout): return Response()
        with patch.object(agent.urllib.request, "build_opener", return_value=Opener()):
            with self.assertRaises(agent.AgentError):
                agent.call_ollama("http://127.0.0.1:11434/api/chat", "local", "task", 5)

    def test_rejects_oversized_ollama_response(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit): return b"x" * limit
        class Opener:
            def open(self, request, timeout): return Response()
        with patch.object(agent.urllib.request, "build_opener", return_value=Opener()):
            with self.assertRaises(agent.AgentError):
                agent.call_ollama("http://127.0.0.1:11434/api/chat", "local", "task", 5)

    def test_rejects_invalid_timeouts(self):
        for timeout in (0, -1, 901, True, 1.5):
            with self.subTest(timeout=timeout), self.assertRaises(agent.AgentError):
                agent.call_ollama("http://127.0.0.1:11434/api/chat", "test", "task", timeout)

    def test_accepts_normal_source_patch(self):
        (self.root / "src").mkdir()
        (self.root / "src" / "example.py").write_text("old\n", encoding="utf-8")
        agent.validate_patch(diff_for("src/example.py"), self.root)

    def test_rejects_empty_patch(self):
        with self.assertRaises(agent.AgentError):
            agent.validate_patch("", self.root)

    def test_rejects_path_traversal(self):
        for path in ("../outside.py", r"..\\outside.py", r"C:\\outside.py", "/outside.py"):
            with self.subTest(path=path), self.assertRaises(agent.AgentError):
                agent.validate_patch(diff_for(path), self.root)

    def test_rejects_internal_symlink_redirection(self):
        protected = self.root / "protected"
        protected.mkdir()
        link = self.root / "src"
        try:
            link.symlink_to(protected, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("directory symlink unavailable on this platform")
        with self.assertRaises(agent.AgentError):
            agent.validate_patch(diff_for("src/hidden.py"), self.root)

    def test_rejects_symlink_escape(self):
        outside = Path(tempfile.mkdtemp())
        link = self.root / "escape"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("directory symlink unavailable on this platform")
        with self.assertRaises(agent.AgentError):
            agent.validate_patch(diff_for("escape/payload.py"), self.root)

    def test_rejects_workflow_changes(self):
        for path in (".github/workflows/ci.py", ".GITHUB/workflows/ci.py"):
            with self.subTest(path=path), self.assertRaises(agent.AgentError):
                agent.validate_patch(diff_for(path), self.root)

    def test_rejects_paths_outside_source_test_docs_tools(self):
        for path in ("scripts/deploy.py", "models/model.py", "build/generated.py"):
            with self.subTest(path=path), self.assertRaises(agent.AgentError):
                agent.validate_patch(diff_for(path), self.root)

    def test_rejects_env_variants_and_configuration_files(self):
        for path in (".env.local", "config.yaml", "settings.json", "keys/private.pem"):
            with self.subTest(path=path), self.assertRaises(agent.AgentError):
                agent.validate_patch(diff_for(path), self.root)

    def test_rejects_secret_like_filenames(self):
        for path in (".env.production", "credentials.txt", "secret-notes.md", "id_rsa.txt"):
            with self.subTest(path=path), self.assertRaises(agent.AgentError):
                agent.validate_patch(diff_for(path), self.root)

    def test_rejects_windows_ads_and_reserved_names(self):
        for path in ("src/file.py:payload", "src/CON.txt", "src/trailing. "):
            with self.subTest(path=path), self.assertRaises(agent.AgentError):
                agent.validate_patch(diff_for(path), self.root)

    def test_rejects_symbolic_link_patch(self):
        patch = diff_for("src/link.py").replace(
            "diff --git a/src/link.py b/src/link.py\n",
            "diff --git a/src/link.py b/src/link.py\nnew file mode 120000\n",
        )
        with self.assertRaises(agent.AgentError):
            agent.validate_patch(patch, self.root)
    def test_rejects_binary_artifact(self):
        with self.assertRaises(agent.AgentError):
            agent.validate_patch(diff_for("models/weights.safetensors"), self.root)

    def test_rejects_mismatched_diff_paths(self):
        patch = diff_for("src/a.py").replace("b/src/a.py", "b/src/b.py")
        with self.assertRaises(agent.AgentError):
            agent.validate_patch(patch, self.root)

    def test_rejects_mismatched_old_file_header(self):
        patch = diff_for("src/a.py").replace("--- a/src/a.py", "--- a/src/other.py")
        with self.assertRaises(agent.AgentError):
            agent.validate_patch(patch, self.root)

    def test_rejects_mismatched_new_file_header(self):
        patch = diff_for("src/a.py").replace("+++ b/src/a.py", "+++ b/src/other.py")
        with self.assertRaises(agent.AgentError):
            agent.validate_patch(patch, self.root)

    def test_accepts_addition_and_deletion_headers(self):
        addition = diff_for("src/new.py").replace("--- a/src/new.py", "--- /dev/null")
        deletion = diff_for("src/old.py").replace("+++ b/src/old.py", "+++ /dev/null")
        agent.validate_patch(addition, self.root)
        agent.validate_patch(deletion, self.root)

    def test_rejects_both_null_device_headers(self):
        patch = diff_for("src/a.py").replace("--- a/src/a.py", "--- /dev/null").replace("+++ b/src/a.py", "+++ /dev/null")
        with self.assertRaises(agent.AgentError):
            agent.validate_patch(patch, self.root)

    def test_rejects_missing_file_headers(self):
        patch = "diff --git a/src/a.py b/src/a.py\n@@ -1 +1 @@\n-old\n+new\n"
        with self.assertRaises(agent.AgentError):
            agent.validate_patch(patch, self.root)

    def test_rejects_non_standard_patch(self):
        with self.assertRaises(agent.AgentError):
            agent.validate_patch("Here is your patch:\n" + diff_for("src/a.py"), self.root)


if __name__ == "__main__":
    unittest.main()
