"""Run retrieval, citation-integrity, abstention, and attack-output checks."""

import argparse
from dataclasses import replace
import json
import math
from pathlib import Path

from .answer import Citation, answer, verify_citation
from .corpus import load_documents
from .retrieval import Index


def retrieval_metrics(ranked: list[str], relevant: set[str], k: int) -> dict[str, float]:
    if k < 1 or not relevant:
        raise ValueError("Retrieval metrics require k > 0 and nonempty relevance labels")
    if len(ranked) != len(set(ranked)):
        raise ValueError("Ranked results must be unique")
    ranked = ranked[:k]
    gains = [int(item in relevant) for item in ranked]
    dcg = sum(gain / math.log2(rank + 2) for rank, gain in enumerate(gains))
    ideal = sum(1 / math.log2(rank + 2) for rank in range(min(k, len(relevant))))
    return {
        "recall_at_k": sum(gains) / len(relevant),
        "reciprocal_rank_at_k": next((1 / (rank + 1) for rank, gain in enumerate(gains) if gain), 0.0),
        "ndcg_at_k": dcg / ideal,
    }


def evaluate(corpus: Path, queries: Path, attacks: Path, k: int = 3) -> dict:
    documents = load_documents(corpus)
    index = Index(documents)
    labels = json.loads(queries.read_text(encoding="utf-8"))
    payloads = json.loads(attacks.read_text(encoding="utf-8"))
    if not labels or not payloads:
        raise ValueError("Evaluation queries and attacks must be nonempty")
    known = {chunk.id: chunk.document_id for chunk in index.chunks}
    report = {"corpus": str(corpus), "k": k, "methods": {},
              "warning": "Fixture results are not evidence of real SEC performance."}
    for method in ("overlap", "hybrid"):
        rows = []
        valid_citations = total_citations = correct_abstentions = 0
        for row in labels:
            relevant = set(row["relevant_chunk_ids"])
            filters = row.get("filters", {})
            if set(filters) - {"document_id", "period"}:
                raise ValueError("Unsupported query filter")
            if not relevant <= known.keys():
                raise ValueError(f"Unknown relevance label in {row['id']}")
            for chunk_id in relevant:
                doc = index.documents[known[chunk_id]]
                if ((filters.get("document_id", doc.id) != doc.id)
                        or (filters.get("period", doc.period) != doc.period)):
                    raise ValueError("Relevant chunk excluded by query filters")
            if bool(relevant) != row["expected_answer"]:
                raise ValueError("Expected-answer label must agree with relevance labels")
            hits = index.search(row["query"], method=method, k=k, **filters)
            output = answer(index, row["query"], method=method, k=k, **filters)
            citations = output["citations"]
            total_citations += len(citations)
            valid_citations += sum(verify_citation(Citation(**c), index.documents) for c in citations)
            correct_abstentions += ((output["status"] != "abstained") == row["expected_answer"])
            metrics = retrieval_metrics([h.chunk.id for h in hits], relevant, k) if relevant else None
            rows.append({"id": row["id"], "retrieved": [h.chunk.id for h in hits],
                         "metrics": metrics, "status": output["status"]})
        scored = [row["metrics"] for row in rows if row["metrics"] is not None]
        means = {key: sum(row[key] for row in scored) / len(scored)
                 for key in scored[0]} if scored else {}
        report["methods"][method] = {
            "answerable_query_count": len(scored), "query_count": len(labels),
            "mean_retrieval_metrics": means,
            "answerability_accuracy": correct_abstentions / len(labels),
            "citation_integrity": valid_citations / total_citations if total_citations else None,
            "citation_count": total_citations, "per_query": rows,
        }
    # Force attacks into the requested document so filters cannot accidentally hide them.
    contained = retrieved_payloads = 0
    for attack in payloads:
        payload = attack["payload"]
        if not isinstance(payload, str) or not payload.strip():
            raise ValueError("Attack payload must be nonempty text")
        injected = "Revenue earnings citation. " + payload
        poisoned = replace(documents[0], text=injected + "\n\n" + documents[0].text)
        poisoned_index = Index([poisoned, *documents[1:]])
        hits = poisoned_index.search("revenue earnings citation", document_id=poisoned.id, k=10)
        retrieved = any(payload in hit.chunk.text for hit in hits)
        retrieved_payloads += retrieved
        output = answer(poisoned_index, "revenue earnings citation", document_id=poisoned.id, k=10)
        # This checks payload echoing only; there is no executable agent or LLM.
        contained += retrieved and not any(payload in c["quote"] for c in output["citations"])
    report["adversarial"] = {"case_count": len(payloads), "payload_not_echoed_count": contained,
                             "retrieved_payload_count": retrieved_payloads, "method": "hybrid", "k": 10,
                             "payload_not_echoed_rate": contained / len(payloads),
                             "scope": "Extractive output only; not a general prompt-injection safety score."}
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("data/fixtures/filings.json"))
    parser.add_argument("--queries", type=Path, default=Path("data/fixtures/queries.json"))
    parser.add_argument("--attacks", type=Path, default=Path("data/fixtures/adversarial.json"))
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = evaluate(args.corpus, args.queries, args.attacks, args.k)
        encoded = json.dumps(report, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded + "\n", encoding="utf-8")
        print(encoded)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"Evaluation failed: {exc}\n")


if __name__ == "__main__":
    main()
