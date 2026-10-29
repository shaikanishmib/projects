"""Validated documents and lossless paragraph chunks with character offsets."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Document:
    id: str
    company: str
    form: str
    period: str
    source_url: str
    provenance: str
    text: str


@dataclass(frozen=True)
class Chunk:
    id: str
    document_id: str
    source_url: str
    document_sha256: str
    start: int
    end: int
    text: str


def load_documents(path: str | Path) -> list[Document]:
    """Reject invalid or duplicate records rather than silently dropping them."""
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("Corpus must be a nonempty JSON list")
    documents = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Every document must be an object")
        try:
            doc = Document(**row)
        except TypeError as exc:
            raise ValueError("Document fields do not match the schema") from exc
        if any(not isinstance(value, str) or not value.strip() for value in row.values()):
            raise ValueError("Document fields must be nonempty strings")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", doc.id):
            raise ValueError("Document ID must use letters, digits, hyphens, underscores")
        if doc.id in seen:
            raise ValueError(f"Duplicate document ID: {doc.id}")
        seen.add(doc.id)
        documents.append(doc)
    return documents


def chunk_documents(documents: list[Document]) -> list[Chunk]:
    """Offsets index Unicode characters in stored normalized text, not raw HTML."""
    chunks = []
    for doc in documents:
        for index, match in enumerate(re.finditer(r"\S[\s\S]*?(?=\n\s*\n|\Z)", doc.text)):
            end = match.end()
            while end > match.start() and doc.text[end - 1].isspace():
                end -= 1
            chunks.append(Chunk(
                f"{doc.id}:p{index}", doc.id, doc.source_url, digest(doc.text),
                match.start(), end, doc.text[match.start():end],
            ))
    return chunks
