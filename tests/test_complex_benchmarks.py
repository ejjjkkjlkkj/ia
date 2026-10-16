import json
import tempfile
import unittest
from pathlib import Path

from tools.run_complex_benchmarks import load_suite, parse_adapter_output


class ComplexBenchmarkHarnessTests(unittest.TestCase):
    def test_suite_has_unique_complex_tasks(self):
        suite = load_suite(Path("benchmarks/complex_tasks.json"))
        self.assertGreaterEqual(len(suite["tasks"]), 10)
        self.assertEqual(len({task["id"] for task in suite["tasks"]}), len(suite["tasks"]))
        self.assertTrue(all(task["category"] and len(task["prompt"]) > 80 for task in suite["tasks"]))

    def test_adapter_accepts_json_value_and_json_encoded_string(self):
        self.assertEqual(parse_adapter_output('{"output":{"answer":42}}'), {"answer": 42})
        self.assertEqual(
            parse_adapter_output(json.dumps({"output": json.dumps({"answer": 42})})),
            {"answer": 42},
        )

    def test_adapter_rejects_non_object_and_missing_output(self):
        for payload in ('[]', '{"answer":42}', 'not-json'):
            with self.subTest(payload=payload), self.assertRaises((ValueError, json.JSONDecodeError)):
                parse_adapter_output(payload)

    def test_duplicate_task_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "suite.json"
            path.write_text(json.dumps({
                "schema_version": 1,
                "tasks": [
                    {"id": "same", "prompt": "first", "expected_output": {}},
                    {"id": "same", "prompt": "second", "expected_output": {}},
                ],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unique"):
                load_suite(path)

    def test_coding_suite_covers_every_catalogue_language_and_complex_tasks(self):
        suite = json.loads(Path("benchmarks/coding_challenges.json").read_text(encoding="utf-8"))
        self.assertEqual(suite["schema_version"], 1)
        self.assertGreaterEqual(len(suite["language_catalogue"]), 35)
        self.assertGreaterEqual(len(suite["tasks"]), 20)
        self.assertEqual(len({row["id"] for row in suite["language_catalogue"]}), len(suite["language_catalogue"]))
        self.assertEqual(len({row["id"] for row in suite["tasks"]}), len(suite["tasks"]))
        self.assertIn("nexora", {row["id"] for row in suite["language_catalogue"]})
        self.assertTrue(all(task.get("cases") and task.get("difficulty") in {"hard", "very_hard"} for task in suite["tasks"]))
        self.assertTrue(all(case.get("input") is not None and case.get("output") is not None for task in suite["tasks"] for case in task["cases"]))


if __name__ == "__main__":
    unittest.main()
