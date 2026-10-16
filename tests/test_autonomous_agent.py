import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import autonomous_agent


class AutonomousAgentTests(unittest.TestCase):
    def test_cycle_has_explicit_generative_blocker_and_no_cloud_fallback(self):
        with patch.object(autonomous_agent, "_run", return_value={
            "status": "PASS", "returncode": 0, "output_tail": ""
        }):
            report = autonomous_agent.run_cycle()
        self.assertEqual(report["overall_status"], "BLOCKED", "a blocked generative task must prevent an overall PASS")
        self.assertFalse(report["safety"]["network_access"])
        self.assertFalse(report["safety"]["cloud_fallback"])
        self.assertFalse(report["safety"]["source_mutation"])
        generative = next(t for t in report["tasks"] if t["id"] == "generative-coding")
        self.assertEqual(generative["status"], "BLOCKED")
        self.assertFalse(generative["cloud_fallback"])

    def test_cycle_includes_independent_benchmark_oracle(self):
        with patch.object(autonomous_agent, "_run", return_value={
            "status": "PASS", "returncode": 0, "output_tail": ""
        }) as run:
            report = autonomous_agent.run_cycle()
        oracle = next(t for t in report["tasks"] if t["id"] == "independent-benchmark-oracle")
        self.assertIn(oracle["status"], {"PASS", "FAIL", "BLOCKED"})
        self.assertGreaterEqual(run.call_count, 2)

    def test_cycle_reports_json_syntax_status(self):
        with patch.object(autonomous_agent, "_run", return_value={
            "status": "PASS", "returncode": 0, "output_tail": ""
        }):
            report = autonomous_agent.run_cycle()
        task = next(t for t in report["tasks"] if t["id"] == "json-syntax")
        self.assertIn(task["status"], {"PASS", "FAIL"})
        self.assertGreaterEqual(task["files_checked"], 0)

    def test_cycle_reports_deeply_nested_python_and_json_without_crashing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "deep.py").write_text(
                "value = " + "[" * 2000 + "0" + "]" * 2000, encoding="utf-8"
            )
            (root / "deep.json").write_text(
                "[" * 10000 + "0" + "]" * 10000, encoding="utf-8"
            )
            with patch.object(autonomous_agent, "ROOT", root), patch.object(
                autonomous_agent, "_run",
                return_value={"status": "PASS", "returncode": 0, "output_tail": ""},
            ):
                report = autonomous_agent.run_cycle()
        syntax = next(t for t in report["tasks"] if t["id"] == "python-syntax")
        json_syntax = next(t for t in report["tasks"] if t["id"] == "json-syntax")
        self.assertEqual(syntax["status"], "FAIL")
        self.assertEqual(json_syntax["status"], "FAIL")
        self.assertEqual(syntax["files_checked"], 1)
        self.assertEqual(json_syntax["files_checked"], 1)

    def test_cycle_skips_virtualenv_and_dependency_cache_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "project.py").write_text("value = 1\n", encoding="utf-8")
            for excluded in ("venv", "node_modules", ".tox", ".pytest_cache"):
                nested = root / excluded
                nested.mkdir()
                (nested / "ignored.py").write_text("this is not valid python =\n", encoding="utf-8")
                (nested / "ignored.json").write_text("{invalid", encoding="utf-8")
            with patch.object(autonomous_agent, "ROOT", root), patch.object(
                autonomous_agent, "_run",
                return_value={"status": "PASS", "returncode": 0, "output_tail": ""},
            ):
                report = autonomous_agent.run_cycle()
        syntax = next(t for t in report["tasks"] if t["id"] == "python-syntax")
        json_syntax = next(t for t in report["tasks"] if t["id"] == "json-syntax")
        self.assertEqual(syntax["status"], "PASS")
        self.assertEqual(json_syntax["status"], "PASS")
        self.assertEqual(syntax["files_checked"], 1)
        self.assertEqual(json_syntax["files_checked"], 0)

    def test_cycle_report_does_not_expose_absolute_repository_path(self):
        with patch.object(autonomous_agent, "_run", return_value={
            "status": "PASS", "returncode": 0, "output_tail": ""
        }):
            report = autonomous_agent.run_cycle()
        self.assertEqual(report["repository_name"], autonomous_agent.ROOT.name)
        self.assertNotIn(str(autonomous_agent.ROOT), json.dumps(report))

    def test_report_write_is_atomic_and_leaves_no_temporary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "evidence.json"
            report = {
                "schema_version": 1,
                "overall_status": "PASS",
                "generated_at_utc": "2026-01-01T00:00:00+00:00",
                "tasks": [],
            }
            with patch("sys.argv", [
                "autonomous_agent.py", "--cycles", "1", "--report", str(report_path)
            ]), patch.object(autonomous_agent, "run_cycle", return_value=report):
                self.assertEqual(autonomous_agent.main(), 0)
            saved = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["runs"], [report])
            self.assertEqual(list(Path(directory).glob(".evidence.json.*.tmp")), [])

    def test_invalid_cycle_count_is_rejected_by_cli(self):
        with patch("sys.argv", ["autonomous_agent.py", "--cycles", "0"]):
            with self.assertRaises(SystemExit) as exc:
                autonomous_agent.main()
        self.assertEqual(exc.exception.code, 2)


if __name__ == "__main__":
    unittest.main()