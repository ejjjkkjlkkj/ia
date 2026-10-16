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

    def test_suite_rejects_oversized_file(self):
        from tools.run_tool_comparison import MAX_SUITE_BYTES
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suite.json"
            path.write_bytes(b" " * (MAX_SUITE_BYTES + 1))
            with self.assertRaisesRegex(ValueError, "exceeds"):
                load_suite(path)

    def test_suite_rejects_too_many_tasks(self):
        from tools.run_tool_comparison import MAX_TASKS
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suite.json"
            path.write_text(json.dumps({
                "schema_version": 1,
                "tasks": [
                    {"id": str(i), "prompt": "x", "expected_output": i}
                    for i in range(MAX_TASKS + 1)
                ],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "tasks"):
                load_suite(path)

    def test_suite_rejects_oversized_prompt(self):
        from tools.run_tool_comparison import MAX_PROMPT_CHARS
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suite.json"
            path.write_text(json.dumps({
                "schema_version": 1,
                "tasks": [{
                    "id": "large", "prompt": "x" * (MAX_PROMPT_CHARS + 1),
                    "expected_output": "x",
                }],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "prompt exceeds"):
                load_suite(path)

    def test_suite_root_must_be_object(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suite.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "root must be a JSON object"):
                load_suite(path)

    def test_suite_rejects_duplicate_json_keys_and_nonstandard_numbers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suite.json"
            path.write_text('{"schema_version":1,"schema_version":1,"tasks":[]}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                load_suite(path)
            path.write_text('{"schema_version":NaN,"tasks":[]}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-standard JSON"):
                load_suite(path)

    def test_suite_rejects_invalid_unicode_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suite.json"
            path.write_text(
                '{"schema_version":1,"tasks":[{"id":"x","prompt":"\\ud800","expected_output":1}]}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "invalid Unicode"):
                load_suite(path)

    def test_json_scoring_does_not_treat_boolean_as_number(self):
        command = [
            sys.executable, "-c",
            "import json; print(json.dumps({'output': True}))",
        ]
        result = run_one(
            command, {"id": "strict-json", "prompt": "Return number 1", "expected_output": 1}, 5
        )
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["reason"], "exact_mismatch")

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
