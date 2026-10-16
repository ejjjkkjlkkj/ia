# Global web resource map

## Purpose

This map seeds a repeatable, source-grounded discovery process for the `ia` repository. It covers lexical resources, programming languages and source code, open models and datasets, scientific metadata, images, audio, video, knowledge graphs, and software supply-chain security.

The machine-readable source registry is `data/global-web-resource-map.json`. It is a discovery index, **not** a claim that all listed resources have been downloaded, imported, validated, or approved for redistribution.

## Web map by resource family

| Family | Primary discovery sources | What to collect | Important boundary |
|---|---|---|---|
| Dictionaries and lexicons | [Kaikki](https://kaikki.org/), [WordNet](https://wordnet.princeton.edu/), [Open Multilingual Wordnet](https://omwn.org/), [Wikidata Lexemes](https://www.wikidata.org/wiki/Wikidata:Lexicographical_data), [UniMorph](https://unimorph.github.io/) | Definitions, senses, translations, pronunciation, morphology, semantic relations | Language coverage and license can vary by sub-resource. |
| Unicode and locale | [Unicode UCD](https://www.unicode.org/ucd/), [Unicode CLDR](https://cldr.unicode.org/) | Character properties, normalization, script data, locale formats and language tags | Pin versions; this is language infrastructure, not a general dictionary. |
| Programming languages and code | [GitHub REST API](https://docs.github.com/en/rest), [GitHub Linguist](https://github.com/github-linguist/linguist), [Repology](https://repology.org/), [Libraries.io](https://libraries.io/) | Language definitions, compilers, interpreters, packages, tests, libraries and agents | A search result or language detector is not proof of complete language coverage or executable correctness. |
| Models and datasets | [Hugging Face Hub API](https://huggingface.co/docs/hub/api), [PyTorch](https://pytorch.org/), [ONNX](https://onnx.ai/), [Papers with Code](https://paperswithcode.com/) | Model cards, dataset cards, revisions, tasks, runtime requirements and evaluation suites | Inspect the exact artifact's license, gated status, provenance, and remote-code risks. |
| Research and publications | [OpenAlex API](https://help.openalex.org/api/), [Crossref API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/), [arXiv API](https://info.arxiv.org/help/api/index.html) | Papers, DOI metadata, authors, institutions, topics and related code/data | Metadata access does not grant rights to reuse full-text papers or linked datasets. |
| Images, audio and video | [Wikimedia Commons](https://commons.wikimedia.org/wiki/Main_Page), [Open Images](https://storage.googleapis.com/openimages/web/index.html), [Common Voice](https://commonvoice.mozilla.org/), [OpenSLR](https://www.openslr.org/), [Freesound](https://freesound.org/) | Media assets, captions, labels, transcripts, locale coverage and provenance | Review license and privacy/consent conditions per corpus or file. |
| Knowledge graphs | [Wikidata Query Service](https://query.wikidata.org/), [DBpedia](https://www.dbpedia.org/), [Schema.org](https://schema.org/) | Canonical entity IDs, relations, ontology terms and structured web metadata | Respect query limits and preserve source identifiers and attribution. |
| Security and licensing metadata | [OSV](https://osv.dev/), [CVE](https://www.cve.org/), [SPDX](https://spdx.dev/), [GitHub license API](https://docs.github.com/en/rest/licenses/licenses) | Vulnerabilities, SPDX identifiers, SBOM metadata and repository license signals | Automated license detection is incomplete and is not legal advice. |

## Harvesting workflow

1. **Discover** candidates from official APIs, maintained project registries, source repositories, and documented data portals.
2. **Normalize** canonical IDs, URLs, language tags, package coordinates, model/dataset IDs, and revision identifiers.
3. **Deduplicate** by stable source ID first; use normalized URLs and content checksums as secondary keys.
4. **Capture provenance**: retrieval timestamp, source revision, endpoint, license URL/expression, attribution, gated status, artifact size, checksum, and parser version.
5. **Review rights and safety** before downloading, redistributing, training, fine-tuning, or executing code. A public endpoint is not a blanket reuse license.
6. **Import incrementally** with pagination, backoff, conditional requests, per-host limits, and explicit stop conditions.
7. **Validate independently**: schema, encoding, duplicates, checksums, expected fields, language coverage, content quality, and reproducibility.
8. **Publish evidence** as versioned JSON/CSV reports and CI artifacts. Preserve failed and blocked results instead of silently dropping them.

## Status meanings

- `DISCOVERED`: a candidate source is recorded.
- `ENDPOINT_DOCUMENTED`: an official API or interface is documented; this does not mean a bulk harvest succeeded.
- `LICENSE_REVIEW_REQUIRED`: rights must be checked for the exact resource/version before reuse.
- `ACCESS_RESTRICTED`: authentication, gating, or policy prevents current collection.
- `NOT_VALIDATED`: no reproducible import/quality test has been recorded.

Do not mark a resource as imported or tested without an artifact checksum and a retained validation report.

## Evidence and operational boundaries

- The official [Hugging Face Hub API documentation](https://huggingface.co/docs/hub/api) documents model, dataset, and Space discovery interfaces and an OpenAPI specification.
- [OpenAlex's API reference](https://help.openalex.org/api/) documents public REST access to scholarly works and related entities; its metadata license does not change the rights of linked publications.
- [Crossref's REST API documentation](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/) states that public access does not require registration and recommends polite use.
- [GitHub's license API documentation](https://docs.github.com/en/rest/licenses/licenses) explains that license detection is based on matching a repository's `LICENSE` file and does not cover every dependency or other license statement.
- [GitHub Actions workflow documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows) notes that scheduled workflows run from the default branch and may be delayed or disabled under repository inactivity/policy. Actions is useful for recurring audits, not a guarantee of unlimited 24/7 compute.

## Current validation state

**PARTIAL / NOT VALIDATED:** this commit adds the initial research map and machine-readable manifest. It does not claim that every endpoint was queried, every source is currently available, any full dataset was downloaded, all licenses were approved, or that every modality is implemented in the project.
