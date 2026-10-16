"""Universal UTF-8 byte-level bigram baseline.

One checkpoint can ingest UTF-8 text from any natural language or programming
language without language-specific tokenization. This is a deliberately small
statistical baseline, not a neural model or a claim of semantic universality.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
MODEL_TYPE = "universal-utf8-byte-bigram"
TOKENIZATION = "raw UTF-8 bytes; reserved BOS=256 EOS=257"
BOS, EOS, VOCAB_SIZE = 256, 257, 258
MAX_TRAINING_BYTES = 1_000_000
MAX_EVALUATION_BYTES = 100_000
MAX_PROMPT_BYTES = 100_000
MAX_GENERATION_BYTES = 4_096
MAX_CHECKPOINT_BYTES = 4_000_000
MAX_ALPHA = 100.0
MAX_JSON_DEPTH = 64

def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate checkpoint JSON key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _check_json_nesting(text: str, max_depth: int = MAX_JSON_DEPTH) -> None:
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
            if depth < 0:
                raise ValueError("malformed checkpoint JSON nesting")


def _validate_alpha(alpha: Any) -> float:
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)):
        raise ValueError("alpha must be a finite number greater than zero")
    try:
        value = float(alpha)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError("alpha must be a finite number greater than zero") from exc
    if not math.isfinite(value) or not 0 < value <= MAX_ALPHA:
        raise ValueError(f"alpha must be finite and in (0, {MAX_ALPHA}]")
    return value


def train_text(text: str, alpha: float = 0.5) -> dict[str, Any]:
    """Train a smoothed byte-level model from mixed-language UTF-8 text."""
    if not isinstance(text, str):
        raise ValueError("training text must be text")
    try:
        data = text.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise ValueError("training text contains invalid Unicode") from exc
    if not data:
        raise ValueError("training text must contain at least one UTF-8 byte")
    if len(data) > MAX_TRAINING_BYTES:
        raise ValueError(f"training data exceeds {MAX_TRAINING_BYTES}-byte limit")
    alpha = _validate_alpha(alpha)
    counts: dict[str, dict[str, int]] = {}
    previous = BOS
    for byte in data:
        row = counts.setdefault(str(previous), {})
        row[str(byte)] = row.get(str(byte), 0) + 1
        previous = byte
    row = counts.setdefault(str(previous), {})
    row[str(EOS)] = row.get(str(EOS), 0) + 1
    counts = {key: dict(sorted(row.items(), key=lambda item: int(item[0])))
              for key, row in sorted(counts.items(), key=lambda item: int(item[0]))}
    return {"schema_version": SCHEMA_VERSION, "model_type": MODEL_TYPE,
            "tokenization": TOKENIZATION,
            "alpha": alpha, "vocab_size": VOCAB_SIZE, "counts": counts,
            "training_bytes": len(data), "training_corpus_sha256": _sha256(data)}

def save_checkpoint(model: dict[str, Any], path: str | Path) -> str:
    """Write a hash-protected JSON checkpoint and return its SHA-256."""
    payload = dict(model)
    payload.pop("checkpoint_sha256", None)
    digest = _sha256(_canonical_json(payload))
    checkpoint = dict(payload, checkpoint_sha256=digest)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(checkpoint, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return digest

def load_checkpoint(path: str | Path) -> dict[str, Any]:
    """Load only supported, integrity-checked checkpoints."""
    checkpoint = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(checkpoint, dict) or checkpoint.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported or malformed checkpoint schema")
    supplied_hash = checkpoint.pop("checkpoint_sha256", None)
    if not isinstance(supplied_hash, str) or supplied_hash != _sha256(_canonical_json(checkpoint)):
        raise ValueError("checkpoint SHA-256 mismatch")
    if checkpoint.get("model_type") != MODEL_TYPE or checkpoint.get("vocab_size") != VOCAB_SIZE:
        raise ValueError("unsupported universal model format")
    if not isinstance(checkpoint.get("counts"), dict):
        raise ValueError("checkpoint is missing transition counts")
    checkpoint["checkpoint_sha256"] = supplied_hash
    return checkpoint

def next_byte_probability(model: dict[str, Any], previous: int, token: int) -> float:
    alpha = float(model["alpha"])
    row = model["counts"].get(str(previous), {})
    total = sum(int(value) for value in row.values())
    return (int(row.get(str(token), 0)) + alpha) / (total + alpha * VOCAB_SIZE)

def evaluate_text(model: dict[str, Any], text: str) -> dict[str, float | int]:
    data = text.encode("utf-8")
    if not data:
        raise ValueError("evaluation text must contain at least one UTF-8 byte")
    previous, nll = BOS, 0.0
    for token in list(data) + [EOS]:
        nll -= math.log(max(next_byte_probability(model, previous, token), 1e-300))
        previous = token
    count = len(data) + 1
    mean = nll / count
    return {"bytes_including_eos": count, "negative_log_likelihood": nll,
            "mean_negative_log_likelihood": mean, "perplexity": math.exp(min(mean, 700.0))}

def generate(model: dict[str, Any], prompt: str = "", max_bytes: int = 64) -> str:
    """Greedy byte generation; decoding replaces incomplete UTF-8 sequences."""
    if max_bytes < 0:
        raise ValueError("max_bytes must be non-negative")
    output = bytearray(prompt.encode("utf-8"))
    previous = output[-1] if output else BOS
    for _ in range(max_bytes):
        row = model["counts"].get(str(previous), {})
        if not row:
            break
        token = min((int(k) for k in row), key=lambda k: (-int(row[str(k)]), k))
        if token == EOS:
            break
        if not 0 <= token <= 255:
            raise ValueError("checkpoint contains a non-byte generation token")
        output.append(token)
        previous = token
    return bytes(output).decode("utf-8", errors="replace")

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Universal UTF-8 byte-level bigram baseline")
    commands = parser.add_subparsers(dest="command", required=True)
    train = commands.add_parser("train", help="train on a UTF-8 mixed-language corpus")
    train.add_argument("corpus", type=Path); train.add_argument("checkpoint", type=Path)
    train.add_argument("--alpha", type=float, default=0.5)
    evaluate = commands.add_parser("evaluate", help="evaluate on a separate held-out UTF-8 corpus")
    evaluate.add_argument("checkpoint", type=Path); evaluate.add_argument("corpus", type=Path)
    gen = commands.add_parser("generate", help="generate bytes from a universal checkpoint")
    gen.add_argument("checkpoint", type=Path); gen.add_argument("--prompt", default="")
    gen.add_argument("--max-bytes", type=int, default=64)
    args = parser.parse_args(argv)
    if args.command == "train":
        model = train_text(args.corpus.read_text(encoding="utf-8"), args.alpha)
        digest = save_checkpoint(model, args.checkpoint)
        result = {"status": "PASS", "model_type": MODEL_TYPE, "training_bytes": model["training_bytes"],
                  "checkpoint": str(args.checkpoint), "checkpoint_sha256": digest,
                  "claim_scope": "universal UTF-8 input coverage; statistical bigram only, not semantic universality"}
    elif args.command == "evaluate":
        result = {"status": "PASS", "model_type": MODEL_TYPE,
                  "evaluation": evaluate_text(load_checkpoint(args.checkpoint), args.corpus.read_text(encoding="utf-8"))}
    else:
        result = {"status": "PASS", "model_type": MODEL_TYPE,
                  "text": generate(load_checkpoint(args.checkpoint), args.prompt, args.max_bytes)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
