# Original intellectual property policy

## Non-negotiable objective

Build the IA project as **original project-owned intellectual property**. Do not copy protected code, model weights, dataset contents, documentation, media, or substantial expressive material from external sources unless the exact rights and required approvals are documented.

This policy applies to dictionaries, programming-language catalogs, model and dataset discovery, code, text, images, audio, video, agents, benchmarks, documentation, and training pipelines.

## How web research may be used

- Use the web to discover facts, public technical specifications, standards, API contracts, license terms, and independently verifiable requirements.
- Prefer official documentation and source-of-truth registries.
- Record source links and factual notes; write our own explanations, implementation, tests, architecture, and wording.
- Reimplement an idea or behavior independently where lawful; do not reproduce protected expression, code structure, proprietary content, or confidential information.
- Do not assume that publicly reachable means free to copy, train on, modify, redistribute, or commercialize.
- Do not bypass authentication, access controls, rate limits, or rights reservations.
- Do not remove attribution, copyright notices, watermarks, or provenance.

## Four separate decisions

Every discovered asset must be evaluated separately for:

1. **Read/inspect:** Is access permitted by the site's terms and applicable law?
2. **Use/integrate:** Does the license or permission allow the intended use, including commercial use if relevant?
3. **Modify/train:** Are derivative works, model training, fine-tuning, distillation, and text/data mining allowed for this exact artifact and use?
4. **Redistribute/release:** May we ship the asset or a derivative, and what attribution, source disclosure, share-alike, notice, patent, or other conditions apply?

Approval for one decision does not automatically approve the others.

## Required provenance before import

Record each asset in `data/ip-provenance-ledger.json` using the full required fields in that schema. Unknown rights are not presumed clear. Set status to `LICENSE_REVIEW_REQUIRED`, `PERMISSION_REQUIRED`, or `NOT_VALIDATED` until evidence supports approval.

**Import gate:** do not place unreviewed third-party content, weights, corpora, or source code in project-owned datasets, training runs, releases, or vendored dependencies.

**Release gate:** review the complete dependency tree, licenses, notices, SBOM, redistribution conditions, model/dataset terms, and attribution. Keep evidence in the repository.

## Prefer original assets

Default work items should be project-created:
- Original code and tests, with dated commits and reviewable development history.
- Original language specification, grammar, compiler/runtime, diagnostics, and built-ins.
- Original model architectures and training/evaluation pipelines, where technically feasible.
- Original benchmark tasks and expected outputs, or assets whose exact reuse rights have been verified.
- Original documentation, diagrams, UI, media, and naming.
- Synthetic data generated from project-authored specifications, with provenance and contamination checks.

“Original” is not a claim that an idea is globally novel or patentable. Search prior art and trademarks separately before making those claims.

## Legal basis and useful official references

- The French INPI explains that copyright protects original expression, including software, rather than ideas or concepts: [INPI — Copyright](https://www.inpi.fr/ressources/propriete-intellectuelle/droit-dauteur).
- The EU Software Directive protects a computer program's expression while excluding underlying ideas and principles from copyright protection: [Directive 2009/24/EC](https://eur-lex.europa.eu/eli/dir/2009/24/oj/eng).
- The EUIPO explains copyright issues for generative AI, text and data mining, and machine-readable rights reservations: [EUIPO — Copyright and GenAI](https://www.euipo.europa.eu/en/copyright-knowledge-centre/copyright-and-genai).
- EU database rights may protect database contents or structure under applicable conditions: [Your Europe — Database protection](https://europa.eu/youreurope/business/growing/protecting-intellectual-property/database-protection/).

These sources are general guidance, not an asset-specific legal clearance. Consult qualified counsel for high-risk commercial releases, disputed rights, patent questions, or uncertain training-data legality.

## Validation states

- `ORIGINAL_PROJECT_CREATED`: created by this project with traceable development records.
- `PUBLIC_DOMAIN_VERIFIED`: public-domain status documented for the specific asset and jurisdiction.
- `LICENSE_APPROVED`: exact license and intended use reviewed and approved.
- `PERMISSION_REQUIRED`: written permission or a commercial license is needed.
- `LICENSE_REVIEW_REQUIRED`: evidence is incomplete.
- `REJECTED`: use is not approved.
- `NOT_VALIDATED`: no adequate evidence yet.

A registry entry is not legal proof by itself. Automated checks can detect missing records, but cannot replace substantive legal review.
