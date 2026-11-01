# RAG foundations and retrieval optimization

A reproducible retrieval study on the original BEIR SciFact and FiQA-2018 datasets, with a complete local research notebook and separate Python modules for acquisition, validation, chunking, indexing, ranking, and evaluation.

The [public notebook](notebooks/01_public_retrieval_research.ipynb) has the same cell sources as the executed local report. It contains no saved outputs or execution counts. The local report is `notebooks/01_complete_retrieval_research.ipynb`; it is ignored by Git and retains its genuine tables and figures. Dataset records, models, embeddings, and indexes remain local.

## Measured test results

| Method | SciFact nDCG@10 | FiQA nDCG@10 |
| --- | ---: | ---: |
| BM25 | 0.6618 | 0.2321 |
| all-MiniLM-L6-v2 | 0.6451 | 0.3687 |
| multi-qa-MiniLM-L6-cos-v1 | 0.5455 | 0.3599 |
| Validation-selected reciprocal rank fusion | 0.7068 | 0.3817 |
| TinyBERT reranking, maximum 20 candidates | 0.6762 | 0.3350 |
| TinyBERT reranking, maximum 50 candidates | 0.6621 | 0.3070 |

Fusion improves on the individual baselines in these runs. The small cross-encoder reduces accuracy, and pseudo-relevance expansion also harms both datasets. Whole documents lead the BM25 chunking validation comparisons; this does not establish the best segmentation for dense retrieval. The notebook reports per-query regressions, candidate counts, paired uncertainty, truncation, and resource costs. These are retrieval results against BEIR judgments, without an answer-generation or factuality evaluation.

The complete aggregate tables are in [reports/research/metrics.csv](reports/research/metrics.csv). Exact preprocessing, validation selection, timing scope, and limitations appear in the notebook. The test sets contain 300 SciFact and 648 FiQA queries.

## Reproduce the study

Use Python 3.12 or newer. From this directory, create a local environment and install the research and test dependencies:

```powershell
python -m venv data/research-venv
data/research-venv/Scripts/python.exe -m pip install -e ".[research,dev]"
data/research-venv/Scripts/python.exe scripts/acquire.py
data/research-venv/Scripts/python.exe scripts/acquire_models.py
data/research-venv/Scripts/python.exe -m pytest
data/research-venv/Scripts/python.exe scripts/run_research.py
data/research-venv/Scripts/python.exe scripts/build_notebook.py
data/research-venv/Scripts/python.exe scripts/execute_notebook.py
data/research-venv/Scripts/python.exe scripts/publish_notebook.py
```

Acquisition refuses to overwrite existing dataset extractions. Use `scripts/acquire.py --verify-only` for existing archives. `models.lock.json` pins model commits and file hashes. `reports/requirements-lock.txt` records the executed environment; install it when reproducing that environment. Cached matrices preserve their initial measured encoding times. To obtain new timings, use a separate project-local experiment directory rather than mixing timing records.

The notebook builder refuses to overwrite an executed local report. Edit that notebook directly when revising a completed report. The publication script reads it, writes the public copy, verifies cell-source identity and empty public execution state, and confirms that the local bytes did not change.

## Study design

The experiment matrix compares whole documents, fixed windows, recursive boundary splitting, and sentence boundary splitting; two MiniLM encoders; BM25; exact cosine search; exhaustive FAISS; embedded persistent Qdrant; reciprocal rank fusion; cross-encoder reranking; and corpus-derived query transformations. Validation selects chunking and fusion configurations. Full test splits supply nDCG@10, MRR@10, MAP@10, and Recall@1/3/5/10/20. Chunk retrieval is aggregated to original document IDs before evaluation.

Search latency uses one sequential local pass. Dense query vectors are precomputed, so those times exclude query encoding. Reranking includes candidate retrieval and cross-encoder scoring. Matrix sizes and artifact storage are measured. An optional process observer records sampled RSS and the observed Windows lifetime peak-working-set counter; it does not isolate each index's memory cost. Semantic chunking and generative HyDE are outside the executed matrix.

For process-memory observations, run `scripts/monitor_process.py --pid <PID>` with the project Python executable in another terminal while the experiment runner is active. The runner prints its process ID. FiQA exceeds the Qdrant client's 20,000-point recommendation for embedded mode; these measurements describe local persistent Qdrant, not a server deployment.

Read [DATA.md](docs/DATA.md) for source URLs, exact counts, hashes, split definitions, quality findings, attribution, and unresolved underlying-text rights. FiQA's 38 empty document bodies remain unchanged. No raw dataset content is published.

## Code and evidence

`src/rag_data/` contains maintained modules. `tests/` checks formulas, failure cases, deterministic selection, leakage prevention, backend consistency, chunk aggregation, and real dataset integrity. Test fixtures are small correctness examples, not benchmark observations.

`reports/research/` holds aggregate measurements and the execution environment. Local per-query diagnostics, figures, matrices, and Qdrant storage are under `data/`. `reports/notebook-verification.json` records publication-copy checks. Cleanup manifests and recoverable legacy work remain local under `reports/cleanup/` and `.local/`.
