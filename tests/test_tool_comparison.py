import json
import sys
import tempfile
import unittest
from pathlib import Path

from tools.run_tool_comparison import load_suite, parse_output, percentile, run_one, summarize


class ToolComparisonTests(unittest.TestCase):
    def test_suite_hashable_and_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suite.json"
            path.write_text(json.dumps({
                "schema_version": 1,
                "benchmark_id": "project-test",
                "tasks": [{"id": "one", "category": "logic", "prompt": "Return 2", "expected_output": 2}],
            }), encoding="utf-8")
            suite, raw = load_suite(path)
            self.assertEqual(suite["tasks"][0]["id"], "one")
            self.assertTrue(raw)

    def test_duplicate_task_ids_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suite.json"
            path.write_text(json.dumps({
                "schema_version": 1,
                "tasks": [
                    {"id": "dup", "prompt": "a", "expected_output": 1},
                    {"id": "dup", "prompt": "b", "expected_output": 2},
                ],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unique"):
                load_suite(path)

    def test_adapter_output_must_have_output_field(self):
        self.assertEqual(parse_output('{"output": {"answer": 42}}'), {"answer": 42})
        with self.assertRaisesRegex(ValueError, "output"):
            parse_output('{"answer": 42}')

    def test_summary_and_percentile(self):
        results = [
            {"status": "PASS", "latency_seconds": 1.0},
            {"status": "FAIL", "latency_seconds": 2.0},
            {"status": "BLOCKED", "latency_seconds": None},
        ]
        summary = summarize(results)
        self.assertEqual(summary["passed"], 1)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["blocked"], 1)
        self.assertEqual(summary["latency_seconds"]["median"], 1.5)
        self.assertEqual(percentile([1, 2, 3, 4], 0.95), 4.0)

    def test_run_one_executes_adapter_and_hashes_output(self):
        command = [
            sys.executable, "-c",
            "import json,sys; json.load(sys.stdin); print(json.dumps({'output': 42}))",
        ]
        result = run_one(command, {"id": "integration", "category": "logic",
                                   "prompt": "Return 42", "expected_output": 42}, 5)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["reason"], "exact_match")
        self.assertEqual(len(result["output_sha256"]), 64)
        self.assertNotIn("output", result)

    def test_run_one_reports_nonzero_exit_without_leaking_stderr(self):
        command = [sys.executable, "-c", "import sys; print('secret diagnostic', file=sys.stderr); sys.exit(7)"]
        result = run_one(command, {"id": "exit", "prompt": "x", "expected_output": "x"}, 5)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["reason"], "nonzero_exit")
        self.assertNotIn("secret diagnostic", json.dumps(result))

    def test_run_one_reports_invalid_json(self):
        command = [sys.executable, "-c", "print('not json')"]
        result = run_one(command, {"id": "invalid", "prompt": "x", "expected_output": "x"}, 5)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["reason"], "invalid_json_output")

    def test_run_one_classifies_timeout_as_blocked(self):
        command = [sys.executable, "-c", "import time; time.sleep(2)"]
        result = run_one(command, {"id": "timeout", "prompt": "x", "expected_output": "x"}, 0.05)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["reason"], "timeout")
        self.assertIsNone(result["latency_seconds"])


if __name__ == "__main__":
    unittest.main()
