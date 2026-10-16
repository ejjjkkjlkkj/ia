import json
import tempfile
import unittest
from pathlib import Path

from ia_reference.ngram import UNK, evaluate_text, generate, load_checkpoint, next_token_probability, save_checkpoint, train_text


class BigramBaselineTests(unittest.TestCase):
    def test_train_evaluate_and_generate(self):
        model = train_text("bonjour monde bonjour monde bonjour monde")
        report = evaluate_text(model, "bonjour monde")
        self.assertEqual(report["tokens"], 3)
        self.assertGreater(report["perplexity"], 0)
        self.assertEqual(generate(model, "bonjour", max_tokens=1), "bonjour monde")

    def test_oov_tokens_map_to_unk_and_probabilities_normalize(self):
        model = train_text("alpha beta alpha gamma")
        self.assertIn(UNK, model["vocabulary"])
        self.assertEqual(
            next_token_probability(model, "alpha", "never-seen"),
            next_token_probability(model, "alpha", UNK),
        )
        total = sum(next_token_probability(model, "alpha", token) for token in model["vocabulary"])
        self.assertAlmostEqual(total, 1.0, places=12)
        report = evaluate_text(model, "unseen-token")
        self.assertGreater(report["perplexity"], 0)

    def test_boolean_smoothing_parameter_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "alpha"):
            train_text("alpha beta", alpha=True)

    def test_checkpoint_round_trip_and_hash(self):
        model = train_text("la voix lit le texte la voix lit")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "model.json"
            expected_hash = save_checkpoint(model, path)
            self.assertEqual(list(path.parent.glob(".model.json.*.tmp")), [])
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

    def test_invalid_model_structure_is_rejected_before_save(self):
        model = train_text("bonjour monde bonjour")
        model["counts"]["bonjour"]["not-in-vocabulary"] = 1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            with self.assertRaisesRegex(ValueError, "not in vocabulary"):
                save_checkpoint(model, path)
            self.assertFalse(path.exists())

    def test_rejects_non_text_and_invalid_unicode_training_inputs(self):
        with self.assertRaisesRegex(ValueError, "training text must be text"):
            train_text(None)
        with self.assertRaisesRegex(ValueError, "invalid Unicode"):
            train_text(chr(0xD800))

    def test_training_and_evaluation_inputs_are_bounded(self):
        from ia_reference.ngram import MAX_TRAINING_BYTES, MAX_EVALUATION_BYTES
        with self.assertRaisesRegex(ValueError, "training data exceeds"):
            train_text("x" * (MAX_TRAINING_BYTES + 1))
        model = train_text("small corpus")
        with self.assertRaisesRegex(ValueError, "evaluation data exceeds"):
            evaluate_text(model, "x" * (MAX_EVALUATION_BYTES + 1))

    def test_alpha_overflow_and_invalid_runtime_types_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "alpha"):
            train_text("valid", alpha=10 ** 1000)
        model = train_text("alpha beta")
        with self.assertRaisesRegex(ValueError, "must be text"):
            next_token_probability(model, [], "alpha")
        with self.assertRaisesRegex(ValueError, "max_tokens"):
            generate(model, "alpha", True)
        with self.assertRaisesRegex(ValueError, "max_tokens"):
            generate(model, "alpha", 4097)

    def test_checkpoint_rejects_duplicate_keys_oversize_and_deep_json(self):
        from ia_reference.ngram import MAX_CHECKPOINT_BYTES
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.json"
            path.write_text('{"schema_version":2,"schema_version":2}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate checkpoint JSON key"):
                load_checkpoint(path)
            path.write_text(" " * (MAX_CHECKPOINT_BYTES + 1), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "byte limit"):
                load_checkpoint(path)
            path.write_text("[" * 100 + "0" + "]" * 100, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nesting"):
                load_checkpoint(path)

    def test_checkpoint_rejects_escaped_surrogate_unicode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-unicode.json"
            path.write_text(
                r'{"schema_version":2,"model_type":"smoothed-bigram-baseline-v2",'
                r'"alpha":0.5,"vocabulary":["<EOS>","<UNK>","\ud800"],'
                r'"counts":{"<BOS>":{"<UNK>":1},"<UNK>":{"<EOS>":1}},'
                r'"training_tokens":1,"training_corpus_sha256":"' + "0" * 64 +
                r'","checkpoint_sha256":"' + "0" * 64 + r'"}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "model JSON cannot be canonically encoded"):
                load_checkpoint(path)

    def test_tokenizer_rejects_non_text_and_invalid_unicode(self):
        from ia_reference.ngram import tokenize
        with self.assertRaisesRegex(ValueError, "input must be text"):
            tokenize(None)
        with self.assertRaisesRegex(ValueError, "invalid Unicode"):
            tokenize(chr(0xD800))

    def test_invalid_training_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            train_text("  ")
        with self.assertRaises(ValueError):
            train_text("hello world", alpha=0)


if __name__ == "__main__":
    unittest.main()
