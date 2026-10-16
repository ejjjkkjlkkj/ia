"""Regression guards for workflow publication safety and evidence handling."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


class WorkflowPublicationSafetyTests(unittest.TestCase):
    def test_autonomous_development_workflow_cannot_publish_changes(self):
        workflow = (WORKFLOWS / "own-model-development.yml").read_text(encoding="utf-8")
        self.assertRegex(workflow, r"(?m)^permissions:\n  contents: read$")
        self.assertIn("persist-credentials: false", workflow)
        self.assertNotIn("pull-requests: write", workflow)
        self.assertNotRegex(
            workflow,
            r"(?m)^\s*(?:git\s+(?:commit|push)\b|gh\s+pr\s+(?:create|merge)\b)",
        )

    def test_model_evidence_upload_requires_training_step_to_start(self):
        workflow = (WORKFLOWS / "own-model-hourly-validation.yml").read_text(encoding="utf-8")
        self.assertIn("id: train_evaluate", workflow)
        self.assertIn("if: always() && steps.train_evaluate.outcome != 'skipped'", workflow)
        self.assertIn("if-no-files-found: error", workflow)
        self.assertRegex(workflow, r"(?m)^\s*path: model-evidence/$")


if __name__ == "__main__":
    unittest.main()
