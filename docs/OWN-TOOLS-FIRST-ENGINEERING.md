# Own-tools-first engineering and evaluation protocol

## Decision rule

**Build our own tools. Use external projects only as observable comparison targets unless a specific dependency is explicitly approved.** Research may identify capabilities, standards, failure modes, and measurable expectations. It does not authorize copying implementations, model weights, datasets, prompts, source code, documentation, media, or proprietary designs.

## Allowed evaluation workflow

1. Define a project-owned requirement and a measurable acceptance criterion before inspecting a candidate.
2. Record the candidate name, official source, exact version/revision, date, environment, and applicable terms.
3. Test only what access terms and law permit. Prefer public APIs, official demos, published benchmarks, standards-conformance tests, and synthetic tasks authored by this project.
4. Keep inputs, test harnesses, scoring rules, and expected outputs project-authored wherever possible. Do not extract or retain protected outputs beyond what is necessary and permitted for evaluation.
5. Compare our implementation and the candidate on the same permitted test cases, environment, and resource limits. Record hardware, software versions, configuration, warm-up, repetitions, and variance.
6. Store factual observations, aggregate metrics, and reproducible test procedures—not copied implementation details or third-party content.
7. Implement our own design from requirements and independently reasoned specifications. Keep commits, design notes, and test provenance to document development history.
8. Do not import, vendor, fine-tune on, distill from, or redistribute a candidate's code, weights, datasets, prompts, or media unless a separate approval explicitly covers that exact asset and intended use.

## Comparison dimensions

Use only dimensions relevant to the tool under test:
- Functional coverage and correctness
- Robustness, edge cases, and failure recovery
- Latency distribution (median and p95), throughput, and resource use
- Accessibility and keyboard/screen-reader behavior, where applicable
- Offline/local operation, privacy, and network behavior
- Security, dependency exposure, and safe handling of untrusted input
- Multilingual and multimodal coverage, where applicable
- Reproducibility, portability, maintainability, and operational cost

A score is not evidence unless the test method, test set, environment, and raw result summary are recorded. Do not claim superiority from incomparable benchmarks.

## Status vocabulary

- `PLANNED`: no test run.
- `READY`: test and acceptance criteria reviewed.
- `RUN`: execution started but incomplete.
- `PASS`: all defined acceptance criteria passed with evidence.
- `FAIL`: at least one required criterion failed with evidence.
- `PARTIAL`: some criteria passed, others remain untested or failed.
- `BLOCKED`: access, environment, safety, or rights prevents a valid test.
- `NOT_VALIDATED`: evidence is absent or insufficient.

## Evidence and rights boundary

A public website, open repository, benchmark result, or downloadable artifact is not automatic permission to reuse its contents. Before importing any external asset, evaluate its exact revision, license/terms, attribution, training permissions, modification rights, and redistribution conditions in the provenance ledger. Evaluation status does not grant reuse rights.

## Project output

The deliverable is our own implementation, tests, specifications, benchmark harness, synthetic test cases, and documentation. External products are references for black-box comparison—not source material to clone. This protocol does not claim global novelty, patentability, or legal clearance.
