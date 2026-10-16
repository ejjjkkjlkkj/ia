"""Regression tests for the universal disability-inclusion contract."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "data" / "universal-disability-inclusion-contract-v1.json"
VALID_STATUSES = {"NOT_IMPLEMENTED", "PARTIAL", "BLOCKED", "NOT_VALIDATED", "PASS"}


def load_contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_contract_is_versioned_and_does_not_claim_unverified_success():
    contract = load_contract()
    assert contract["schema_version"] == "1.0.0"
    assert contract["contract_id"] == "ia.universal-disability-inclusion"
    assert contract["status"] == "PARTIAL"
    assert contract["evidence_status"] == "NOT_VALIDATED"


def test_all_major_disability_domains_are_explicit_and_not_ranked():
    domains = {item["id"] for item in load_contract()["coverage_domains"]}
    assert {
        "vision", "hearing", "mobility_motor", "speech_communication",
        "cognitive_learning_neurodivergence", "mental_health_fatigue_chronic_pain",
        "multiple_fluctuating_invisible_temporary"
    } <= domains


def test_privacy_choice_and_no_diagnosis_requirements_are_mandatory():
    contract = load_contract()
    principles = set(contract["principles"])
    assert "no_diagnosis_or_medical_disclosure_required" in principles
    assert "user_control_and_configurable_preferences" in principles
    assert "privacy_by_default_no_silent_medical_inference" in principles
    requirements = set(contract["essential_requirements"])
    assert "preferences_are_combinable_and_changeable" in requirements
    assert "no_essential_task_requires_voice_input" in requirements


def test_validation_requires_real_context_and_user_testing():
    validation = load_contract()["validation"]
    assert validation["automated_test_is_user_validation"] is False
    assert "assistive_technology" in validation["evidence_fields"]
    assert "results" in validation["evidence_fields"]
    assert "automated_manual_specialist_and_user_testing" in validation["required_areas"]


def test_references_are_https_and_evidence_statuses_are_known():
    contract = load_contract()
    assert all(url.startswith("https://") for url in contract["references"])
    assert set(contract["evidence_statuses"]) == VALID_STATUSES
