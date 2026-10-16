import json
import unittest
from pathlib import Path

from tools.generate_language_status_manifest import build_manifest, read_catalog


ROOT = Path(__file__).resolve().parents[1]


class LanguageStatusManifestTests(unittest.TestCase):
    def test_manifest_covers_every_catalogue_id_without_inventing_passes(self):
        catalogue = read_catalog(ROOT / "LANGUAGE-CATALOG.md")
        manifest_path = ROOT / "data" / "language-implementation-status.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = build_manifest(catalogue)

        self.assertEqual(manifest, expected)
        self.assertEqual(manifest["language_count"], len(catalogue))
        self.assertEqual(len({item["id"] for item in manifest["languages"]}), len(catalogue))
        self.assertEqual(
            {item["id"] for item in manifest["languages"]},
            {item["id"] for item in catalogue},
        )
        self.assertEqual(
            [item["id"] for item in manifest["languages"] if item["status"] == "PARTIAL"],
            ["python"],
        )
        self.assertFalse(any(item["status"] == "PASS" for item in manifest["languages"]))
        self.assertTrue(all(item["evidence"] == [] for item in manifest["languages"] if item["status"] == "NOT_IMPLEMENTED"))

    def test_generator_output_is_deterministic(self):
        manifest = build_manifest(read_catalog(ROOT / "LANGUAGE-CATALOG.md"))
        serialized = json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        self.assertEqual(
            serialized,
            (ROOT / "data" / "language-implementation-status.json").read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
