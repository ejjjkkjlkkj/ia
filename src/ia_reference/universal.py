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
BOS, EOS, VOCAB_SIZE = 256, 257, 258
MAX_CHECKPOINT_BYTES = 8_000_000
MAX_JSON_DEPTH = 64
MAX_TRAINING_BYTES = 100_000
MAX_EVALUATION_BYTES = 100_000
MAX_GENERATION_BYTES = 4_096

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

def _validate_checkpoint_payload(checkpoint: Any) -> dict[str, Any]:
    required = {
        "schema_version", "model_type", "tokenization", "alpha", "vocab_size",
        "counts", "training_bytes", "training_corpus_sha256",
    }
    if not isinstance(checkpoint, dict) or set(checkpoint) != required:
        raise ValueError("checkpoint has invalid fields")
    if type(checkpoint["schema_version"]) is not int or checkpoint["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported or malformed checkpoint schema")
    if checkpoint["model_type"] != MODEL_TYPE or checkpoint["vocab_size"] != VOCAB_SIZE:
        raise ValueError("unsupported universal model format")
    if checkpoint["tokenization"] != "raw UTF-8 bytes; reserved BOS=256 EOS=257":
        raise ValueError("unsupported tokenization format")
    alpha = checkpoint["alpha"]
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not math.isfinite(alpha) or alpha <= 0:
        raise ValueError("checkpoint alpha must be finite and greater than zero")
    training_bytes = checkpoint["training_bytes"]
    if type(training_bytes) is not int or training_bytes < 1:
        raise ValueError("checkpoint training_bytes must be a positive integer")
    corpus_hash = checkpoint["training_corpus_sha256"]
    if not isinstance(corpus_hash, str) or len(corpus_hash) != 64 or any(c not in "0123456789abcdef" for c in corpus_hash):
        raise ValueError("checkpoint corpus SHA-256 is malformed")
    counts = checkpoint["counts"]
    if not isinstance(counts, dict) or not counts or len(counts) > 257:
        raise ValueError("checkpoint transition counts are malformed")
    observed_total = 0
    for previous, row in counts.items():
        if not isinstance(previous, str) or not previous.isdigit() or not 0 <= int(previous) <= BOS:
            raise ValueError("checkpoint has an invalid previous-token ID")
        if not isinstance(row, dict) or not row or len(row) > VOCAB_SIZE:
            raise ValueError("checkpoint has an invalid transition row")
        for token, count in row.items():
            if not isinstance(token, str) or not token.isdigit() or not 0 <= int(token) < VOCAB_SIZE:
                raise ValueError("checkpoint has an invalid next-token ID")
            if type(count) is not int or count <= 0:
                raise ValueError("checkpoint transition counts must be positive integers")
            observed_total += count
    if observed_total != training_bytes + 1:
        raise ValueError("checkpoint transition counts do not match training_bytes")
    eos_transitions = sum(row.get(str(EOS), 0) for row in counts.values())
    if counts.get(str(BOS), {}).get(str(EOS), 0) or eos_transitions != 1:
        raise ValueError("checkpoint must contain exactly one valid EOS transition")
    return checkpoint

def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def train_text(text: str, alpha: float = 0.5) -> dict[str, Any]:
    """Train a smoothed byte-level model from bounded mixed-language UTF-8 text."""
    if not isinstance(text, str):
        raise ValueError("training text must be text")
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not math.isfinite(alpha) or alpha <= 0:
        raise ValueError("alpha must be a finite number greater than zero")
    try:
        data = text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError("training text contains invalid Unicode") from exc
    if not data:
        raise ValueError("training text must contain at least one UTF-8 byte")
    if len(data) > MAX_TRAINING_BYTES:
        raise ValueError(f"training data exceeds {MAX_TRAINING_BYTES}-byte limit")
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
    """Load only bounded, supported, integrity-checked checkpoints."""
    source = Path(path)
    if source.stat().st_size > MAX_CHECKPOINT_BYTES:
        raise ValueError(f"checkpoint exceeds {MAX_CHECKPOINT_BYTES}-byte limit")
    raw = source.read_text(encoding="utf-8")
    _check_json_nesting(raw)
    checkpoint = json.loads(
        raw,
        object_pairs_hook=_unique_json_object,
        parse_constant=_reject_json_constant,
    )
    if not isinstance(checkpoint, dict):
        raise ValueError("unsupported or malformed checkpoint schema")
    supplied_hash = checkpoint.pop("checkpoint_sha256", None)
    if not isinstance(supplied_hash, str) or len(supplied_hash) != 64 or any(c not in "0123456789abcdef" for c in supplied_hash):
        raise ValueError("checkpoint SHA-256 is malformed")
    if supplied_hash != _sha256(_canonical_json(checkpoint)):
        raise ValueError("checkpoint SHA-256 mismatch")
    _validate_checkpoint_payload(checkpoint)
    checkpoint["checkpoint_sha256"] = supplied_hash
    return checkpoint

def next_byte_probability(model: dict[str, Any], previous: int, token: int) -> float:
    alpha = float(model["alpha"])
    row = model["counts"].get(str(previous), {})
    total = sum(int(value) for value in row.values())
    return (int(row.get(str(token), 0)) + alpha) / (total + alpha * VOCAB_SIZE)

def evaluate_text(model: dict[str, Any], text: str) -> dict[str, float | int]:
    if not isinstance(model, dict):
        raise ValueError("model must be a checkpoint object")
    _validate_checkpoint_payload({key: value for key, value in model.items() if key != "checkpoint_sha256"})
    if not isinstance(text, str):
        raise ValueError("evaluation text must be text")
    try:
        data = text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError("evaluation text contains invalid Unicode") from exc
    if not data:
        raise ValueError("evaluation text must contain at least one UTF-8 byte")
    if len(data) > MAX_EVALUATION_BYTES:
        raise ValueError(f"evaluation data exceeds {MAX_EVALUATION_BYTES}-byte limit")
    previous, nll = BOS, 0.0
    for token in list(data) + [EOS]:
        nll -= math.log(max(next_byte_probability(model, previous, token), 1e-300))
        previous = token
    count = len(data) + 1
    mean = nll / count
    return {"bytes_including_eos": count, "negative_log_likelihood": nll,
            "mean_negative_log_likelihood": mean, "perplexity": math.exp(min(mean, 700.0))}

def generate(model: dict[str, Any], prompt: str = "", max_bytes: int = 64) -> str:
    """Greedy byte generation with bounded output; incomplete UTF-8 is replaced."""
    if not isinstance(model, dict):
        raise ValueError("model must be a checkpoint object")
    _validate_checkpoint_payload({key: value for key, value in model.items() if key != "checkpoint_sha256"})
    if not isinstance(prompt, str):
        raise ValueError("prompt must be text")
    if type(max_bytes) is not int or not 0 <= max_bytes <= MAX_GENERATION_BYTES:
        raise ValueError(f"max_bytes must be between 0 and {MAX_GENERATION_BYTES}")
    try:
        prompt_bytes = prompt.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError("prompt contains invalid Unicode") from exc
    if len(prompt_bytes) > MAX_EVALUATION_BYTES:
        raise ValueError(f"prompt exceeds {MAX_EVALUATION_BYTES}-byte limit")
    output = bytearray(prompt_bytes)
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
