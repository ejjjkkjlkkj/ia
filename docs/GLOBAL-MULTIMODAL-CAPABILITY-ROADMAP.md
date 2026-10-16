# Global capability roadmap: code, text, files, images, audio, video and agents

## Objective

Build a common, auditable evaluation and integration layer for the project's intended capabilities. This is a work plan and registry, not a claim that one model already supports every modality. The canonical machine-readable list is `data/capability-matrix.json`.

## Capability coverage

- **Text:** multilingual input/output, generation, editing, translation, classification, summarization, question answering, factuality checks and Unicode edge cases.
- **Code:** A–Z language inventory, dialects, parsers, compilers/interpreters, code generation, debugging, refactoring, code review, tests, security, build systems and repository-level changes. Track each language separately; no catalog entry proves competence.
- **Files/documents:** text, Markdown, PDF, office formats, structured data, archives and source trees. Test malformed inputs, encoding, tables, metadata, large files, round-trip fidelity and hostile files. Never execute macros or embedded code during parsing.
- **Images:** image input, visual question answering, captioning, OCR-assisted workflows, charts, object detection, segmentation, editing and generation. OCR is a task/tool, not a substitute for visual reasoning or accessibility-tree data.
- **Audio:** speech recognition, speech synthesis, diarization, sound events, audio captioning, translation, music and noisy environments. Separate objective WER/CER metrics from human-rated speech quality.
- **Video:** frame sampling, temporal reasoning, scene changes, action recognition, timestamps, captions, subtitles and clip summaries. Record frame rate, sampling policy and audio handling.
- **Agents/tools:** planning, tool-schema validation, multi-step execution, repository inspection, patch creation, tests, retry/recovery, logging and human approval gates. Do not confuse an agent loop with an underlying model's skill.
- **Search/retrieval:** indexing, deduplication, ranking, source-grounded answers and citation checks.
- **Accessibility:** keyboard-first interaction, UI Automation/accessibility trees, focus order, screen-reader interoperability, captions, alt text and speech output.
- **Tables/data:** CSV, spreadsheets, SQL, schema validation, formulas, data quality, numerical correctness and privacy.
- **Math/science:** symbolic and numerical reasoning, unit-aware calculations, proofs checked by tools and reproducible computation.
- **3D/spatial:** meshes, point clouds, poses, geometry, trajectories and explicit safety constraints.
- **Cross-modal fusion:** mixed inputs and outputs, modality routing, grounding and consistency checks.
- **Safety/security:** prompt injection, secret leakage, dependency risk, sandbox policy, privacy and robust failure handling.

## Evidence states

Use the capability statuses in the JSON registry. A capability is not `TESTED` until an executable, reproducible test has run and its logs/results are retained. `IMPLEMENTED` means code exists; it does not imply quality. Use `BLOCKED` for an explicit missing dependency or hardware requirement and `NOT_VALIDATED` when evidence is insufficient.

## Dataset and model acquisition

1. Discover candidates using official model cards, source repositories and documented public APIs.
2. Record model/dataset revision, source URL, license, attribution, intended use, gated status and hardware requirements.
3. Review license and data provenance before downloading, redistributing, fine-tuning, distilling or publishing.
4. Keep large weights and corpora out of Git history unless redistribution is explicitly permitted and justified.
5. Verify hashes, file formats, schemas and provenance. Do not run model-provided code by default.
6. Run inference in a sandbox with resource limits; disable network after downloads where possible.
7. Store exact prompts/tasks, expected outputs, seeds, commands, logs, model hashes, runtime versions and raw scores.
8. Evaluate each modality separately and then evaluate cross-modal consistency. Do not average incompatible metrics into a misleading single score.
9. Compare against versioned baselines using held-out tasks and contamination checks.
10. Publish machine-readable reports as CI artifacts; do not auto-publish datasets or releases.

## GitHub Actions

The workflow `.github/workflows/capability-matrix-audit.yml` validates the registry and runs the repository's lightweight deterministic checks without API keys or large model downloads. Heavy model benchmarks should be opt-in, self-hosted or explicitly resource-bounded. Scheduled GitHub-hosted workflows are not a guaranteed 24/7 compute service and may be delayed or disabled by repository inactivity/policy.

## Initial deliverables and boundaries

- Machine-readable capability matrix with 14 top-level categories.
- Static validator for unique IDs, required fields, known statuses and nonempty task/metric definitions.
- CI workflow for push, pull request, manual dispatch and scheduled auditing.
- Artifact report containing the registry and validation summary.

Not yet claimed: all external datasets collected, licenses approved, models downloaded, fine-tuning completed, every modality implemented, or superiority over commercial models. Those require separate reproducible evidence.
