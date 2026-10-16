"""Regression tests for the leakage-aware tiny-model evaluation CLI."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "evaluate_tiny_neural", ROOT / "tools" / "evaluate_tiny_neural.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

from ia_reference.tiny_neural import save_checkpoint, train_text


class EvaluateTinyNeuralTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.training = "training corpus alpha"
        self.checkpoint = self.root / "model.json"
        self.training_path = self.root / "training.txt"
        self.training_path.write_text(self.training, encoding="utf-8")
        save_checkpoint(
            train_text(self.training, epochs=1, learning_rate=0.05, seed=3, embedding_dim=1),
            self.checkpoint,
        )
        self.heldout = self.root / "heldout.txt"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_reports_reproducible_hashes_and_metrics(self) -> None:
        self.heldout.write_text("separate validation corpus", encoding="utf-8")
        report = MODULE.evaluate(self.checkpoint, self.heldout, self.training_path)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(len(report["checkpoint_sha256"]), 64)
        self.assertEqual(len(report["training_corpus_sha256"]), 64)
        self.assertEqual(len(report["heldout_corpus_sha256"]), 64)
        self.assertIn("perplexity", report["metrics"])
        self.assertEqual(report["checkpoint_training_corpus_match"], "PASS")
        self.assertEqual(report["learning_rate"], 0.05)
        self.assertNotEqual(
            report["training_corpus_sha256"], report["heldout_corpus_sha256"]
        )

    def test_refuses_training_corpus_that_does_not_match_checkpoint(self) -> None:
        self.training_path.write_text("different training data", encoding="utf-8")
        self.heldout.write_text("separate validation corpus", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "does not match checkpoint training corpus"):
            MODULE.evaluate(self.checkpoint, self.heldout, self.training_path)

    def test_refuses_exact_training_corpus_reuse(self) -> None:
        self.heldout.write_text(self.training, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "matches the training corpus"):
            MODULE.evaluate(self.checkpoint, self.heldout, self.training_path)

    def test_refuses_empty_heldout_corpus(self) -> None:
        self.heldout.write_bytes(b"")
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            MODULE.evaluate(self.checkpoint, self.heldout, self.training_path)

    def test_refuses_non_utf8_heldout_corpus(self) -> None:
        self.heldout.write_bytes(b"\xff\xfe")
        with self.assertRaisesRegex(ValueError, "valid UTF-8"):
            MODULE.evaluate(self.checkpoint, self.heldout, self.training_path)


if __name__ == "__main__":
    unittest.main()
