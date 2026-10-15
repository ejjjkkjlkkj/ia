"""Universal UTF-8 byte-level bigram baseline.

One checkpoint can ingest UTF-8 text from any natural language or programming
language without language-specific tokenization. This is a deliberately small
statistical baseline, not a neural model or a claim of semantic universality.
"""
from __future__ import annotations
import argparse, hashlib, json, math, re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
MODEL_TYPE = "universal-utf8-byte-bigram"
BOS, EOS, VOCAB_SIZE = 256, 257, 258

def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def train_text(text: str, alpha: float = 0.5) -> dict[str, Any]:
    """Train a smoothed byte-level model from mixed-language UTF-8 text."""
    if not math.isfinite(alpha) or alpha <= 0:
        raise ValueError("alpha must be a finite number greater than zero")
    data = text.encode("utf-8")
    if not data:
        raise ValueError("training text must contain at least one UTF-8 byte")
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
            "tokenization": "raw UTF-8 bytes; reserved BOS=256 EOS=257",
            "alpha": alpha, "vocab_size": VOCAB_SIZE, "counts": counts,
            "training_bytes": len(data), "training_corpus_sha256": _sha256(data)}

def _validate_payload(model: Any) -> None:
    """Validate every field and transition before a checkpoint is saved or used."""
    required = {
        "schema_version", "model_type", "tokenization", "alpha", "vocab_size",
        "counts", "training_bytes", "training_corpus_sha256",
    }
    if not isinstance(model, dict) or set(model) != required:
        raise ValueError("checkpoint fields do not match the model schema")
    if type(model["schema_version"]) is not int or model["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported checkpoint schema version")
    if model["model_type"] != MODEL_TYPE or model["vocab_size"] != VOCAB_SIZE:
        raise ValueError("unsupported universal model format")
    if model["tokenization"] != "raw UTF-8 bytes; reserved BOS=256 EOS=257":
        raise ValueError("unsupported tokenization contract")
    alpha = model["alpha"]
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not math.isfinite(alpha) or alpha <= 0:
        raise ValueError("alpha must be a finite positive number")
    training_bytes = model["training_bytes"]
    if type(training_bytes) is not int or training_bytes <= 0:
        raise ValueError("invalid training byte count")
    corpus_hash = model["training_corpus_sha256"]
    if not isinstance(corpus_hash, str) or re.fullmatch(r"[0-9a-f]{64}", corpus_hash) is None:
        raise ValueError("invalid training corpus SHA-256")
    counts = model["counts"]
    if not isinstance(counts, dict) or str(BOS) not in counts:
        raise ValueError("invalid transition counts")
    total = 0
    eos_count = 0
    for previous, row in counts.items():
        if not isinstance(previous, str) or not previous.isdecimal() or str(int(previous)) != previous:
            raise ValueError("invalid previous-byte key")
        previous_id = int(previous)
        if previous_id < 0 or previous_id > BOS:
            raise ValueError("previous-byte key is out of range")
        if not isinstance(row, dict) or not row:
            raise ValueError("transition rows must be non-empty objects")
        for token, count in row.items():
            if not isinstance(token, str) or not token.isdecimal() or str(int(token)) != token:
                raise ValueError("invalid next-byte key")
            token_id = int(token)
            if token_id < 0 or token_id > EOS:
                raise ValueError("next-byte key is out of range")
            if type(count) is not int or count <= 0:
                raise ValueError("transition counts must be positive integers")
            total += count
            if token_id == EOS:
                eos_count += count
    if total != training_bytes + 1 or eos_count != 1 or sum(counts[str(BOS)].values()) != 1:
        raise ValueError("transition counts do not match training byte totals")


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate checkpoint JSON key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError("non-standard checkpoint JSON numeric constant")


def save_checkpoint(model: dict[str, Any], path: str | Path) -> str:
    """Validate and write a hash-protected JSON checkpoint."""
    payload = dict(model)
    payload.pop("checkpoint_sha256", None)
    _validate_payload(payload)
    digest = _sha256(_canonical_json(payload))
    checkpoint = dict(payload, checkpoint_sha256=digest)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(checkpoint, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return digest


def load_checkpoint(path: str | Path) -> dict[str, Any]:
    """Load only supported, structurally valid, integrity-checked checkpoints."""
    try:
        checkpoint = json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_json_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("cannot read checkpoint JSON") from exc
    if not isinstance(checkpoint, dict):
        raise ValueError("unsupported or malformed checkpoint schema")
    supplied_hash = checkpoint.pop("checkpoint_sha256", None)
    if not isinstance(supplied_hash, str) or supplied_hash != _sha256(_canonical_json(checkpoint)):
        raise ValueError("checkpoint SHA-256 mismatch")
    _validate_payload(checkpoint)
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
