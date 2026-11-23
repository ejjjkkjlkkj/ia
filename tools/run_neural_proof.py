"""Run a reproducible, leakage-aware proof of the tiny neural baseline.

This is a functionality/traceability smoke test, not evidence of broad language
quality or superiority over external models. Only deterministic synthetic text
is used; no network access or external model is required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
import time
from pathlib import Path
from typing import Any

from ia_reference.tiny_neural import (
    MODEL_TYPE,
    evaluate_text,
    generate,
    load_checkpoint,
    save_checkpoint,
    train_text,
)

TRAIN_TEXT = (
    "alpha beta alpha gamma\n"
    "beta gamma beta alpha\n"
    "alpha beta gamma alpha\n"
)
HELDOUT_TEXT = "gamma beta alpha\n"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_proof(output_dir: str | Path) -> dict[str, Any]:
    """Train, save, reload, evaluate held-out text, and record inspectable evidence."""
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    checkpoint_path = root / "tiny-neural-proof.json"
    report_path = root / "tiny-neural-proof-report.json"

    start = time.perf_counter()
    model = train_text(TRAIN_TEXT, epochs=2, learning_rate=0.05, seed=20261016)
    train_seconds = time.perf_counter() - start
    checkpoint_sha256 = save_checkpoint(model, checkpoint_path)
    reloaded = load_checkpoint(checkpoint_path)
    evaluation = evaluate_text(reloaded, HELDOUT_TEXT)
    generated = generate(reloaded, "alpha", max_bytes=16)

    if not math.isfinite(evaluation["mean_cross_entropy"]) or not math.isfinite(evaluation["perplexity"]):
        raise RuntimeError("held-out evaluation produced non-finite metrics")
    if evaluation["tokens"] != len(HELDOUT_TEXT.encode("utf-8")) + 1:
        raise RuntimeError("held-out token count does not match the declared evaluation corpus")
    if reloaded.get("checkpoint_sha256") != checkpoint_sha256:
        raise RuntimeError("checkpoint digest changed during round-trip")
    if not isinstance(generated, str):
        raise RuntimeError("generation did not return text")

    report: dict[str, Any] = {
        "schema_version": 1,
        "status": "PASS",
        "claim_scope": "synthetic functionality smoke test only; not a quality or superiority claim",
        "model_type": MODEL_TYPE,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "seed": 20261016,
        "epochs": 2,
        "learning_rate": 0.05,
        "training_bytes": len(TRAIN_TEXT.encode("utf-8")),
        "training_corpus_sha256": _sha256(TRAIN_TEXT.encode("utf-8")),
        "heldout_bytes": len(HELDOUT_TEXT.encode("utf-8")),
        "heldout_corpus_sha256": _sha256(HELDOUT_TEXT.encode("utf-8")),
        "heldout_metrics": evaluation,
        "generated_text": generated,
        "checkpoint_sha256": checkpoint_sha256,
        "checkpoint_bytes": checkpoint_path.stat().st_size,
        "training_seconds": round(train_seconds, 6),
        "leakage_check": "PASS: training and held-out corpus strings are distinct",
        "round_trip_check": "PASS: checkpoint saved, hash-validated, and reloaded",
    }
    if TRAIN_TEXT == HELDOUT_TEXT:
        raise RuntimeError("training and held-out corpora must be distinct")
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report = run_proof(args.output_dir)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
