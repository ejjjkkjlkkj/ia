import json
import unittest
from unittest.mock import patch, Mock

from tools import ci_triage


class CITriageTests(unittest.TestCase):
    def test_summarize_all_success(self):
        overall, counts = ci_triage.summarize([
            {"status": "completed", "conclusion": "success"},
            {"status": "completed", "conclusion": "success"},
        ])
        self.assertEqual(overall, "PASS")
        self.assertEqual(counts["success"], 2)

    def test_summarize_pending_and_empty_are_not_pass(self):
        self.assertEqual(ci_triage.summarize([{"status": "queued"}])[0], "PENDING")
        self.assertEqual(ci_triage.summarize([])[0], "PENDING")

    def test_failure_takes_precedence_over_pending(self):
        overall, counts = ci_triage.summarize([
            {"status": "completed", "conclusion": "failure"},
            {"status": "in_progress"},
        ])
        self.assertEqual(overall, "FAIL")
        self.assertEqual(counts["failure"], 1)
        self.assertEqual(counts["pending"], 1)

    @patch("tools.ci_triage.shutil.which", return_value="gh.exe")
    @patch("tools.ci_triage.subprocess.run")
    def test_fetch_runs_filters_exact_commit_sha(self, run_mock, _which):
        run_mock.return_value = Mock(
            returncode=0,
            stdout=json.dumps([
                {"headSha": "target", "name": "same commit"},
                {"headSha": "other", "name": "different commit"},
            ]),
            stderr="",
        )
        runs = ci_triage.fetch_runs("owner/repo", "branch", "target")
        self.assertEqual([run["name"] for run in runs], ["same commit"])
        args, kwargs = run_mock.call_args
        self.assertEqual(args[0][0:3], ["gh", "run", "list"])
        self.assertFalse(kwargs["shell"])
        self.assertEqual(kwargs["timeout"], 30)

    @patch("tools.ci_triage.shutil.which", return_value=None)
    def test_missing_cli_is_blocked(self, _which):
        with self.assertRaisesRegex(RuntimeError, "not installed"):
            ci_triage.fetch_runs("owner/repo", "branch", "target")

    @patch("tools.ci_triage.shutil.which", return_value="gh")
    @patch("tools.ci_triage.subprocess.run")
    def test_invalid_json_is_blocked(self, run_mock, _which):
        run_mock.return_value = Mock(returncode=0, stdout="not-json", stderr="")
        with self.assertRaisesRegex(RuntimeError, "invalid JSON"):
            ci_triage.fetch_runs("owner/repo", "branch", "target")

    def test_invalid_repo_and_limit_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "owner/name"):
            ci_triage.fetch_runs("badrepo", "branch", "sha")
        with self.assertRaisesRegex(ValueError, "limit"):
            ci_triage.fetch_runs("owner/repo", "branch", "sha", limit=101)


if __name__ == "__main__":
    unittest.main()
