import json
import subprocess
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

    def test_cancelled_or_skipped_runs_are_unvalidated_not_test_failures(self):
        for conclusion in ("cancelled", "skipped", "neutral", "stale"):
            with self.subTest(conclusion=conclusion):
                overall, counts = ci_triage.summarize([
                    {"status": "completed", "conclusion": conclusion}
                ])
                self.assertEqual(overall, "PENDING")
                self.assertEqual(counts["failure"], 0)
                self.assertEqual(counts["pending"], 1)

    def test_known_execution_failures_are_fail(self):
        for conclusion in ("failure", "timed_out", "action_required", "startup_failure"):
            with self.subTest(conclusion=conclusion):
                self.assertEqual(
                    ci_triage.summarize([{"status": "completed", "conclusion": conclusion}])[0],
                    "FAIL",
                )

    @patch("tools.ci_triage.shutil.which", return_value="gh.exe")
    @patch("tools.ci_triage.subprocess.run")
    def test_fetch_runs_filters_exact_commit_sha(self, run_mock, _which):
        sha = "a" * 40
        run_mock.return_value = Mock(
            returncode=0,
            stdout=json.dumps([
                {"headSha": sha, "name": "same commit"},
                {"headSha": "b" * 40, "name": "different commit"},
            ]),
            stderr="",
        )
        runs = ci_triage.fetch_runs("owner/repo", sha)
        self.assertEqual([run["name"] for run in runs], ["same commit"])
        args, kwargs = run_mock.call_args
        self.assertEqual(args[0][0:3], ["gh", "run", "list"])
        self.assertIn("--commit", args[0])
        self.assertFalse(kwargs["shell"])
        self.assertEqual(kwargs["timeout"], 30)
        self.assertIs(kwargs["stdin"], subprocess.DEVNULL)

    @patch("tools.ci_triage.shutil.which", return_value="gh")
    @patch("tools.ci_triage.subprocess.run")
    def test_limit_saturated_response_is_blocked_as_potentially_truncated(self, run_mock, _which):
        run_mock.return_value = Mock(
            returncode=0,
            stdout=json.dumps([{"headSha": "a" * 40}]),
            stderr="",
        )
        with self.assertRaisesRegex(RuntimeError, "may be truncated"):
            ci_triage.fetch_runs("owner/repo", "a" * 40, limit=1)

    @patch("tools.ci_triage.shutil.which", return_value=None)
    def test_missing_cli_is_blocked(self, _which):
        with self.assertRaisesRegex(RuntimeError, "not installed"):
            ci_triage.fetch_runs("owner/repo", "a" * 40)

    @patch("tools.ci_triage.shutil.which", return_value="gh")
    @patch("tools.ci_triage.subprocess.run")
    def test_invalid_json_is_blocked(self, run_mock, _which):
        run_mock.return_value = Mock(returncode=0, stdout="not-json", stderr="")
        with self.assertRaisesRegex(RuntimeError, "invalid JSON"):
            ci_triage.fetch_runs("owner/repo", "a" * 40)

    @patch("tools.ci_triage.shutil.which", return_value="gh")
    @patch("tools.ci_triage.subprocess.run")
    def test_non_list_json_is_blocked(self, run_mock, _which):
        run_mock.return_value = Mock(returncode=0, stdout=json.dumps({"runs": []}), stderr="")
        with self.assertRaisesRegex(RuntimeError, "unexpected JSON shape"):
            ci_triage.fetch_runs("owner/repo", "a" * 40)

    @patch("tools.ci_triage.shutil.which", return_value="gh")
    @patch("tools.ci_triage.subprocess.run")
    def test_gh_failure_is_blocked(self, run_mock, _which):
        run_mock.return_value = Mock(returncode=1, stdout="", stderr="permission denied")
        with self.assertRaisesRegex(RuntimeError, "permission denied"):
            ci_triage.fetch_runs("owner/repo", "a" * 40)

    @patch("tools.ci_triage.shutil.which", return_value="gh")
    @patch("tools.ci_triage.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="gh", timeout=30))
    def test_gh_timeout_is_blocked(self, _run_mock, _which):
        with self.assertRaisesRegex(RuntimeError, "timed out after 30 seconds"):
            ci_triage.fetch_runs("owner/repo", "a" * 40)

    def test_malformed_sha_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "full 40-character"):
            ci_triage.fetch_runs("owner/repo", "not-a-sha")

    def test_accepts_full_sha256_format(self):
        sha = "a" * 64
        with patch("tools.ci_triage.shutil.which", return_value="gh"), patch("tools.ci_triage.subprocess.run") as run_mock:
            run_mock.return_value = Mock(returncode=0, stdout=json.dumps([{"headSha": sha}]), stderr="")
            self.assertEqual(len(ci_triage.fetch_runs("owner/repo", sha)), 1)

    def test_invalid_repo_and_limit_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "owner/name"):
            ci_triage.fetch_runs("badrepo", "a" * 40)
        with self.assertRaisesRegex(ValueError, "limit"):
            ci_triage.fetch_runs("owner/repo", "a" * 40, limit=101)
        with self.assertRaisesRegex(ValueError, "limit"):
            ci_triage.fetch_runs("owner/repo", "a" * 40, limit=True)

    def test_repo_must_contain_exactly_one_separator(self):
        with self.assertRaisesRegex(ValueError, "owner/name"):
            ci_triage.fetch_runs("owner/name/extra", "a" * 40)


if __name__ == "__main__":
    unittest.main()
