import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.validate_benchmark_truth import ORACLES, load_suite, main


class BenchmarkOracleValidationTests(unittest.TestCase):
    def test_repository_suite_matches_every_independent_oracle(self):
        suite = load_suite(Path("benchmarks/complex_tasks.json"))
        by_id = {task["id"]: task for task in suite["tasks"]}
        self.assertEqual(set(by_id), set(ORACLES))
        for task_id, oracle in ORACLES.items():
            with self.subTest(task_id=task_id):
                self.assertEqual(oracle(), by_id[task_id]["expected_output"])

    def test_rejects_duplicate_ids_and_non_object_tasks(self):
        base = {
            "schema_version": 1,
            "tasks": [
                {"id": "a", "category": "reasoning", "prompt": "task a", "expected_output": {}},
                {"id": "a", "category": "reasoning", "prompt": "task a again", "expected_output": {}},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suite.json"
            path.write_text(json.dumps(base), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unique"):
                load_suite(path)
            path.write_text(json.dumps({"schema_version": 1, "tasks": [None]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must be an object"):
                load_suite(path)

    def test_rejects_duplicate_json_keys_and_excessive_nesting(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suite.json"
            path.write_text('{"schema_version":1,"schema_version":1,"tasks":[]}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                load_suite(path)
            path.write_text("[" * 100 + "0" + "]" * 100, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nesting"):
                load_suite(path)

    def test_rejects_oversized_suite(self):
        from tools.validate_benchmark_truth import MAX_BENCHMARK_BYTES
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suite.json"
            path.write_text(" " * (MAX_BENCHMARK_BYTES + 1), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "byte limit"):
                load_suite(path)

    def test_cli_propagates_oracle_failure_as_nonzero_exit_code(self):
        suite = json.loads(Path("benchmarks/complex_tasks.json").read_text(encoding="utf-8"))
        suite["tasks"].append({
            "id": "unverified_cli_task",
            "category": "reasoning",
            "prompt": "A task without an independent oracle.",
            "expected_output": {},
        })
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suite.json"
            path.write_text(json.dumps(suite), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "tools/validate_benchmark_truth.py", str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("missing independent oracles", result.stdout)

    def test_main_fails_when_task_has_no_independent_oracle(self):
        suite = json.loads(Path("benchmarks/complex_tasks.json").read_text(encoding="utf-8"))
        suite["tasks"].append({
            "id": "unverified_extra_task",
            "category": "reasoning",
            "prompt": "An extra task without a registered oracle.",
            "expected_output": {},
        })
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suite.json"
            path.write_text(json.dumps(suite), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main([str(path)])
            self.assertEqual(status, 1)
            self.assertIn("missing independent oracles", output.getvalue())


if __name__ == "__main__":
    unittest.main()
