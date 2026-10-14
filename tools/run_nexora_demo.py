"""Run the checked-in NEXORA example with the Python standard library only."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexora_language import run  # noqa: E402

source_path = ROOT / "examples" / "hello.nex"
source = source_path.read_text(encoding="utf-8")
expected = [42, "NEXORA fonctionne"]
actual = run(source)

print("NEXORA INTERPRETER DEMO")
print(f"Source: {source_path.name}")
for value in actual:
    print(value)
if actual != expected:
    print(f"FAIL: expected {expected!r}, got {actual!r}", file=sys.stderr)
    raise SystemExit(1)
print("RESULT: PASS (prototype interpreter; not native compilation or UEFI readiness)")
