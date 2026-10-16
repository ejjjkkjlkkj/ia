import tempfile
import unittest
from pathlib import Path

from tools.validate_corpus_split import validate_split


class CorpusSplitTests(unittest.TestCase):
    def test_accepts_disjoint_examples(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            training = root / "train.txt"
            heldout = root / "heldout.txt"
            training.write_text("train example\nsecond train\n", encoding="utf-8")
            heldout.write_text("held-out example\nseparate validation\n", encoding="utf-8")
            result = validate_split(training, heldout)
            self.assertEqual(result["exact_overlap"], 0)
            self.assertEqual(result["training_examples"], 2)
            self.assertEqual(result["heldout_examples"], 2)

    def test_rejects_exact_line_leakage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            training = root / "train.txt"
            heldout = root / "heldout.txt"
            training.write_text("shared example\ntraining only\n", encoding="utf-8")
            heldout.write_text("shared example\nheldout only\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "share 1 exact example"):
                validate_split(training, heldout)

    def test_rejects_empty_corpus(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            training = root / "train.txt"
            heldout = root / "heldout.txt"
            training.write_text("   \n", encoding="utf-8")
            heldout.write_text("valid example\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "at least one"):
                validate_split(training, heldout)


if __name__ == "__main__":
    unittest.main()
