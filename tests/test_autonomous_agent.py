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
        self.assertIn(report["overall_status"], {"PASS", "BLOCKED"})
        self.assertFalse(report["safety"]["network_access"])
        self.assertFalse(report["safety"]["cloud_fallback"])
        self.assertFalse(report["safety"]["source_mutation"])
        generative = next(t for t in report["tasks"] if t["id"] == "generative-coding")
        self.assertEqual(generative["status"], "BLOCKED")
        self.assertFalse(generative["cloud_fallback"])

    def test_cycle_reports_json_syntax_status(self):
        with patch.object(autonomous_agent, "_run", return_value={
            "status": "PASS", "returncode": 0, "output_tail": ""
        }):
            report = autonomous_agent.run_cycle()
        task = next(t for t in report["tasks"] if t["id"] == "json-syntax")
        self.assertIn(task["status"], {"PASS", "FAIL"})
        self.assertGreaterEqual(task["files_checked"], 0)

    def test_invalid_cycle_count_is_rejected_by_cli(self):
        with patch("sys.argv", ["autonomous_agent.py", "--cycles", "0"]):
            with self.assertRaises(SystemExit) as exc:
                autonomous_agent.main()
        self.assertEqual(exc.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
