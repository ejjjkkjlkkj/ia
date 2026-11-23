"""Generate an honest per-language implementation-status manifest from the shared catalogue."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "LANGUAGE-CATALOG.md"
DEFAULT_OUTPUT = ROOT / "data" / "language-implementation-status.json"
ROW = re.compile(r"^\|\s*([a-z0-9][a-z0-9_-]*)\s*\|\s*([^|]+)\|")


def read_catalog(path: Path = CATALOG) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    in_id_language_table = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\|\s*ID\s*\|\s*Langage\s*\|", line):
            in_id_language_table = True
            continue
        if in_id_language_table and line.lstrip().startswith("|"):
            if re.match(r"^\|\s*:?-{3,}", line):
                continue
            match = ROW.match(line)
            if match:
                entries.append({"id": match.group(1), "language": match.group(2).strip()})
            continue
        in_id_language_table = False
    ids = [entry["id"] for entry in entries]
    if not entries or len(ids) != len(set(ids)):
        raise ValueError("language catalogue is empty or contains duplicate IDs")
    return entries


def build_manifest(entries: list[dict[str, str]]) -> dict[str, object]:
    result = []
    for entry in entries:
        if entry["id"] == "python":
            status = "PARTIAL"
            evidence = [
                "src/ia_reference/numeric.py",
                "src/ia_reference/causal_attention.py",
                "src/ia_reference/tiny_neural.py",
                "tools/run_neural_proof.py",
            ]
            limits = "Python reference kernels and a tiny neural byte model only; no complete Transformer or production LLM."
        else:
            status = "NOT_IMPLEMENTED"
            evidence = []
            limits = "No language-specific implementation of the shared trained model has been evidenced in this repository."
        result.append({
            **entry,
            "status": status,
            "evidence": evidence,
            "limits": limits,
        })
    return {
        "schema_version": 1,
        "catalogue": "LANGUAGE-CATALOG.md",
        "catalogue_version": 2,
        "status_vocabulary": ["PASS", "PARTIAL", "NOT_IMPLEMENTED", "BLOCKED", "NOT_VALIDATED"],
        "generated_by": "tools/generate_language_status_manifest.py",
        "claim_scope": "Repository evidence inventory only. A catalogue entry is not proof of an implementation.",
        "language_count": len(result),
        "languages": result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    manifest = build_manifest(read_catalog())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "PASS",
        "language_count": manifest["language_count"],
        "implemented_partial": sum(x["status"] == "PARTIAL" for x in manifest["languages"]),
        "not_implemented": sum(x["status"] == "NOT_IMPLEMENTED" for x in manifest["languages"]),
        "output": str(args.output),
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
