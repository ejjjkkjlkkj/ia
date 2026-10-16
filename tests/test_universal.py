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
            with self.assertRaisesRegex(ValueError, "invalid training byte metadata"):
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

    def test_rejects_empty_corpus_and_bad_alpha(self):
        with self.assertRaises(ValueError):
            train_text("")
        with self.assertRaises(ValueError):
            train_text("abc", alpha=0)

if __name__ == "__main__":
    unittest.main()
