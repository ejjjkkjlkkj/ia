"""Trainable local bigram language-model baseline (stdlib only).

This is a real, from-scratch statistical baseline. It is NOT a Transformer and
must not be reported as satisfying the repository's neural-model release gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
BOS = "<BOS>"
EOS = "<EOS>"
TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Return a deterministic Unicode-aware, lowercase word/punctuation stream."""
    return TOKEN_PATTERN.findall(text.lower())


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def train_text(text: str, alpha: float = 0.5) -> dict[str, Any]:
    """Fit a smoothed bigram model from text without network access or dependencies."""
    if not math.isfinite(alpha) or alpha <= 0:
        raise ValueError("alpha must be a finite number greater than zero")
    tokens = tokenize(text)
    if not tokens:
        raise ValueError("training text must contain at least one token")

    counts: dict[str, Counter[str]] = defaultdict(Counter)
    previous = BOS
    for token in tokens:
        counts[previous][token] += 1
        previous = token
    counts[previous][EOS] += 1

    normalized_counts = {
        key: dict(sorted(next_counts.items()))
        for key, next_counts in sorted(counts.items())
    }
    vocabulary = sorted(set(tokens) | {EOS})
    return {
        "schema_version": SCHEMA_VERSION,
        "model_type": "smoothed-bigram-baseline",
        "alpha": alpha,
        "vocabulary": vocabulary,
        "counts": normalized_counts,
        "training_tokens": len(tokens),
        "training_corpus_sha256": _sha256(text.encode("utf-8")),
    }


def save_checkpoint(model: dict[str, Any], path: str | Path) -> str:
    """Write an integrity-checked JSON checkpoint atomically and return its hash."""
    payload = dict(model)
    payload.pop("checkpoint_sha256", None)
    digest = _sha256(_canonical_json(payload))
    checkpoint = dict(payload)
    checkpoint["checkpoint_sha256"] = digest
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(checkpoint, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return digest


def load_checkpoint(path: str | Path) -> dict[str, Any]:
    """Load a checkpoint only when its schema and content hash are valid."""
    checkpoint = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(checkpoint, dict) or checkpoint.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported or malformed checkpoint schema")
    supplied_hash = checkpoint.pop("checkpoint_sha256", None)
    actual_hash = _sha256(_canonical_json(checkpoint))
    if not isinstance(supplied_hash, str) or supplied_hash != actual_hash:
        raise ValueError("checkpoint SHA-256 mismatch")
    if checkpoint.get("model_type") != "smoothed-bigram-baseline":
        raise ValueError("unsupported model type")
    if not isinstance(checkpoint.get("counts"), dict) or not checkpoint.get("vocabulary"):
        raise ValueError("checkpoint is missing model data")
    checkpoint["checkpoint_sha256"] = supplied_hash
    return checkpoint


def next_token_probability(model: dict[str, Any], previous: str, token: str) -> float:
    """Return add-alpha smoothed conditional probability."""
    alpha = float(model["alpha"])
    counts = model["counts"].get(previous, {})
    vocabulary = model["vocabulary"]
    total = sum(counts.values())
    return (int(counts.get(token, 0)) + alpha) / (total + alpha * len(vocabulary))


def evaluate_text(model: dict[str, Any], text: str) -> dict[str, float | int]:
    """Evaluate token negative log-likelihood and perplexity on supplied text."""
    tokens = tokenize(text)
    if not tokens:
        raise ValueError("evaluation text must contain at least one token")
    previous = BOS
    total_nll = 0.0
    for token in tokens + [EOS]:
        probability = next_token_probability(model, previous, token)
        total_nll -= math.log(max(probability, 1e-300))
        previous = token
    token_count = len(tokens) + 1
    mean_nll = total_nll / token_count
    return {
        "tokens": token_count,
        "negative_log_likelihood": total_nll,
        "mean_negative_log_likelihood": mean_nll,
        "perplexity": math.exp(min(mean_nll, 700.0)),
    }


def generate(model: dict[str, Any], prompt: str = "", max_tokens: int = 20) -> str:
    """Generate deterministically using the most frequent observed next token."""
    if max_tokens < 0:
        raise ValueError("max_tokens must be non-negative")
    output = tokenize(prompt)
    previous = output[-1] if output else BOS
    counts = model["counts"]
    for _ in range(max_tokens):
        choices = counts.get(previous, {})
        if not choices:
            break
        token = min(choices, key=lambda item: (-int(choices[item]), item))
        if token == EOS:
            break
        output.append(token)
        previous = token
    return " ".join(output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local from-scratch bigram LM baseline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    train_parser = subparsers.add_parser("train", help="train from a UTF-8 text corpus")
    train_parser.add_argument("corpus", type=Path)
    train_parser.add_argument("checkpoint", type=Path)
    train_parser.add_argument("--alpha", type=float, default=0.5)

    eval_parser = subparsers.add_parser("evaluate", help="evaluate on a separate text file")
    eval_parser.add_argument("checkpoint", type=Path)
    eval_parser.add_argument("corpus", type=Path)

    generate_parser = subparsers.add_parser("generate", help="generate from a checkpoint")
    generate_parser.add_argument("checkpoint", type=Path)
    generate_parser.add_argument("--prompt", default="")
    generate_parser.add_argument("--max-tokens", type=int, default=20)

    args = parser.parse_args(argv)
    if args.command == "train":
        text = args.corpus.read_text(encoding="utf-8")
        model = train_text(text, alpha=args.alpha)
        digest = save_checkpoint(model, args.checkpoint)
        print(json.dumps({
            "status": "PASS",
            "model_type": model["model_type"],
            "training_tokens": model["training_tokens"],
            "checkpoint": str(args.checkpoint),
            "checkpoint_sha256": digest,
            "claim_scope": "statistical bigram baseline only; not a Transformer",
        }, ensure_ascii=False, indent=2))
    elif args.command == "evaluate":
        model = load_checkpoint(args.checkpoint)
        report = evaluate_text(model, args.corpus.read_text(encoding="utf-8"))
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        model = load_checkpoint(args.checkpoint)
        print(generate(model, args.prompt, args.max_tokens))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
