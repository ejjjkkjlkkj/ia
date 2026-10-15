# Autonomous engineering queue — IA / NEXORA

This task file is the persistent work queue for the local Ollama agent team. Work only on the current dedicated feature branch. Each iteration must inspect the relevant implementation and tests, select one small, high-value item, implement it, add regression coverage, run the repository's real test suite, and report evidence through the JSONL log. The runner publishes only test-passing commits to this feature branch; it never merges or releases.

## Priority order

1. **Correctness and bounded inputs:** NEXORA lexer/parser/IR; malformed input, nesting/recursion limits, Unicode, escaped strings, deterministic serialization, clear error behavior.
2. **Regression and property coverage:** boundary cases, parser fuzz-like generated fixtures, round-trip invariants, reference-model correctness, stable reproducibility.
3. **Reference implementation quality:** inspect `src/ia_reference/`; fix concrete bugs and document exact limits rather than claiming unimplemented training/inference.
4. **Catalogue integrity:** verify every model track has truthful scope, implementation status, reproducible commands, and links that resolve. Do not create fake model implementations merely to fill a catalogue.
5. **Build/release readiness:** identify missing tests, packaging metadata, CI gaps, and reproducibility evidence; make incremental testable fixes.

## Specialist roles

- IMPLEMENTER: one correctness fix or a small missing feature.
- TEST_ENGINEER: regression/boundary/property tests; do not weaken tests to get green CI.
- ACCESSIBILITY_REVIEWER: keyboard/screen-reader behavior where this repository exposes user-facing behavior; otherwise document applicability.
- SECURITY_RED_TEAM: local-only defensive tests using synthetic inputs; no external targets, credential access, exploit deployment, or destructive actions.
- INDEPENDENT_REVIEWER: check assumptions, scope, determinism, resource limits, evidence, and changed-file diff.

## Hard gates

Never modify `.github/workflows/`, `AGENTS.md`, this queue, secrets/configuration, release artifacts, or the agent runner. No network access added to runtime, credential collection, persistence, destructive actions, firmware/NVRAM/partition operations, or arbitrary command execution. Do not claim a test passed unless its exit code is zero. Do not claim model training or inference works without executable evidence. If no safe, testable improvement is apparent, return exactly `NO_PATCH`.
