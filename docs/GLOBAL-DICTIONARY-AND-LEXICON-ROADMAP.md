# Global dictionary, lexicon, and language-resource inventory

## Objective

Build an auditable, extensible inventory for **all resource families**, not just prose dictionaries or the A–Z programming-language list. No finite list can honestly promise every dictionary in existence. The system must continuously discover resources, record provenance, and report gaps without conflating discovery with import, licensing, or quality validation.

## Resource families

1. **Lexical dictionaries:** headwords, definitions, parts of speech, examples, inflections, pronunciation, etymology, usage labels.
2. **Translation dictionaries:** language pairs, direction, senses, regional variants, source language codes, confidence and provenance.
3. **Semantic dictionaries:** synonyms, antonyms, hypernyms, hyponyms, semantic frames and word senses.
4. **Morphology:** lemmas, inflected forms, paradigms, grammatical features, segmentation and derivation.
5. **Pronunciation and speech:** IPA, phoneme inventories, syllabification, stress, audio metadata and licenses. Do not assume a text dictionary grants rights to audio.
6. **Grammar and usage:** syntax, conjugation, declension, agreement, punctuation, style and regional usage.
7. **Multilingual and locale data:** language/script/region tags, transliteration, collation, plural rules, dates, numbers and Unicode normalization.
8. **Terminology and specialist lexicons:** science, medicine, law, engineering, computing, accessibility and domain-specific terms. Sensitive or regulated datasets require separate review.
9. **Historical, dialectal and endangered-language resources:** archived forms, dialects, historical spelling, alternate scripts and documented language variants.
10. **Programming-language catalogs:** language name and aliases, paradigms, dialects, specification, compiler/interpreter, versions, license, platforms, package ecosystem, file extensions, grammar, examples and conformance tests.
11. **Code vocabulary and API dictionaries:** keywords, built-ins, standard-library symbols, diagnostics, API signatures, documentation versions and deprecations.
12. **NEXORA:** project keywords, grammar, operators, types, standard library, diagnostics, examples, and compiler/interpreter conformance. NEXORA is not to be marked complete until the implementation and specification agree.
13. **Evaluation corpora:** licensed or synthetic language understanding, translation, morphology, code generation, compilation, runtime, security and regression tasks.

## Required record schema

Every resource must have a stable ID, official name, aliases, resource family, language/script/locale coverage, source URL, source revision/date, license and attribution requirements, redistribution restrictions, format, checksum, parser/importer version, provenance, status, known gaps, and validation report. Store language identifiers using BCP 47 where applicable and record source-specific IDs as well.

Statuses are independent:
- `DISCOVERED`: source found; no rights or technical validation implied.
- `LICENSE_REVIEW`: licensing/attribution review required.
- `READY_FOR_IMPORT`: license, format, provenance and import policy checked.
- `IMPORTED`: data ingested with manifest and checksum.
- `TESTED`: schema, integrity and sample-level tests passed.
- `BLOCKED`: explicit dependency, rights or access issue.
- `NOT_VALIDATED`: insufficient evidence.

Never use `PASS` for a dictionary simply because a URL exists or a download succeeds.

## Discovery and import pipeline

1. Search primary project pages, official data releases, recognized open-data catalogs, scholarly repositories and source repositories.
2. Prefer official dumps/APIs over scraping rendered web pages.
3. Store a manifest, not a blind copy of every dataset. Download only after checking license, attribution, privacy, redistribution and size.
4. Keep each language and dataset release independently versioned; do not infer uniform coverage or licensing across a collection.
5. Validate checksums, schema, encoding, Unicode normalization, duplicate IDs, malformed records, language tags, empty definitions and broken cross-references.
6. Build deduplicated indices while preserving source-specific IDs, citations, alternate spellings and provenance. Do not merge homonyms or senses solely by spelling.
7. Keep train/validation/test splits separate and prevent near-duplicate leakage. Never train on data whose rights are unresolved.
8. Produce per-family and per-language coverage reports, including unsupported languages and missing fields.
9. For programming languages, validate a syntax sample and compiler/interpreter availability separately from the lexical catalog. A catalog entry is not evidence that the IA can write correct code.
10. For NEXORA, generate keyword/builtin dictionaries from the canonical specification when possible and test them against lexer/parser behavior.
11. Re-run on schedule and when the manifest, parser, catalog, or relevant source revision changes.
12. Publish reports as workflow artifacts. Do not commit large corpora, secrets, private data, or unlicensed dumps.

## Seed sources to investigate

The machine-readable seed registry is `data/dictionary-sources.json`. It contains starting points only; each resource needs its own license, coverage and format review. Add further official and community-maintained dictionaries, domain lexicons, language-specific corpora, and compiler catalogs as discovered.

## CI acceptance criteria

- Manifest parses and conforms to the required schema.
- Resource IDs are unique; URLs are HTTPS; statuses are recognized.
- Every entry has a domain, coverage statement, license-review state, status and import policy.
- No entry is labeled imported/tested without a corresponding artifact, checksum and validation report.
- A source outage is reported distinctly from invalid metadata.
- Scheduled discovery and manual runs work without any paid API key.
- CI is allowed to create reports/artifacts; it must not silently merge PRs, publish datasets, or change repository settings.
- Hosted GitHub Actions is not unlimited or guaranteed to run at exact times. Scheduled workflows may be delayed or disabled by repository policy/inactivity; verify actual run history.

## Initial evidence boundaries

The seed registry is a discovery backlog, not proof of complete global coverage. License review, downloads, parsing, per-language quality evaluation, and model training remain separate gates.
