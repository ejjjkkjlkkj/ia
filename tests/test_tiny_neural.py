import json
import tempfile
import unittest
from pathlib import Path

from ia_reference.tiny_neural import (
    MODEL_TYPE, evaluate_text, generate, load_checkpoint, next_token_probabilities,
    save_checkpoint, train_text,
)


class TinyNeuralModelTests(unittest.TestCase):
    def test_training_provenance_hash_is_recorded_and_validated(self):
        import hashlib
        text = "provenance—😊\n"
        model = train_text(text, epochs=1)
        self.assertEqual(model["schema_version"], 2)
        self.assertEqual(model["learning_rate"], 0.05)
        self.assertEqual(
            model["training_corpus_sha256"],
            hashlib.sha256(text.encode("utf-8")).hexdigest(),
        )
        tampered = dict(model)
        tampered["training_corpus_sha256"] = "not-a-hash"
        with self.assertRaisesRegex(ValueError, "training corpus SHA-256"):
            evaluate_text(tampered, "held out")

    def test_training_is_deterministic_and_changes_parameters(self):
        first = train_text("hello\nbonjour\n", epochs=2, seed=11)
        second = train_text("hello\nbonjour\n", epochs=2, seed=11)
        self.assertEqual(first, second)
        self.assertEqual(first["model_type"], MODEL_TYPE)
        self.assertNotEqual(first["bias"], [0.0] * 258)

    def test_probability_distribution_is_normalized(self):
        model = train_text("abcabc", epochs=1)
        probabilities = next_token_probabilities(model, ord("a"))
        self.assertEqual(len(probabilities), 258)
        self.assertAlmostEqual(sum(probabilities), 1.0, places=12)
        self.assertTrue(all(0.0 <= value <= 1.0 for value in probabilities))

    def test_evaluation_and_generation_validate_model_only_once(self):
        from unittest.mock import patch
        import ia_reference.tiny_neural as implementation

        model = train_text("abcabcabc\n", epochs=1)
        with patch.object(implementation, "_validate_model", wraps=implementation._validate_model) as validate:
            report = evaluate_text(model, "abcabc\n")
            self.assertGreater(report["perplexity"], 1)
            validate.assert_called_once()
        with patch.object(implementation, "_validate_model", wraps=implementation._validate_model) as validate:
            generated = generate(model, "abc", max_bytes=8)
            self.assertIsInstance(generated, str)
            validate.assert_called_once()

    def test_evaluation_and_generation(self):
        model = train_text("screen reader speaks text\n", epochs=2)
        report = evaluate_text(model, "screen reader")
        self.assertGreater(report["mean_cross_entropy"], 0)
        self.assertGreater(report["perplexity"], 1)
        self.assertIsInstance(generate(model, "screen", max_bytes=8), str)

    def test_checkpoint_round_trip_and_tampering_detection(self):
        model = train_text("local model", epochs=1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.json"
            digest = save_checkpoint(model, path)
            restored = load_checkpoint(path)
            self.assertEqual({key: value for key, value in restored.items() if key != "checkpoint_sha256"}, model)
            self.assertEqual(restored["checkpoint_sha256"], digest)
            self.assertGreater(evaluate_text(restored, "local")["perplexity"], 0)
            document = json.loads(path.read_text(encoding="utf-8"))
            document["bias"][0] += 0.25
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                load_checkpoint(path)

    def test_checkpoint_rejects_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate checkpoint JSON key"):
                load_checkpoint(path)

    def test_checkpoint_rejects_oversized_input(self):
        from ia_reference.tiny_neural import MAX_CHECKPOINT_BYTES
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversized.json"
            path.write_text(" " * (MAX_CHECKPOINT_BYTES + 1), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "byte limit"):
                load_checkpoint(path)

    def test_checkpoint_rejects_excessive_json_nesting(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested.json"
            path.write_text("[" * 3000 + "0" + "]" * 3000, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nesting exceeds parser limit"):
                load_checkpoint(path)

    def test_rejects_out_of_range_checkpoint_training_metadata(self):
        model = train_text("valid", epochs=1)
        model["training_bytes"] = 10_001
        with self.assertRaisesRegex(ValueError, "invalid training metadata"):
            evaluate_text(model, "valid")

    def test_rejects_invalid_training_options(self):
        for kwargs in ({"epochs": 0}, {"epochs": True}, {"learning_rate": float("nan")}, {"embedding_dim": 0}, {"seed": True}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    train_text("valid", **kwargs)

    def test_rejects_training_that_exceeds_compute_budget(self):
        with self.assertRaisesRegex(ValueError, "operation budget"):
            train_text("x" * 10_000, epochs=20, embedding_dim=64)

    def test_rejects_out_of_range_seed_and_large_evaluation(self):
        with self.assertRaisesRegex(ValueError, "signed 64-bit"):
            train_text("valid", seed=1 << 80)
        model = train_text("valid", epochs=1)
        with self.assertRaisesRegex(ValueError, "evaluation data exceeds"):
            evaluate_text(model, "x" * 100_001)

    def test_rejects_empty_or_oversized_data(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            train_text("")
        with self.assertRaisesRegex(ValueError, "byte limit"):
            train_text("x" * 10_001)

    def test_cli_train_checkpoint_evaluate_generate(self):
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            train = root / "train.txt"
            heldout = root / "heldout.txt"
            checkpoint = root / "model.json"
            train.write_text("the screen reader speaks text\n", encoding="utf-8")
            heldout.write_text("screen reader\n", encoding="utf-8")
            import os
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path("src").resolve())
            trained = subprocess.run(
                [sys.executable, "-m", "ia_reference.tiny_neural", "train",
                 str(train), str(checkpoint), "--epochs", "1", "--learning-rate", "0.03",
                 "--embedding-dim", "4"],
                env=env, check=True, capture_output=True, text=True,
            )
            training_report = json.loads(trained.stdout)
            self.assertEqual(training_report["status"], "PASS")
            self.assertEqual(training_report["embedding_dim"], 4)
            self.assertEqual(training_report["learning_rate"], 0.03)
            self.assertEqual(len(training_report["training_corpus_sha256"]), 64)
            evaluated = subprocess.run([sys.executable, "-m", "ia_reference.tiny_neural", "evaluate", str(checkpoint), str(heldout)], env=env, check=True, capture_output=True, text=True)
            evaluation_report = json.loads(evaluated.stdout)
            self.assertIn("perplexity", evaluation_report)
            self.assertEqual(len(evaluation_report["evaluation_corpus_sha256"]), 64)
            generated = subprocess.run([sys.executable, "-m", "ia_reference.tiny_neural", "generate", str(checkpoint), "--prompt", "screen", "--max-bytes", "4"], env=env, check=True, capture_output=True, text=True)
            self.assertTrue(generated.stdout.strip())


if __name__ == "__main__":
    unittest.main()
