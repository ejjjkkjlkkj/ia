"""Regression tests for the multimodal capability contract."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data" / "multimodal-creative-capabilities-contract-v1.json"
ROADMAP = ROOT / "docs" / "MULTIMODAL-CREATIVE-CAPABILITIES-ROADMAP.md"

class MultimodalCreativeCapabilitiesContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.roadmap = ROADMAP.read_text(encoding="utf-8")

    def test_contract_is_versioned_and_honest_by_default(self):
        self.assertEqual(self.contract["schema_version"], "1.0.0")
        self.assertEqual(self.contract["status"], "NOT_VALIDATED")

    def test_all_requested_media_domains_are_explicit(self):
        capabilities = self.contract["capabilities"]
        for capability in (
            "image_understanding", "image_generation_and_editing",
            "video_understanding", "video_generation_and_editing",
            "film_preproduction_and_postproduction",
            "game_code_asset_and_level_generation",
            "runnable_game_prototyping_and_testing",
            "audio_transcription_and_generation",
            "3d_asset_and_scene_generation", "multimodal_workflow_orchestration",
        ):
            self.assertIn(capability, capabilities)
            self.assertEqual(capabilities[capability], "NOT_VALIDATED")

    def test_evidence_requires_real_outputs_and_logs(self):
        evidence = self.contract["evidence_schema"]
        self.assertIn("artifact_sha256", evidence["required"])
        self.assertIn("logs", evidence["required"])
        self.assertIn("reproducible real execution", evidence["pass_requires"])

    def test_rights_safety_and_accessibility_are_requirements(self):
        joined = " ".join(self.contract["requirements"]).lower()
        for term in ("copyright", "sandbox", "screen-reader", "licensed", "remote processing"):
            self.assertIn(term, joined)

    def test_roadmap_distinguishes_components_from_complete_products(self):
        for term in ("cinéma", "jeux vidéo", "vidéo", "NOT_VALIDATED", "générateur d'images"):
            self.assertIn(term.lower(), self.roadmap.lower())

if __name__ == "__main__":
    unittest.main()
