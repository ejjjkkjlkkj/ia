# Project completion and release gates

## Mission

Deliver a reproducible, usable AI system whose required inference/runtime path is owned by this project. Keep working iteratively until every release gate is either evidenced as PASS or explicitly documented as BLOCKED with the exact external dependency and remediation. Do not declare completion while a required gate is unresolved.

## Autonomous work loop

For each iteration:
1. Inspect the current branch, open issues, TODO/FIXME markers, tests, build scripts, and latest CI evidence.
2. Select the highest-impact, smallest independently verifiable task.
3. Implement the change and add or update regression tests.
4. Run the narrow test first, then the full relevant test suite, formatters, linters, and static checks available in the repository.
5. Fix regressions without deleting, skipping, weakening, or falsifying tests.
6. Review the diff for accidental files, secrets, nondeterminism, license problems, and unsafe defaults.
7. Commit focused changes on the working branch and record exact commands, exit codes, and results.
8. Repeat while actionable work remains. Never report a test as passing unless it actually ran successfully.

If a tool, credential, hardware device, model artifact, or permission is unavailable, mark that item BLOCKED and continue with independent work. Do not fabricate results.

## Engineering priorities

1. Reproducible build, deterministic behavior, parser and input validation, numerical correctness.
2. Unit and integration tests for inference, tokenization, model/checkpoint loading, serialization, error handling, and resource limits.
3. Explicit model/artifact formats, versioning, integrity checks, provenance, and compatibility tests.
4. Local-first inference and training workflows; no mandatory hosted inference/API dependency in the final user runtime unless explicitly approved.
5. Accessibility, clear diagnostics, offline installation, resource profiling, and recovery from corrupted/incomplete artifacts.
6. Documentation that matches the implementation and gives exact reproducible commands.

## Final deliverables

- Source code, tests, build scripts, dependency/license inventory, threat model, and reproducible build instructions.
- A release artifact with SHA-256, version, source commit, build environment, and test report.
- A clean-install test on a separate directory or clean machine/environment.
- Model quality claims backed by named datasets, fixed evaluation procedures, metrics, and saved reports. Never claim training or quality improvements without artifacts and evidence.
- An offline smoke test proving that the required runtime path works without a network connection.

## Release gates

A release is READY only when all applicable gates pass:
- [ ] Clean checkout builds reproducibly.
- [ ] All required tests pass; failures and skipped tests are explained.
- [ ] Static analysis, formatting, dependency/license and secret scans are reviewed.
- [ ] Runtime inference works offline with documented model artifacts.
- [ ] Corrupt, missing, incompatible, and oversized inputs fail safely.
- [ ] Install, upgrade, rollback/recovery, and uninstall procedures are tested where applicable.
- [ ] Documentation, versioning, checksums, release notes, and known limitations are complete.
- [ ] No credentials, private data, generated junk, or unreviewed binaries are committed.
- [ ] Release artifact and test evidence are attached to the release candidate.

## Operating-system independence boundary

Development may use an existing host OS and CI to build and test. That is not proof of runtime independence. If the final product is required to run without Windows or Linux, build and validate a separately bootable project-owned runtime/OS and document every remaining firmware, hardware, compiler, and third-party dependency. Do not describe an AI application as an OS or as bare-metal merely because it has a local executable.

## Safety and change control

Use only owned or explicitly authorized test targets. No secret exfiltration, persistence, stealth, destructive actions, or unauthorized access. Do not change repository permissions, publish a release, or merge to the default branch without explicit authorization. Prefer small, reviewable commits and preserve failing tests as evidence.

## Evidence labels

- PASS: command or test executed successfully; include exact command and result.
- FAIL: executed and failed; include the failure.
- PARTIAL: some acceptance criteria passed.
- BLOCKED: could not execute due to a concrete missing prerequisite.
- NOT_VALIDATED: assertion has no direct test evidence yet.
