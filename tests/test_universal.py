import json
import tempfile
import unittest
from pathlib import Path
from ia_reference.universal import evaluate_text, generate, load_checkpoint, save_checkpoint, train_text

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
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                load_checkpoint(path)

    def test_rejects_duplicate_json_keys_even_with_valid_outer_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate checkpoint JSON key"):
                load_checkpoint(path)

    def test_rejects_nonstandard_json_constants(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "constant.json"
            path.write_text('{"checkpoint_sha256":"x","alpha":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-standard JSON constant"):
                load_checkpoint(path)

    def test_rejects_excessive_nesting(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested.json"
            path.write_text("[" * 100 + "0" + "]" * 100, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nesting exceeds parser limit"):
                load_checkpoint(path)

    def test_rejects_invalid_transition_counts_even_if_hash_is_recomputed(self):
        from ia_reference.universal import _canonical_json, _sha256
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-counts.json"
            model = train_text("abc")
            model["counts"]["97"]["98"] = 0
            payload = dict(model)
            payload.pop("checkpoint_sha256", None)
            payload["checkpoint_sha256"] = _sha256(_canonical_json(payload))
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "positive integers"):
                load_checkpoint(path)

    def test_rejects_checkpoint_over_size_limit(self):
        from ia_reference.universal import MAX_CHECKPOINT_BYTES
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversized.json"
            path.write_text(" " * (MAX_CHECKPOINT_BYTES + 1), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "byte limit"):
                load_checkpoint(path)

    def test_rejects_empty_corpus_and_bad_alpha(self):
        with self.assertRaises(ValueError):
            train_text("")
        with self.assertRaises(ValueError):
            train_text("abc", alpha=0)

if __name__ == "__main__":
    unittest.main()
