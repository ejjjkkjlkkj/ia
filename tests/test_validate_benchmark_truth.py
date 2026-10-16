import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate_benchmark_truth.py"
SUITE = ROOT / "benchmarks" / "complex_tasks.json"


class BenchmarkTruthValidatorTests(unittest.TestCase):
    def test_current_complex_suite_has_independent_oracles(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(SUITE)],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS: 10 independent oracle checks", result.stdout)

    def test_new_task_without_oracle_fails_closed(self):
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        suite["tasks"].append({
            "id": "unregistered_future_task",
            "category": "regression",
            "prompt": "Return JSON.",
            "expected_output": {"ok": True},
        })
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suite.json"
            path.write_text(json.dumps(suite), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), str(path)],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unregistered_future_task", result.stdout)
        self.assertIn("FAIL", result.stdout)


if __name__ == "__main__":
    unittest.main()
