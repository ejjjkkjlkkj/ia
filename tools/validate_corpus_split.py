#!/usr/bin/env python3
"""Validate that local model training and held-out corpora have no exact line overlap."""
from __future__ import annotations

import argparse
from pathlib import Path

MAX_CORPUS_BYTES = 1_000_000


def _read_examples(path: Path, label: str) -> set[str]:
    with path.open("rb") as stream:
        raw = stream.read(MAX_CORPUS_BYTES + 1)
    if len(raw) > MAX_CORPUS_BYTES:
        raise ValueError(f"{label} corpus exceeds {MAX_CORPUS_BYTES}-byte limit")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label} corpus must be valid UTF-8") from exc
    examples = {line.strip() for line in text.splitlines() if line.strip()}
    if not examples:
        raise ValueError(f"{label} corpus must contain at least one non-empty example")
    return examples


def validate_split(training_path: Path, heldout_path: Path) -> dict[str, int]:
    training = _read_examples(training_path, "training")
    heldout = _read_examples(heldout_path, "held-out")
    overlap = training & heldout
    if overlap:
        raise ValueError(f"training and held-out corpora share {len(overlap)} exact example(s)")
    return {"training_examples": len(training), "heldout_examples": len(heldout), "exact_overlap": 0}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("training", type=Path)
    parser.add_argument("heldout", type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate_split(args.training, args.heldout)
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print(f"PASS: {result['training_examples']} training examples; "
          f"{result['heldout_examples']} disjoint held-out examples; exact overlap=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
