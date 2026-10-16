# Open-model acquisition and capability expansion

## What is now automated

- `open-model-registry.json` tracks candidate publishers and discovery tasks.
- `../tools/discover_open_models.py` queries the public Hugging Face Hub metadata API across 18 task categories: language generation, image understanding/generation/editing, video, speech recognition/synthesis, audio, embeddings/ranking, document QA, depth, segmentation, and detection.
- `.github/workflows/discover-open-model-candidates.yml` runs weekly and on manual dispatch, then stores a JSON report as a 30-day GitHub Actions artifact.
- The discovery process does **not** download weights, access private models, accept licenses, or claim any model is superior.

## Acquisition stages

1. Discover candidates by task, architecture, language, size, license metadata, recency, and hardware requirements.
2. Inspect the exact model card, license text, gated status, training-data provenance, export restrictions, and intended use.
3. Record the immutable revision, repository URL, license text/hash, model config, weight hashes, and expected disk/RAM/VRAM.
4. Download only after license and storage checks; keep third-party weights outside Git history unless redistribution is explicitly permitted and needed.
5. Run integrity checks and isolated inference tests, with network disabled after acquisition where feasible.
6. Benchmark each candidate against the same versioned private/public test suites. Store raw outputs, scores, latency, memory, hardware, quantization, seeds, and commands.
7. Use a candidate as a teacher, specialist, or baseline only if its license and data provenance permit the intended use. Distillation is not automatically allowed by every license.
8. Train and validate our own checkpoint and runtime; record the complete lineage. A catalogue of downloaded models is not our own model.

## Capability coverage target

The end-to-end product should have a tested model/tool pipeline for:
- code generation, repository navigation, patching, unit tests, compilation, debugging, and safe command execution;
- language, reasoning, structured extraction, long-context retrieval, and multilingual tasks;
- image understanding, OCR, document and screenshot understanding, image generation/editing;
- audio transcription, speech synthesis, and audio understanding;
- video understanding and generation where feasible;
- embeddings, semantic search, reranking, retrieval-augmented generation, and citations;
- tool calling, planning, persistent project state, evaluation, sandboxing, and local packaging.

These are target capabilities, not claims that all are implemented today. Use modular specialist models where appropriate, but keep a unified local orchestrator and common evaluation harness. Do not assume a single enormous checkpoint is best at every task.

## Hardware reality

The user's current workstation cannot hold every large open-weight model simultaneously. The acquisition plan must record file size and estimated RAM/VRAM before download, support one-model-at-a-time evaluation, quantization where legal and technically valid, resumable downloads, checksums, and explicit disk-space limits. Do not automatically download multi-hundred-gigabyte or multi-terabyte weights.

## Success criteria for surpassing other models

A claim of superiority must be scoped by task and backed by independent reproducible evidence. Compare our checkpoint to fixed versions of Claude (only with authorized access), Qwen, Llama, and other relevant open-weight candidates using identical prompts, task sets, scoring rules, token/tool budgets, and comparable hardware where possible. Report every category separately and publish regressions as well as wins. Downloads, parameter count, and benchmark claims from model vendors alone do not prove superiority.

## License vocabulary

- **Open source**: use only when the exact artifact and license support that claim.
- **Open weights**: weights are available; this does not by itself guarantee open training data, unrestricted use, or redistribution rights.
- **Candidate / license unverified**: discovered metadata only; not yet approved for use.
