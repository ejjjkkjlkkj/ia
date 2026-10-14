# Independent language implementations and NEXORA

## Required separation

Every entry in `LANGUAGE-CATALOG.md` has its own implementation track. Do not treat a catalogue row, a shared specification, or a common checkpoint as proof that a language implementation exists.

For each language, track these independently:
- **Model/runtime implementation**: tensor operations, tokenizer integration, layers, inference, training hooks and checkpoint read/write where the language/toolchain can support them.
- **Data and training pipeline**: data provenance, preprocessing, deterministic training/evaluation commands and resource limits appropriate to that language.
- **Conformance tests**: shared deterministic vectors, numeric tolerances, tokenizer fixtures, checkpoint round trips and generated-output regression tests.
- **Target support**: host/runtime requirements, architecture, memory and unsupported operations.
- **Release evidence**: toolchain versions, build/test logs, artifact hashes and measured performance.

The same mathematical model specification and tokenizer/checkpoint formats may be shared to allow interoperability, but source implementations remain language-specific. Each implementation must state whether it is native, a binding to another runtime, a wrapper, or only a reference prototype. Do not call a wrapper a native port. Do not claim an independently trained model unless its own training run, produced weights, logs, data provenance and held-out evaluation are recorded.

The accessibility repository's separate deliverables are also tracked independently per language: screen reader, UEFI/bare-metal and operating-system integration. A model/runtime implementation in this repository does not establish that any of those accessibility deliverables exists.

## NEXORA is a separate universal programming language

NEXORA is the experimental universal programming language in this project. It is **not** the same thing as the universal AI model, and it is not the existing language named U.

NEXORA must have its own grammar, lexer/parser, static type rules, deterministic intermediate representation (IR), reference interpreter, conformance tests and eventually separate compiler backends. Its IR can be an interoperability boundary between language-specific implementations, but it must not erase their semantics or make the other implementations dependent on the NEXORA runtime.

The following claims are distinct and must never be conflated:
1. **Universal AI model** — a model architecture, training process, weights and evaluation.
2. **Per-language model/runtime implementation** — language-specific code implementing or consuming the documented model operations.
3. **NEXORA language** — syntax, semantics, compiler/interpreter and backend project.
4. **Accessibility implementations** — per-language screen-reader, UEFI and OS tracks in the accessibility repository.

## Honest status gates

Use `PASS`, `FAIL`, `PARTIAL`, `BLOCKED` and `NOT_VALIDATED` per language and per deliverable. A passing shared test suite is necessary but does not prove every language backend is production-ready. Unsupported toolchains and unsuitable runtimes must be explicitly marked with reasons.

A model is not reported as trained until there are reproducible training logs, a checkpoint hash, a data/license manifest and held-out evaluation results. A NEXORA backend is not reported as implemented until it compiles and passes language-specific conformance tests. No cloud provider or API key is required for the local reference path.
