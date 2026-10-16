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
        self.assertEqual(parse_adapter_output('{"output":"{\"answer\":42}"}'), {"answer": 42})

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


if __name__ == "__main__":
    unittest.main()
