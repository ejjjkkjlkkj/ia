"""Trainable local bigram language-model baseline (stdlib only).

This is a real, from-scratch statistical baseline. It is NOT a Transformer and
must not be reported as satisfying the repository's neural-model release gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
BOS = "<BOS>"
EOS = "<EOS>"
UNK = "<UNK>"
TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)
MAX_TRAINING_BYTES = 1_000_000
MAX_EVALUATION_BYTES = 100_000
MAX_PROMPT_BYTES = 100_000
MAX_GENERATION_TOKENS = 4_096
MAX_CHECKPOINT_BYTES = 4_000_000
MAX_TRAINING_TOKENS = 100_000
MAX_VOCABULARY_SIZE = 100_000
MAX_JSON_DEPTH = 64


def tokenize(text: str) -> list[str]:
    """Return a deterministic Unicode-aware, lowercase word/punctuation stream."""
    return TOKEN_PATTERN.findall(text.lower())


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _valid_alpha(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value) and 0 < value <= 100
    except (OverflowError, TypeError, ValueError):
        return False


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate checkpoint JSON key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _check_json_nesting(text: str) -> None:
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == chr(92):
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise ValueError("checkpoint JSON nesting exceeds parser limit")
        elif character in "]}":
            depth -= 1
            if depth < 0:
                raise ValueError("malformed checkpoint JSON nesting")


def train_text(text: str, alpha: float = 0.5) -> dict[str, Any]:
    """Fit a smoothed bigram model from text without network access or dependencies."""
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not math.isfinite(alpha) or alpha <= 0:
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
    vocabulary = sorted(set(tokens) | {EOS, UNK})
    return {
        "schema_version": SCHEMA_VERSION,
        "model_type": "smoothed-bigram-baseline-v2",
        "alpha": alpha,
        "vocabulary": vocabulary,
        "counts": normalized_counts,
        "training_tokens": len(tokens),
        "training_corpus_sha256": _sha256(text.encode("utf-8")),
    }


def _validate_model_payload(model: Any) -> None:
    """Reject malformed model data before it reaches probability or generation code."""
    required = {
        "schema_version", "model_type", "alpha", "vocabulary", "counts",
        "training_tokens", "training_corpus_sha256",
    }
    if not isinstance(model, dict) or set(model) != required:
        raise ValueError("checkpoint fields do not match the model schema")
    if type(model["schema_version"]) is not int or model["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported model schema version")
    if model["model_type"] != "smoothed-bigram-baseline-v2":
        raise ValueError("unsupported model type")
    alpha = model["alpha"]
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not math.isfinite(alpha) or alpha <= 0:
        raise ValueError("alpha must be a finite positive number")
    vocabulary = model["vocabulary"]
    if (not isinstance(vocabulary, list) or not vocabulary
            or any(not isinstance(token, str) or not token for token in vocabulary)
            or vocabulary != sorted(set(vocabulary))
            or EOS not in vocabulary or UNK not in vocabulary or BOS in vocabulary):
        raise ValueError("invalid vocabulary")
    training_tokens = model["training_tokens"]
    if type(training_tokens) is not int or training_tokens <= 0:
        raise ValueError("invalid training token count")
    corpus_hash = model["training_corpus_sha256"]
    if not isinstance(corpus_hash, str) or re.fullmatch(r"[0-9a-f]{64}", corpus_hash) is None:
        raise ValueError("invalid training corpus SHA-256")
    counts = model["counts"]
    if not isinstance(counts, dict) or BOS not in counts:
        raise ValueError("invalid transition counts")
    allowed_previous = set(vocabulary) - {EOS}
    allowed_previous.add(BOS)
    allowed_next = set(vocabulary)
    total = 0
    eos_count = 0
    for previous, row in counts.items():
        if not isinstance(previous, str) or previous not in allowed_previous:
            raise ValueError("invalid previous-token key in counts")
        if not isinstance(row, dict) or not row:
            raise ValueError("transition rows must be non-empty objects")
        for token, count in row.items():
            if not isinstance(token, str) or token not in allowed_next:
                raise ValueError("transition token is not in vocabulary")
            if type(count) is not int or count <= 0:
                raise ValueError("transition counts must be positive integers")
            total += count
            if token == EOS:
                eos_count += count
    if total != training_tokens + 1 or eos_count != 1 or sum(counts[BOS].values()) != 1:
        raise ValueError("transition counts do not match training token totals")


def save_checkpoint(model: dict[str, Any], path: str | Path) -> str:
    """Validate and atomically write an integrity-checked JSON checkpoint."""
    payload = dict(model)
    payload.pop("checkpoint_sha256", None)
    _validate_model_payload(payload)
    digest = _sha256(_canonical_json(payload))
    checkpoint = dict(payload)
    checkpoint["checkpoint_sha256"] = digest
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent,
            prefix=f".{destination.name}.", suffix=".tmp", delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(json.dumps(checkpoint, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
    return digest

def load_checkpoint(path: str | Path) -> dict[str, Any]:
    """Load only a structurally valid checkpoint whose content hash matches."""
    try:
        checkpoint = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("cannot read checkpoint JSON") from exc
    if not isinstance(checkpoint, dict):
        raise ValueError("unsupported or malformed checkpoint schema")
    supplied_hash = checkpoint.pop("checkpoint_sha256", None)
    actual_hash = _sha256(_canonical_json(checkpoint))
    if not isinstance(supplied_hash, str) or supplied_hash != actual_hash:
        raise ValueError("checkpoint SHA-256 mismatch")
    _validate_model_payload(checkpoint)
    checkpoint["checkpoint_sha256"] = supplied_hash
    return checkpoint

def next_token_probability(model: dict[str, Any], previous: str, token: str) -> float:
    """Return a normalized add-alpha probability, mapping OOV tokens to UNK."""
    vocabulary = model["vocabulary"]
    vocabulary_set = set(vocabulary)
    if token not in vocabulary_set:
        token = UNK
    if previous != BOS and previous not in vocabulary_set:
        previous = UNK
    alpha = float(model["alpha"])
    counts = model["counts"].get(previous, {})
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
    if previous != BOS and previous not in model["vocabulary"]:
        previous = UNK
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
