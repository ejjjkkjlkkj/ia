"""Regression tests for the machine-readable visual accessibility contract."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "data" / "accessibility-screenreader-contract-v1.json"
VALID_STATUSES = {"NOT_IMPLEMENTED", "PARTIAL", "BLOCKED", "NOT_VALIDATED", "PASS"}


def load_contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_contract_has_versioned_identity_and_honest_evidence_status():
    contract = load_contract()
    assert contract["schema_version"] == "1.0.0"
    assert contract["contract_id"] == "ia.visual-accessibility.screenreader"
    assert contract["status"] in VALID_STATUSES
    assert contract["evidence_status"] in VALID_STATUSES
    assert contract["evidence_status"] != "PASS"


def test_contract_requires_keyboard_first_offline_and_privacy_principles():
    principles = set(load_contract()["principles"])
    assert "keyboard_only_operation" in principles
    assert "offline_core_without_api_keys" in principles
    assert "privacy_by_default" in principles
    assert "platform_accessibility_tree_is_primary" in principles
    assert "simulation_is_not_physical_proof" in load_contract()["evidence_rules"]


def test_accessible_element_contract_covers_name_role_state_and_actions():
    fields = set(load_contract()["common_element_fields"])
    assert {"accessible_name", "role", "states", "available_actions"} <= fields
    states = set(load_contract()["recommended_states"])
    assert {"focused", "focusable", "enabled"} <= states


def test_each_platform_adapter_has_official_reference_and_separate_status():
    adapters = load_contract()["platform_adapters"]
    assert {"windows", "linux", "web"} <= {item["platform"] for item in adapters}
    for adapter in adapters:
        assert adapter["status"] in VALID_STATUSES
        assert adapter["official_docs"].startswith("https://")
        assert adapter["interface"]


def test_real_assistive_technology_and_hardware_tests_are_required():
    required = set(load_contract()["required_test_areas"])
    assert "real_screen_reader_interoperability" in required
    assert "real_hardware_validation_for_audio_braille_and_uefi" in required
    outputs = {item["name"]: item["status"] for item in load_contract()["output_modules"]}
    assert outputs["local_speech"] == "NOT_VALIDATED"
    assert outputs["braille"] == "NOT_VALIDATED"
    assert outputs["uefi_bare_metal"] == "NOT_VALIDATED"
