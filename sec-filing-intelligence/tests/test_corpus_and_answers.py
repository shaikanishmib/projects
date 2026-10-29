from dataclasses import replace
import json

import pytest

from sec_filing_intelligence.answer import Citation, answer, verify_citation
from sec_filing_intelligence.corpus import chunk_documents, digest, load_documents


def test_exact_offsets_and_labels(documents, fixture_dir):
    by_id = {doc.id: doc for doc in documents}
    chunks = chunk_documents(documents)
    for chunk in chunks:
        doc = by_id[chunk.document_id]
        assert doc.text[chunk.start:chunk.end] == chunk.text
        assert chunk.document_sha256 == digest(doc.text)
    known = {chunk.id for chunk in chunks}
    for row in json.loads((fixture_dir / "queries.json").read_text()):
        assert set(row["relevant_chunk_ids"]) <= known
    assert next(c.text for c in chunks if c.id == "cedar-2024-10k:p5").startswith("Cedar held $35 million")


@pytest.mark.parametrize("method", ["overlap", "hybrid"])
def test_answer_and_period_separation(index, method):
    output = answer(index, "Cedar cash and cash equivalents", method=method,
                    document_id="cedar-2023-10k")
    assert output["status"] == "evidence_excerpt"
    assert "$22 million" in output["answer"]
    citation = Citation(**output["citations"][0])
    assert verify_citation(citation, index.documents)
    assert not verify_citation(replace(citation, quote="Invented quote"), index.documents)
    assert not verify_citation(replace(citation, source_url="https://attacker.invalid"), index.documents)
    assert not verify_citation(replace(citation, start=-1), index.documents)
    assert not verify_citation(replace(citation, document_id="missing"), index.documents)
    assert not verify_citation(replace(citation, chunk_id="forged:p0"), index.documents)
    altered = dict(index.documents)
    altered[citation.document_id] = replace(altered[citation.document_id], text="Edited source")
    assert not verify_citation(citation, altered)


def test_abstention_and_empty_filters(index):
    assert answer(index, "zirconium dividend forecast")["status"] == "abstained"
    assert answer(index, "revenue", document_id="missing")["citations"] == []
    assert index.search("the and is") == []


def test_reject_invalid_corpus(tmp_path, documents):
    from dataclasses import asdict
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([asdict(documents[0]), asdict(documents[0])]))
    with pytest.raises(ValueError, match="Duplicate"):
        load_documents(path)
    path.write_text("[]")
    with pytest.raises(ValueError, match="nonempty"):
        load_documents(path)
    path.write_text('[{"id": "missing-fields"}]')
    with pytest.raises(ValueError, match="schema"):
        load_documents(path)
