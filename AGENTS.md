# Autonomous Engineering Contract — IA/NEXORA

This file is the task contract for any coding agent operating in this repository. It does not itself start an agent or grant execution credentials.

## Mission
Drive the repository from the current state to a reproducible, tested release of the project's own local AI technology. Work in small, reviewable increments; do not stop after documentation-only changes when a concrete implementation or test is feasible.

## Required work loop
1. Inspect the current branch, working tree, open failures, tests, and latest CI evidence before editing.
2. Select the highest-impact, smallest independently verifiable blocker.
3. Implement the actual code, not a mock or a claim of future functionality.
4. Add regression tests and adversarial/negative tests for the changed behavior.
5. Run the narrow test first, then the relevant full suite, static checks, and reproducibility checks.
6. Record exact commands, exit codes, artifacts, limitations, and status in a concise report.
7. Repeat while the execution budget remains. Leave the next concrete task and blocker when the run must stop.

## Product and integration requirements
- Build the project's own model/runtime, tokenizer, weight/checkpoint contract, training and inference pipeline; do not relabel a third-party API wrapper as the project's own model.
- Keep training and inference local-capable; no mandatory cloud API key or network dependency at runtime.
- Keep the versioned integration contract synchronized with `ejjjkkjlkkj/accessibility`.
- Prove reproducibility with fixed seeds, pinned dependencies, known test vectors, deterministic serialization where applicable, and documented hardware/resource requirements.
- Clearly distinguish implemented, tested, benchmarked, and experimentally demonstrated capabilities.

## Release gates
- Required CI and tests pass on the release commit.
- Clean checkout can reproduce the documented build/test flow.
- Model format, tokenizer, inference, and integration contract have conformance tests.
- Security, data provenance, dependency, and license checks have explicit results.
- Release artifacts have hashes, version metadata, build logs, and rollback notes.
- Any unproven training scale, quality claim, benchmark, or cross-platform port is marked NOT_VALIDATED, never inferred from documentation.

## Permissions and integrity
- Work only in authorized repositories and branches.
- Do not expose secrets, weaken security checks to make CI green, fabricate test output, or silently skip failing tests.
- Do not force-push, delete branches, publish a release, or merge unreviewed changes automatically.
- Prefer a focused fix over broad rewrites. Preserve unrelated user work.
