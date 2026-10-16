"""Leakage-aware, reproducible evaluation CLI for the tiny neural byte model.

The training corpus is supplied separately because checkpoint schema v1 does
not embed its source corpus hash. This tool refuses exact corpus reuse and
emits hashes so results can be audited. It does not claim semantic quality.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ia_reference.tiny_neural import evaluate_text, load_checkpoint  # noqa: E402


def evaluate(checkpoint_path: Path, heldout_path: Path, training_path: Path) -> dict[str, Any]:
    checkpoint_bytes = checkpoint_path.read_bytes()
    heldout_bytes = heldout_path.read_bytes()
    training_bytes = training_path.read_bytes()
    if not training_bytes:
        raise ValueError("training corpus must not be empty")
    if not heldout_bytes:
        raise ValueError("held-out corpus must not be empty")

    try:
        training_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("training corpus must be valid UTF-8") from exc
    try:
        heldout_text = heldout_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("held-out corpus must be valid UTF-8") from exc

    training_sha256 = hashlib.sha256(training_bytes).hexdigest()
    heldout_sha256 = hashlib.sha256(heldout_bytes).hexdigest()
    if heldout_sha256 == training_sha256:
        raise ValueError("held-out corpus exactly matches the training corpus")

    model = load_checkpoint(checkpoint_path)
    metrics = evaluate_text(model, heldout_text)
    return {
        "schema_version": 1,
        "status": "PASS",
        "evaluation": "held-out UTF-8 byte next-token prediction",
        "checkpoint_sha256": hashlib.sha256(checkpoint_bytes).hexdigest(),
        "training_corpus_sha256": training_sha256,
        "heldout_corpus_sha256": heldout_sha256,
        "heldout_bytes": len(heldout_bytes),
        "model_type": model["model_type"],
        "model_schema_version": model["schema_version"],
        "seed": model["seed"],
        "epochs": model["epochs"],
        "embedding_dim": model["embedding_dim"],
        "metrics": metrics,
        "limitations": [
            "Only exact byte-for-byte corpus equality is checked; partial overlap is not detected.",
            "The supplied training corpus must be the exact corpus used to create the checkpoint; this relationship cannot be independently proven by checkpoint schema v1.",
            "Perplexity measures byte-level prediction, not semantic correctness.",
            "This tiny reference model is not a production LLM.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("training_corpus", type=Path, help="exact UTF-8 corpus used to train this checkpoint")
    parser.add_argument("heldout_corpus", type=Path)
    parser.add_argument("--report", type=Path, help="optional JSON report output path")
    args = parser.parse_args()
    try:
        report = evaluate(args.checkpoint, args.heldout_corpus, args.training_corpus)
        rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.report.with_name(args.report.name + ".tmp")
            temporary.write_text(rendered, encoding="utf-8")
            temporary.replace(args.report)
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False))
        return 2

    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
