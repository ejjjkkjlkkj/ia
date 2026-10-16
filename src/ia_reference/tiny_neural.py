"""Small from-scratch trainable neural byte language model (stdlib only).

This is a CPU reference experiment, not a production LLM. It learns a
single-hidden-layer next-byte predictor and records deterministic checkpoints.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
MODEL_TYPE = "tiny-neural-utf8-byte"
BOS, EOS, VOCAB_SIZE = 256, 257, 258
EMBED_DIM = 8
MAX_TRAINING_BYTES = 10_000
MAX_EPOCHS = 20
MAX_CHECKPOINT_BYTES = 2_000_000
MAX_TRAINING_WORK = 40_000_000
MAX_EVALUATION_BYTES = 100_000
MAX_SEED = (1 << 63) - 1


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate checkpoint JSON key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _check_json_nesting(text: str, max_depth: int = 64) -> None:
    """Reject excessively nested JSON consistently across Python versions."""
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
            if depth > max_depth:
                raise ValueError("checkpoint JSON nesting exceeds parser limit")
        elif character in "]}":
            depth -= 1


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    try:
        finite = math.isfinite(value)
    except (OverflowError, TypeError):
        finite = False
    if not finite:
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def _validate_model(model: Any, require_hash: bool = False) -> dict[str, Any]:
    if not isinstance(model, dict):
        raise ValueError("checkpoint must be an object")
    required = {"schema_version", "model_type", "vocab_size", "embedding_dim", "seed", "training_bytes", "training_corpus_sha256", "epochs", "learning_rate", "embedding", "weights", "bias"}
    allowed = required | {"checkpoint_sha256"}
    if set(model) not in (required, allowed) or (require_hash and set(model) != allowed):
        raise ValueError("invalid checkpoint fields")
    if type(model["schema_version"]) is not int or model["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported checkpoint schema")
    if model["model_type"] != MODEL_TYPE or type(model["vocab_size"]) is not int or model["vocab_size"] != VOCAB_SIZE:
        raise ValueError("unsupported model type or vocabulary")
    dim = model["embedding_dim"]
    if type(dim) is not int or not 1 <= dim <= 64:
        raise ValueError("embedding dimension out of range")
    if (type(model["seed"]) is not int or not -(1 << 63) <= model["seed"] <= MAX_SEED
            or type(model["training_bytes"]) is not int
            or not 1 <= model["training_bytes"] <= MAX_TRAINING_BYTES):
        raise ValueError("invalid training metadata")
    corpus_hash = model["training_corpus_sha256"]
    if not isinstance(corpus_hash, str) or len(corpus_hash) != 64 or any(c not in "0123456789abcdef" for c in corpus_hash):
        raise ValueError("invalid training corpus SHA-256")
    if type(model["epochs"]) is not int or not 1 <= model["epochs"] <= MAX_EPOCHS:
        raise ValueError("invalid epoch metadata")
    learning_rate = _finite_number(model["learning_rate"], "learning_rate")
    if not 0 < learning_rate <= 1:
        raise ValueError("invalid learning-rate metadata")
    embedding, weights, bias = model["embedding"], model["weights"], model["bias"]
    if not isinstance(embedding, list) or len(embedding) != VOCAB_SIZE or not isinstance(weights, list) or len(weights) != VOCAB_SIZE or not isinstance(bias, list) or len(bias) != VOCAB_SIZE:
        raise ValueError("invalid parameter shapes")
    for matrix in (embedding, weights):
        for row in matrix:
            if not isinstance(row, list) or len(row) != dim:
                raise ValueError("invalid parameter dimensions")
            for item in row:
                if abs(_finite_number(item, "parameter")) > 1000:
                    raise ValueError("parameter magnitude exceeds safety bound")
    for item in bias:
        if abs(_finite_number(item, "bias")) > 1000:
            raise ValueError("bias magnitude exceeds safety bound")
    if "checkpoint_sha256" in model:
        unsigned = {key: value for key, value in model.items() if key != "checkpoint_sha256"}
        if not isinstance(model["checkpoint_sha256"], str) or model["checkpoint_sha256"] != _digest(unsigned):
            raise ValueError("checkpoint SHA-256 mismatch")
    return model


def train_text(text: str, *, epochs: int = 3, learning_rate: float = 0.05, seed: int = 7, embedding_dim: int = EMBED_DIM) -> dict[str, Any]:
    """Train a tiny byte-level neural next-token model deterministically."""
    if not isinstance(text, str):
        raise ValueError("training text must be text")
    try:
        data = text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError("training text contains invalid Unicode") from exc
    if not data:
        raise ValueError("training text must not be empty")
    if len(data) > MAX_TRAINING_BYTES:
        raise ValueError(f"training data exceeds {MAX_TRAINING_BYTES}-byte limit")
    if type(epochs) is not int or not 1 <= epochs <= MAX_EPOCHS:
        raise ValueError(f"epochs must be between 1 and {MAX_EPOCHS}")
    if type(seed) is not int or not -(1 << 63) <= seed <= MAX_SEED:
        raise ValueError("seed must be a signed 64-bit integer")
    if type(embedding_dim) is not int or not 1 <= embedding_dim <= 64:
        raise ValueError("embedding_dim must be between 1 and 64")
    lr = _finite_number(learning_rate, "learning_rate")
    if not 0 < lr <= 1:
        raise ValueError("learning_rate must be in (0, 1]")

    estimated_work = len(data) * epochs * VOCAB_SIZE * embedding_dim
    if estimated_work > MAX_TRAINING_WORK:
        raise ValueError(f"estimated training work exceeds {MAX_TRAINING_WORK}-operation budget")

    rng = random.Random(seed)
    scale = 0.1
    embedding = [[rng.uniform(-scale, scale) for _ in range(embedding_dim)] for _ in range(VOCAB_SIZE)]
    weights = [[rng.uniform(-scale, scale) for _ in range(embedding_dim)] for _ in range(VOCAB_SIZE)]
    bias = [0.0] * VOCAB_SIZE
    sequence = [BOS, *data, EOS]

    for _ in range(epochs):
        for previous, target in zip(sequence, sequence[1:]):
            x = embedding[previous]
            logits = [bias[j] + sum(weights[j][k] * x[k] for k in range(embedding_dim)) for j in range(VOCAB_SIZE)]
            peak = max(logits)
            exps = [math.exp(max(-80.0, value - peak)) for value in logits]
            total = sum(exps)
            probs = [value / total for value in exps]
            probs[target] -= 1.0
            embedding_gradient = [sum(probs[j] * weights[j][k] for j in range(VOCAB_SIZE)) for k in range(embedding_dim)]
            for j, grad in enumerate(probs):
                bias[j] = max(-100.0, min(100.0, bias[j] - lr * grad))
                row = weights[j]
                for k in range(embedding_dim):
                    row[k] = max(-100.0, min(100.0, row[k] - lr * grad * x[k]))
            for k in range(embedding_dim):
                grad = max(-1.0, min(1.0, embedding_gradient[k]))
                embedding[previous][k] = max(-5.0, min(5.0, embedding[previous][k] - lr * grad))

    model = {
        "schema_version": SCHEMA_VERSION, "model_type": MODEL_TYPE, "vocab_size": VOCAB_SIZE,
        "embedding_dim": embedding_dim, "seed": seed, "training_bytes": len(data),
        "training_corpus_sha256": hashlib.sha256(data).hexdigest(), "epochs": epochs,
        "learning_rate": lr,
        "embedding": embedding, "weights": weights, "bias": bias,
    }
    _validate_model(model)
    return model


def _next_token_probabilities_validated(model: dict[str, Any], previous: int) -> list[float]:
    """Compute probabilities when the caller has already validated the model."""
    x = model["embedding"][previous]
    logits = [model["bias"][j] + sum(model["weights"][j][k] * x[k] for k in range(model["embedding_dim"])) for j in range(VOCAB_SIZE)]
    peak = max(logits)
    exps = [math.exp(max(-80.0, value - peak)) for value in logits]
    total = sum(exps)
    return [value / total for value in exps]


def next_token_probabilities(model: dict[str, Any], previous: int) -> list[float]:
    """Return the next-token distribution after validating the checkpoint."""
    _validate_model(model)
    if type(previous) is not int or not 0 <= previous < VOCAB_SIZE:
        raise ValueError("previous token is outside the vocabulary")
    return _next_token_probabilities_validated(model, previous)


def evaluate_text(model: dict[str, Any], text: str) -> dict[str, float | int]:
    _validate_model(model)
    if not isinstance(text, str):
        raise ValueError("evaluation text must be text")
    try:
        data = text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError("evaluation text contains invalid Unicode") from exc
    if not data:
        raise ValueError("evaluation text must not be empty")
    if len(data) > MAX_EVALUATION_BYTES:
        raise ValueError(f"evaluation data exceeds {MAX_EVALUATION_BYTES}-byte limit")
    sequence = [BOS, *data, EOS]
    loss = 0.0
    probabilities_by_previous: dict[int, list[float]] = {}
    for previous, target in zip(sequence, sequence[1:]):
        probabilities = probabilities_by_previous.get(previous)
        if probabilities is None:
            probabilities = _next_token_probabilities_validated(model, previous)
            probabilities_by_previous[previous] = probabilities
        loss -= math.log(max(probabilities[target], 1e-300))
    count = len(sequence) - 1
    mean_loss = loss / count
    return {"tokens": count, "mean_cross_entropy": mean_loss, "perplexity": math.exp(min(mean_loss, 700.0))}


def generate(model: dict[str, Any], prompt: str = "", max_bytes: int = 64) -> str:
    _validate_model(model)
    if type(max_bytes) is not int or not 0 <= max_bytes <= 4096:
        raise ValueError("max_bytes must be between 0 and 4096")
    try:
        prefix = prompt.encode("utf-8")
    except (AttributeError, UnicodeEncodeError) as exc:
        raise ValueError("prompt must be valid Unicode text") from exc
    previous = prefix[-1] if prefix else BOS
    output = bytearray()
    probabilities_by_previous: dict[int, list[float]] = {}
    for _ in range(max_bytes):
        probabilities = probabilities_by_previous.get(previous)
        if probabilities is None:
            probabilities = _next_token_probabilities_validated(model, previous)
            probabilities_by_previous[previous] = probabilities
        candidates = [*range(256), EOS]
        token = max(candidates, key=lambda idx: (probabilities[idx], -idx))
        if token == EOS:
            break
        output.append(token)
        previous = token
    return (prefix + output).decode("utf-8", errors="replace")


def save_checkpoint(model: dict[str, Any], path: str | Path) -> str:
    _validate_model(model)
    unsigned = dict(model)
    unsigned.pop("checkpoint_sha256", None)
    digest = _digest(unsigned)
    document = dict(unsigned, checkpoint_sha256=digest)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.write_bytes(_canonical(document))
    temporary.replace(destination)
    return digest


def load_checkpoint(path: str | Path) -> dict[str, Any]:
    try:
        raw = Path(path).read_bytes()
        if len(raw) > MAX_CHECKPOINT_BYTES:
            raise ValueError("checkpoint byte limit exceeded")
        text = raw.decode("utf-8")
        _check_json_nesting(text)
        document = json.loads(text, object_pairs_hook=_unique_json_object, parse_constant=_reject_json_constant)
    except ValueError as exc:
        if str(exc) == "checkpoint byte limit exceeded" or str(exc).startswith("duplicate checkpoint") or str(exc).startswith("non-standard JSON") or str(exc).startswith("checkpoint JSON nesting"):
            raise
        raise ValueError("unable to read checkpoint JSON") from exc
    except RecursionError as exc:
        raise ValueError("checkpoint JSON nesting exceeds parser limit") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("unable to read checkpoint JSON") from exc
    return _validate_model(document, require_hash=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    train = sub.add_parser("train")
    train.add_argument("input", type=Path)
    train.add_argument("checkpoint", type=Path)
    train.add_argument("--epochs", type=int, default=3)
    train.add_argument("--seed", type=int, default=7)
    train.add_argument("--learning-rate", type=float, default=0.05)
    train.add_argument("--embedding-dim", type=int, default=EMBED_DIM)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("checkpoint", type=Path)
    evaluate.add_argument("input", type=Path)
    sample = sub.add_parser("generate")
    sample.add_argument("checkpoint", type=Path)
    sample.add_argument("--prompt", default="")
    sample.add_argument("--max-bytes", type=int, default=64)
    args = parser.parse_args()
    if args.command == "train":
        model = train_text(args.input.read_text(encoding="utf-8"), epochs=args.epochs, seed=args.seed,
                           learning_rate=args.learning_rate, embedding_dim=args.embedding_dim)
        print(json.dumps({
            "status": "PASS", "model_type": MODEL_TYPE,
            "checkpoint_sha256": save_checkpoint(model, args.checkpoint),
            "training_corpus_sha256": model["training_corpus_sha256"],
            "training_bytes": model["training_bytes"], "epochs": model["epochs"],
            "seed": model["seed"], "learning_rate": model["learning_rate"],
            "embedding_dim": model["embedding_dim"], "schema_version": SCHEMA_VERSION,
        }, sort_keys=True))
    elif args.command == "evaluate":
        model = load_checkpoint(args.checkpoint)
        text = args.input.read_text(encoding="utf-8")
        result = evaluate_text(model, text)
        result.update({
            "status": "PASS", "model_type": MODEL_TYPE,
            "checkpoint_sha256": model["checkpoint_sha256"],
            "evaluation_corpus_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        })
        print(json.dumps(result, sort_keys=True))
    else:
        print(generate(load_checkpoint(args.checkpoint), args.prompt, args.max_bytes))


if __name__ == "__main__":
    main()
