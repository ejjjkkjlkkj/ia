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

    def test_rejects_invalid_transition_counts_before_save(self):
        model = train_text("abc")
        model["counts"]["256"]["999"] = 1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            with self.assertRaisesRegex(ValueError, "out of range"):
                save_checkpoint(model, path)
            self.assertFalse(path.exists())

    def test_load_rejects_invalid_payload_even_with_matching_hash(self):
        import hashlib
        model = train_text("abc")
        model["alpha"] = True
        canonical = json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        checkpoint = dict(model, checkpoint_sha256=hashlib.sha256(canonical).hexdigest())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text(json.dumps(checkpoint), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "alpha"):
                load_checkpoint(path)

    def test_rejects_empty_corpus_and_bad_alpha(self):
        with self.assertRaises(ValueError):
            train_text("")
        with self.assertRaises(ValueError):
            train_text("abc", alpha=0)
        with self.assertRaises(ValueError):
            train_text("abc", alpha=True)

if __name__ == "__main__":
    unittest.main()
