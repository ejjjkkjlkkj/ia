#!/usr/bin/env python3
"""Validate the multimodal capability registry without network access."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "capability-matrix.json"
ALLOWED = {"PLANNED", "DISCOVERED", "LICENSE_REVIEW", "READY_FOR_TEST", "IMPLEMENTED", "TESTED", "BLOCKED", "NOT_VALIDATED"}
REQUIRED = {"id", "name", "inputs", "outputs", "tasks", "status", "metrics"}

def main() -> int:
    try:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"FAIL: cannot parse {REGISTRY}: {exc}")
        return 1
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    categories = data.get("modalities")
    if not isinstance(categories, list) or not categories:
        errors.append("modalities must be a non-empty list")
        categories = []
    seen: set[str] = set()
    for index, item in enumerate(categories):
        prefix = f"modalities[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = sorted(REQUIRED - item.keys())
        if missing:
            errors.append(f"{prefix} missing: {', '.join(missing)}")
            continue
        identifier = item["id"]
        if not isinstance(identifier, str) or not identifier.strip():
            errors.append(f"{prefix}.id must be non-empty text")
        elif identifier in seen:
            errors.append(f"duplicate category id: {identifier}")
        else:
            seen.add(identifier)
        if item["status"] not in ALLOWED:
            errors.append(f"{prefix}.status is unknown: {item['status']!r}")
        for field in ("inputs", "outputs", "tasks", "metrics"):
            value = item[field]
            if not isinstance(value, list) or not value or not all(isinstance(x, str) and x.strip() for x in value):
                errors.append(f"{prefix}.{field} must be a non-empty list of non-empty strings")
    requirements = data.get("cross_cutting_requirements")
    if not isinstance(requirements, list) or not requirements:
        errors.append("cross_cutting_requirements must be a non-empty list")
    print(f"Categories: {len(categories)}")
    print(f"Unique IDs: {len(seen)}")
    print(f"Cross-cutting requirements: {len(requirements) if isinstance(requirements, list) else 0}")
    if errors:
        print("FAIL: registry validation")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: capability registry schema and evidence gates")
    return 0

if __name__ == "__main__":
    sys.exit(main())
