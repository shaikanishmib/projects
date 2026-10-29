import math

import pytest

from sec_filing_intelligence.evaluate import evaluate, retrieval_metrics


@pytest.mark.parametrize("method", ["overlap", "hybrid"])
def test_retrieval_ranking_filter_and_determinism(index, method):
    hits = index.search("Cedar single supplier specialty sensors", method=method,
                        document_id="cedar-2024-10k")
    assert hits[0].chunk.id == "cedar-2024-10k:p3"
    assert hits == index.search("Cedar single supplier specialty sensors", method=method,
                                document_id="cedar-2024-10k")
    assert all(h.chunk.document_id == "cedar-2024-10k" for h in hits)
    assert all(h.chunk.document_id == "cedar-2023-10k"
               for h in index.search("cash", period="2023-12-31", method=method))


def test_metrics_hand_calculated():
    scores = retrieval_metrics(["wrong", "gold-a", "gold-b"], {"gold-a", "gold-b"}, 2)
    assert scores["recall_at_k"] == 0.5
    assert scores["reciprocal_rank_at_k"] == 0.5
    assert scores["ndcg_at_k"] == pytest.approx((1 / math.log2(3)) / (1 + 1 / math.log2(3)))
    assert retrieval_metrics([], {"gold"}, 3)["ndcg_at_k"] == 0
    with pytest.raises(ValueError):
        retrieval_metrics(["gold", "gold"], {"gold"}, 3)
    with pytest.raises(ValueError):
        retrieval_metrics([], set(), 3)


def test_invalid_search_arguments(index):
    with pytest.raises(ValueError):
        index.search("cash", k=0)
    with pytest.raises(ValueError):
        index.search("cash", method="unknown")


def test_evaluation_report_structure(fixture_dir):
    report = evaluate(fixture_dir / "filings.json", fixture_dir / "queries.json",
                      fixture_dir / "adversarial.json")
    assert set(report["methods"]) == {"overlap", "hybrid"}
    for method in report["methods"].values():
        assert method["query_count"] == 7
        assert method["answerable_query_count"] == 6
        assert method["citation_count"] > 0
        assert method["citation_integrity"] == 1.0
        assert all(0 <= value <= 1 for value in method["mean_retrieval_metrics"].values())
    assert report["adversarial"]["case_count"] == 4
    assert report["adversarial"]["retrieved_payload_count"] == 4
