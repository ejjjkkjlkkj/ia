# IA — local, multi-language AI engineering

Repository goal: build a local-first AI development system with a language-specific engineering track for every language catalogued by `ejjjkkjlkkj/accessibility`. This repository starts as an architecture and execution contract; it does not claim that models have already been trained.

## Principles

- Local-first inference; no mandatory cloud provider or API key.
- Reuse the same stable language IDs as the accessibility repository.
- Prefer one capable local base model plus per-language parsers, compiler/toolchain integrations, retrieval indexes, test suites, prompts and optional adapters.
- A dedicated foundation model per programming language is an experiment, not an assumption. Training from scratch requires licensed data, compute, reproducibility and held-out benchmark evidence.
- Do not commit model weights, secrets, API keys, private source code or unlicensed corpora.
- Every capability needs tests and an evidence record. A directory or config file is not proof of a working model.

## Language catalog

See [LANGUAGE-CATALOG.md](LANGUAGE-CATALOG.md). It covers primary systems languages, feasibility candidates and hosted/platform-specific languages. The same IDs must be used in the accessibility repository.

## Architecture

1. **Local inference gateway** — adapter for local runtimes such as Ollama; provider-independent internal API.
2. **Language registry** — stable ID, extensions, compiler, parser, target platforms, capabilities and blockers.
3. **Per-language toolchain adapter** — compile/check/test/format/lint commands; sandboxed execution and structured diagnostics.
4. **Source understanding** — parser/AST where available, symbol index, repository retrieval and dependency/license metadata.
5. **Code agent** — plan, inspect, patch, run approved tests, report evidence; no unapproved destructive actions, publishing or merging.
6. **Evaluation harness** — syntax/compile tests, unit tests, task benchmarks, regression suites, security tests and cross-language parity.
7. **Optional model specialization** — adapters or fine-tunes only with documented dataset provenance, license, compute, benchmark and rollback.
8. **Accessibility integration** — share semantic event contracts, UEFI/kernel release evidence and test vectors with `ejjjkkjlkkj/accessibility`.

## Status vocabulary

- `PASS`: reproducible command, environment, test result and artifact/hash are recorded.
- `PARTIAL`: implementation exists but acceptance criteria remain.
- `BLOCKED`: a concrete toolchain/runtime/data/compute limitation is recorded.
- `NOT_VALIDATED`: no adequate evidence yet.
- `NOT_IMPLEMENTED`: no implementation yet.

## Initial milestones

1. Establish the registry and language parity with accessibility.
2. Add local inference gateway contract and health tests.
3. Add one toolchain adapter at a time, starting with C, C++, Rust, Go, Python, Zig and D.
4. Build an evaluation corpus from licensed or synthetic tasks with train/test separation.
5. Add retrieval and language-aware diagnostics before attempting fine-tuning.
6. Measure each adapter/model separately and publish evidence; do not invent results.

## Safety and release policy

Run generated code in isolated sandboxes with time, memory and filesystem limits. Require explicit approval for destructive file operations, firmware/NVRAM changes, physical reboot, release, merge, or publication. Never represent QEMU/emulator success as physical hardware validation.
