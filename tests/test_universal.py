import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from ia_reference.universal import evaluate_text, generate, load_checkpoint, next_byte_probability, save_checkpoint, train_text

class UniversalByteModelTests(unittest.TestCase):
    def test_accepts_mixed_natural_and_programming_languages(self):
        corpus = 'Français: bonjour. English: hello. 日本語。 العربية. \nfn main() { println!("你好"); }'
        model = train_text(corpus)
        self.assertEqual(model["model_type"], "universal-utf8-byte-bigram")
        self.assertEqual(model["training_bytes"], len(corpus.encode("utf-8")))
        self.assertGreater(evaluate_text(model, "Rust: let x = 1;")["perplexity"], 0)

    def test_checkpoint_round_trip_and_generation(self):
        model = train_text("hello hello\nfn main() {}\n")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "universal.json"
            digest = save_checkpoint(model, path)
            restored = load_checkpoint(path)
            self.assertEqual(restored["checkpoint_sha256"], digest)
            self.assertEqual(generate(restored, "hello", 8), generate(model, "hello", 8))

    def test_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "universal.json"
            save_checkpoint(train_text("abc"), path)
            checkpoint = json.loads(path.read_text(encoding="utf-8"))
            checkpoint["training_bytes"] = 0
            path.write_text(json.dumps(checkpoint), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_checkpoint(path)

    def test_valid_metadata_tampering_fails_checkpoint_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "universal.json"
            save_checkpoint(train_text("abc"), path)
            checkpoint = json.loads(path.read_text(encoding="utf-8"))
            checkpoint["alpha"] = 0.75
            path.write_text(json.dumps(checkpoint), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checkpoint SHA-256 mismatch"):
                load_checkpoint(path)

    def test_rejects_non_text_and_invalid_unicode_training_inputs(self):
        with self.assertRaisesRegex(ValueError, "must be text"):
            train_text(None)
        with self.assertRaisesRegex(ValueError, "invalid Unicode"):
            train_text(chr(0xD800))

    def test_training_and_evaluation_inputs_are_bounded(self):
        from ia_reference.universal import MAX_TRAINING_BYTES, MAX_EVALUATION_BYTES
        with self.assertRaisesRegex(ValueError, "training data exceeds"):
            train_text("x" * (MAX_TRAINING_BYTES + 1))
        model = train_text("small corpus")
        with self.assertRaisesRegex(ValueError, "evaluation data exceeds"):
            evaluate_text(model, "x" * (MAX_EVALUATION_BYTES + 1))

    def test_alpha_rejects_boolean_non_numeric_nonfinite_and_excessive_values(self):
        for alpha in (True, "0.5", float("nan"), float("inf"), 101):
            with self.subTest(alpha=alpha), self.assertRaises(ValueError):
                train_text("valid", alpha=alpha)

    def test_checkpoint_rejects_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate checkpoint JSON key"):
                load_checkpoint(path)

    def test_checkpoint_rejects_oversized_and_deep_json(self):
        from ia_reference.universal import MAX_CHECKPOINT_BYTES
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversized.json"
            path.write_text(" " * (MAX_CHECKPOINT_BYTES + 1), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "byte limit"):
                load_checkpoint(path)
            path.write_text("[" * 100 + "0" + "]" * 100, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nesting"):
                load_checkpoint(path)

    def test_checkpoint_rejects_invalid_transition_counts_even_with_recomputed_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-counts.json"
            save_checkpoint(train_text("abc"), path)
            document = json.loads(path.read_text(encoding="utf-8"))
            document["counts"]["97"]["98"] = True
            unsigned = {key: value for key, value in document.items() if key != "checkpoint_sha256"}
            canonical = json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
            document["checkpoint_sha256"] = hashlib.sha256(canonical).hexdigest()
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "positive integers"):
                load_checkpoint(path)

    def test_inference_rejects_invalid_argument_types(self):
        model = train_text("valid")
        with self.assertRaisesRegex(ValueError, "previous token"):
            next_byte_probability(model, True, 1)
        with self.assertRaisesRegex(ValueError, "max_bytes"):
            generate(model, "prompt", True)
        with self.assertRaisesRegex(ValueError, "evaluation text must be text"):
            evaluate_text(model, None)

    def test_rejects_empty_corpus_and_bad_alpha(self):
        with self.assertRaises(ValueError):
            train_text("")
        with self.assertRaises(ValueError):
            train_text("abc", alpha=0)

if __name__ == "__main__":
    unittest.main()
