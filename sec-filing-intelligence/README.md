# SEC Filing Intelligence

An educational Python project for evidence retrieval over public SEC filings.
It compares a term-overlap baseline with BM25 plus bigram rank fusion and
returns a verbatim passage with a verifiable source citation. It runs offline
on small, clearly fictional fixtures. No model, API key, vector database, or
external service is required.

**Implementation status:** source, tests, fixtures, and an unexecuted notebook
are provided. Generated code, tests, notebook cells, and evaluation have **not
been executed during implementation**. No real SEC filings have been downloaded,
and no measured results are claimed. Validation is a separate step.

## Problem and scope

Filings contain similar language across issuers and years. A useful answer must
trace to the correct issuer, period, document, and passage. This project teaches
retrieval, source identity, abstention, evaluation, and the limits of treating
retrieved text as trustworthy evidence.

The answer component is deliberately extractive: it returns one full paragraph
as an `evidence_excerpt`, not an LLM-generated summary. It cannot reliably
calculate growth, reconcile accounting definitions, compare multiple filings,
or establish that a retrieved passage answers every part of a question.
The project is a transparent starting point for RAG, not a validated financial
research system.

## Setup and offline use

Use Python 3.10 or newer. Run from this repository's root. These commands are
instructions for a later validation session; they were not run during creation.
The core uses only the Python standard library. Optional dependencies and build
tools have version constraints in `pyproject.toml`; they are not an exact lockfile.

PowerShell, without installing anything:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m sec_filing_intelligence.cli "What was Cedar revenue in fiscal 2024?" --document-id cedar-2024-10k
python -m sec_filing_intelligence.evaluate --k 3 --output reports/fixture-evaluation.json
```

If pytest is already available:

```powershell
python -m pytest
```

In an environment where dependency installation is permitted, the following
optional setup installs the constrained teaching tools:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
filing-qa "Cedar cash and cash equivalents" --document-id cedar-2023-10k --method overlap
filing-evaluate --output reports/fixture-evaluation.json
```

Tests use fixtures and mocked HTTP transport; they do not require internet
access. The development extras support executing the notebook with `nbclient`;
a Jupyter-compatible editor may be used as the interface. For repeatable results
record the Python version and resolved dependency versions alongside evaluation
reports. Do not copy environment variables or credentials into reports.

## Data provenance and rights

`data/fixtures/filings.json` contains three short **synthetic** records about two
fictional companies. Amounts, wording, query labels, and attack strings were
authored for this project. `fixture://` source URIs identify local fixtures;
they are not SEC links. Fixture JSON files are CC0 1.0; see the fixture README.
Code and documentation are MIT licensed under `LICENSE`.

For real data, manually choose a public 10-K or 10-Q primary document using
the [SEC EDGAR search](https://www.sec.gov/edgar/search/). The opt-in acquisition
module accepts only direct `https://www.sec.gov/Archives/edgar/data/...` URLs,
rejects redirects, uses an identifying contact user agent, limits downloads to
15 MB, and performs one request with no automatic retries. It sleeps 0.2 seconds
before requesting; it has no coordination across processes. Use it serially.
Review the current [SEC developer resources](https://www.sec.gov/about/developer-resources)
and [website privacy/security policy](https://www.sec.gov/privacy.htm) before
accessing EDGAR. These reference links were not fetched during implementation;
current access rules have not been verified. Stop on denial or rate limiting.

In a later session with network access authorized, replace the URL and metadata
below with a filing you selected. The placeholder is intentionally unusable.
Use a real identifying organization and contact address, never a credential:

```powershell
python -m sec_filing_intelligence.acquire "PASTE_DIRECT_SEC_FILING_URL" --user-agent "YourOrganization your-contact@example.org" --document-id issuer-2024-10k --company "Issuer name" --form 10-K --period 2024-12-31
python -m sec_filing_intelligence.cli "What risks are disclosed?" --corpus data/downloads/issuer-2024-10k/corpus.json --document-id issuer-2024-10k
```

The acquisition command saves `raw.bin`, `corpus.json`, and `manifest.json` in
a new per-document bundle. The manifest records the retrieval timestamp,
source URL, raw and normalized SHA-256 hashes, encoding, size, and normalizer
version. User-supplied issuer/form/period metadata must be checked against the
filing header. Reusing an existing output bundle fails rather than overwriting.
A disk-write failure can leave a partial bundle; inspect it and use a new ID
for a retry. No request headers or contact email are written into the manifest.

Public accessibility does not establish a blanket reuse license. Filings and
exhibits may include issuer or third-party copyrighted material. Review rights
and terms before redistributing downloaded text; the code's MIT license does
not license external filings. Downloaded data and generated reports are ignored
by the included `.gitignore`.

## Methods and citation contract

1. Validate a JSON list of documents with unique IDs, issuer, form, fiscal
   period, source URL, provenance, and text. No network requests occur on import.
2. Split normalized text on blank lines, including headings. A chunk ID combines
   the document ID with its zero-based paragraph index, such as
   `cedar-2024-10k:p1`. Paragraphs have no maximum length in this teaching version.
3. Apply optional document and period filters before ranking. For actual use,
   select the exact document ID: a shared period does not identify an issuer.
   The system does not infer issuer identity or years from natural language.
4. Rank using `overlap` (count of distinct shared tokens) or `hybrid` (BM25
   with k1=1.5, b=0.75, plus matching adjacent token pairs). Rank positive BM25
   and bigram scores separately, then sum `1/(60 + rank)` for reciprocal rank
   fusion. Ties break by chunk ID. Scores are not probabilities. Tokenization
   lowercases ASCII words/numbers and removes a small fixed stopword list;
   there is no stemming, embedding model, or semantic search.
5. Scan the top k hits and return the first eligible paragraph. Headings with
   fewer than five remaining tokens and known instruction-like passages are
   skipped. Unknown or unsupported queries can still match unrelated language;
   no overlap or no eligible passage causes abstention.
6. Verify every citation before returning it. It contains document ID, source
   URL, normalized document hash, chunk ID, exact quote, and start/end Unicode
   character offsets (end exclusive). Verification checks all these fields
   against the stored document and paragraph boundaries. Offsets refer to
   normalized text, **not bytes, PDF pages, or positions in raw HTML**.

Hashes detect changes relative to the local corpus; they do not authenticate
an issuer or establish truth. The raw download hash in the acquisition manifest
supports auditing normalization. For a particular real-data run, preserve the
raw bundle, normalized corpus, query judgments, and software versions together.

## Evaluation and error analysis

Run `python -m sec_filing_intelligence.evaluate` from the root. It compares both
methods with the same corpus, queries, filters, and k. It prints JSON and can
write a report using `--output`. No report is checked in as an executed result.

| Metric | Definition and denominator |
| --- | --- |
| Recall@k | Relevant chunks in the top k divided by all labeled relevant chunks for that query. |
| Reciprocal rank@k | 1/rank of the first relevant chunk in the top k, or zero if none. The reported mean is truncated MRR@k. |
| nDCG@k | Sum of binary relevance/log2(rank+1), divided by the ideal ordering at k. |
| Answerability accuracy | Fraction of all queries where emitting an excerpt versus abstaining agrees with the expected-answer label. This does not assess answer correctness. |
| Citation integrity | Fraction of emitted citations passing exact local-source verification. Null when none are emitted. This does not assess relevance or factual truth. |
| Payload-not-echoed rate | Fraction of synthetic document attacks that are retrieved but whose full payload does not appear in an emitted citation. Unretrieved attacks fail this check to prevent vacuous success. This is a narrow output check, not a general attack-success or security measure. |

Retrieval means exclude unanswerable queries because those have no ideal
relevance ordering. Missing hits count as zero; there is no padding with
invented results. The report includes per-query ranked IDs and statuses for
manual inspection. The fixture has six answerable questions and one
unanswerable question; it is too small and too tailored to support performance
claims or a claim that hybrid retrieval improves on the baseline.

The adversarial report uses hybrid retrieval at k=10, prepends each attack to
the first document with matching query terms, and records how many payloads
were actually retrieved before checking output. This fixed attack setup is
separate from the k used for the labeled retrieval comparison.

For a meaningful real-data experiment, create separately labeled development
and held-out sets split by issuer and period. Keep related amendments and
near-duplicate filings together. Label every acceptable supporting paragraph,
include hard negatives across years/issuers, and include unanswerable questions
with overlapping vocabulary. Freeze tokenization, k, and filters before looking
at held-out results. Use multiple reviewers for ambiguous labels. Report sample
counts and uncertainty, and inspect errors for tables, numeric units, wrong
periods, missing evidence, and mismatched accounting concepts. Record reviewer
judgments separately from retrieval metrics; citation integrity alone cannot
measure answer faithfulness or completeness.

## Adversarial boundaries

`data/fixtures/adversarial.json` includes instruction override, secret
exfiltration, spoofed system role, and hidden-markup payloads. Tests force
poisoned passages into retrieved candidates, verify selected known attacks are
skipped, test suspicious user queries, and demonstrate an unseen paraphrase
that bypasses the heuristic.

Retrieved text is always data: this project has no LLM, shell-execution tool,
external link follower, or agent capable of acting on passage instructions.
The explicit acquisition command is the only network component. The regex
filter is a demonstration and has false positives and false negatives; an
unknown attack can be returned as a quoted paragraph. Never treat excerpt text
as trusted instructions. Adding a generative model would require a separate
threat model and evaluation of instruction isolation, fabricated citations,
tool permissions, and information disclosure.

## Notebook, files, and limitations

Open `notebooks/01_grounded_retrieval.ipynb` to explore chunks, rankings,
citations, hand-calculated metrics, and adversarial data. All cells have empty
outputs and null execution counts. Exercises cover cross-year retrieval,
numeric ambiguity, labeling, and defenses.

The `src/sec_filing_intelligence` modules implement corpus handling, retrieval,
extractive answering, acquisition, CLI, and evaluation. `tests/` covers offsets,
tampering, ranking, filters, abstention, metrics, attack cases, URL restrictions,
normalization, and a mocked acquisition. No CI workflows are included or changed.

HTML extraction is intentionally basic: it does not faithfully preserve table
headers, footnotes, inline XBRL semantics, CSS visibility, or PDF layout. Large
paragraphs and whole-index scans are unsuitable for large corpora. Lexical
ranking cannot resolve paraphrases, ambiguous entities, restatements, financial
units, or multi-hop questions. There is no trained model and no training claim.

Use only for education and research. Evidence excerpts are not investment,
accounting, or legal advice. Check the original filing, its amendments, context,
units, and dates before drawing conclusions. Real-data acquisition, dependency
compatibility, test outcomes, notebook execution, and retrieval quality all
remain unverified until separately run and reviewed.
