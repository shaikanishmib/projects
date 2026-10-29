"""Extractive answers: source text is data and is never sent to an interpreter."""

from dataclasses import asdict, dataclass
import re

from .corpus import Document, chunk_documents, digest
from .retrieval import Index, tokens


@dataclass(frozen=True)
class Citation:
    chunk_id: str
    document_id: str
    source_url: str
    document_sha256: str
    start: int
    end: int
    quote: str


def verify_citation(citation: Citation, documents: dict[str, Document]) -> bool:
    doc = documents.get(citation.document_id)
    if doc is None:
        return False
    return (
        citation.source_url == doc.source_url
        and citation.document_sha256 == digest(doc.text)
        and 0 <= citation.start < citation.end <= len(doc.text)
        and doc.text[citation.start:citation.end] == citation.quote
        and bool(citation.quote.strip())
        and any(chunk.id == citation.chunk_id and chunk.start == citation.start
                and chunk.end == citation.end for chunk in chunk_documents([doc]))
    )


def suspicious(text: str) -> bool:
    """Conservative demonstration heuristic; not a complete injection detector."""
    return bool(re.search(
        r"ignore.{0,40}instructions|system\s*:|<\|im_start\|>|"
        r"api[ _-]?key|send\s+secrets|forg(?:e|ed)\s+citation|"
        r"replace\s+every\s+citation", text, re.IGNORECASE | re.DOTALL,
    ))


def answer(index: Index, question: str, *, method: str = "hybrid", k: int = 3,
           document_id: str | None = None, period: str | None = None) -> dict:
    """Return a verbatim passage, never a generated financial interpretation.

    Lexical overlap is a weak abstention policy: irrelevant but overlapping text
    can still be returned. The output explicitly calls itself an evidence excerpt.
    """
    if suspicious(question):
        return {"status": "abstained", "reason": "Suspicious query instruction", "citations": []}
    hits = index.search(question, method=method, k=k, document_id=document_id, period=period)
    for hit in hits:
        chunk = hit.chunk
        # Skip headings and instruction-like paragraphs. No tool or model consumes them.
        if len(tokens(chunk.text)) < 5 or suspicious(chunk.text):
            continue
        citation = Citation(chunk.id, chunk.document_id, chunk.source_url,
                            chunk.document_sha256, chunk.start, chunk.end, chunk.text)
        if not verify_citation(citation, index.documents):
            raise ValueError("Citation failed source verification")
        return {"status": "evidence_excerpt", "answer": chunk.text,
                "citations": [asdict(citation)],
                "notice": "Verbatim evidence; relevance and completeness require review."}
    return {"status": "abstained", "reason": "No eligible evidence in retrieved passages", "citations": []}
