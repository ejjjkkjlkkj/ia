"""Leakage-aware evaluation for the tiny neural byte model.

Checkpoint schema v2 binds the model to the exact training-corpus SHA-256.
This tool verifies that binding and refuses exact train/held-out corpus reuse.
It cannot detect partial overlap or establish semantic quality.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ia_reference.tiny_neural import (  # noqa: E402
    MAX_CHECKPOINT_BYTES,
    MAX_EVALUATION_BYTES,
    MAX_TRAINING_BYTES,
    evaluate_text,
    load_checkpoint,
)


def evaluate(checkpoint_path: Path, heldout_path: Path, training_path: Path) -> dict[str, Any]:
    for path, limit, label in (
        (checkpoint_path, MAX_CHECKPOINT_BYTES, "checkpoint"),
        (training_path, MAX_TRAINING_BYTES, "training corpus"),
        (heldout_path, MAX_EVALUATION_BYTES, "held-out corpus"),
    ):
        if path.stat().st_size > limit:
            raise ValueError(f"{label} exceeds {limit}-byte limit")

    checkpoint_bytes = checkpoint_path.read_bytes()
    heldout_bytes = heldout_path.read_bytes()
    training_bytes = training_path.read_bytes()
    if not training_bytes:
        raise ValueError("training corpus must not be empty")
    if not heldout_bytes:
        raise ValueError("held-out corpus must not be empty")

    try:
        training_bytes.decode("utf-8", errors="strict")
        heldout_text = heldout_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("training and held-out corpora must be valid UTF-8") from exc

    training_sha256 = hashlib.sha256(training_bytes).hexdigest()
    heldout_sha256 = hashlib.sha256(heldout_bytes).hexdigest()
    if heldout_sha256 == training_sha256:
        raise ValueError("held-out corpus exactly matches the training corpus")

    model = load_checkpoint(checkpoint_path)
    if model["training_corpus_sha256"] != training_sha256:
        raise ValueError("supplied training corpus does not match checkpoint training corpus SHA-256")
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
        "learning_rate": model["learning_rate"],
        "checkpoint_training_corpus_match": "PASS",
        "metrics": metrics,
        "limitations": [
            "Only exact corpus hashes are checked; partial overlap or leakage through derived data is not detected.",
            "The embedded hash proves byte identity with the supplied corpus, not that the corpus is licensed or representative.",
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
            temporary_path: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", newline="\n",
                    dir=args.report.parent, prefix=f".{args.report.name}.", suffix=".tmp", delete=False,
                ) as stream:
                    temporary_path = Path(stream.name)
                    stream.write(rendered)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary_path, args.report)
                temporary_path = None
            finally:
                if temporary_path is not None:
                    try:
                        temporary_path.unlink()
                    except FileNotFoundError:
                        pass
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False))
        return 2

    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
