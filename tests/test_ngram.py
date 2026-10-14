import json
import tempfile
import unittest
from pathlib import Path

from ia_reference.ngram import evaluate_text, generate, load_checkpoint, save_checkpoint, train_text


class BigramBaselineTests(unittest.TestCase):
    def test_train_evaluate_and_generate(self):
        model = train_text("bonjour monde bonjour monde bonjour monde")
        report = evaluate_text(model, "bonjour monde")
        self.assertEqual(report["tokens"], 3)
        self.assertGreater(report["perplexity"], 0)
        self.assertEqual(generate(model, "bonjour", max_tokens=1), "bonjour monde")

    def test_checkpoint_round_trip_and_hash(self):
        model = train_text("la voix lit le texte la voix lit")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "model.json"
            expected_hash = save_checkpoint(model, path)
            restored = load_checkpoint(path)
            self.assertEqual(restored["checkpoint_sha256"], expected_hash)
            self.assertEqual(generate(restored, "la", max_tokens=3), generate(model, "la", max_tokens=3))

    def test_checkpoint_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.json"
            save_checkpoint(train_text("un deux trois"), path)
            checkpoint = json.loads(path.read_text(encoding="utf-8"))
            checkpoint["training_tokens"] = 999
            path.write_text(json.dumps(checkpoint), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                load_checkpoint(path)

    def test_invalid_training_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            train_text("  ")
        with self.assertRaises(ValueError):
            train_text("hello world", alpha=0)


if __name__ == "__main__":
    unittest.main()
