"""Term-overlap baseline and BM25 + bigram reciprocal rank fusion."""

from collections import Counter
from dataclasses import dataclass
import math
import re

from .corpus import Chunk, Document, chunk_documents


STOPWORDS = frozenset("a an and are as at be by did do does for from had has how in is it of on or reported the to was were what which with much".split())


def tokens(text: str) -> list[str]:
    return [word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOPWORDS]


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


class Index:
    def __init__(self, documents: list[Document]):
        self.documents = {doc.id: doc for doc in documents}
        if len(self.documents) != len(documents):
            raise ValueError("Duplicate document IDs")
        self.chunks = chunk_documents(documents)
        self.terms = [Counter(tokens(chunk.text)) for chunk in self.chunks]

    def search(self, query: str, *, method: str = "hybrid", k: int = 3,
               document_id: str | None = None, period: str | None = None) -> list[Hit]:
        if method not in {"overlap", "hybrid"}:
            raise ValueError("Method must be overlap or hybrid")
        if k < 1:
            raise ValueError("k must be positive")
        q = tokens(query)
        if not q:
            return []
        # Filter before computing statistics: cross-period data cannot leak into ranking.
        candidates = [i for i, c in enumerate(self.chunks)
                      if (document_id is None or c.document_id == document_id)
                      and (period is None or self.documents[c.document_id].period == period)]
        if not candidates:
            return []
        overlap = {i: float(len(set(q) & self.terms[i].keys())) for i in candidates}
        if method == "overlap":
            scores = overlap
        else:
            n = len(candidates)
            avg_length = sum(sum(self.terms[i].values()) for i in candidates) / n
            bm25 = {}
            for i in candidates:
                score = 0.0
                length = sum(self.terms[i].values())
                for term in set(q):
                    df = sum(term in self.terms[j] for j in candidates)
                    tf = self.terms[i][term]
                    idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
                    score += idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * length / max(avg_length, 1)))
                bm25[i] = score
            q_pairs = set(zip(q, q[1:]))
            phrase = {}
            for i in candidates:
                words = tokens(self.chunks[i].text)
                phrase[i] = float(len(q_pairs & set(zip(words, words[1:]))))
            scores = {i: 0.0 for i in candidates}
            for ranking in (bm25, phrase):
                ordered = sorted((i for i in candidates if ranking[i] > 0),
                                 key=lambda i: (-ranking[i], self.chunks[i].id))
                for rank, i in enumerate(ordered, 1):
                    scores[i] += 1 / (60 + rank)
        ordered = sorted((i for i in candidates if scores[i] > 0),
                         key=lambda i: (-scores[i], self.chunks[i].id))
        return [Hit(self.chunks[i], scores[i]) for i in ordered[:k]]
