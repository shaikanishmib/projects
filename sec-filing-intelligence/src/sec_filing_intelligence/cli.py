"""Ask a question against a local corpus."""

import argparse
import json
from pathlib import Path

from .answer import answer
from .corpus import load_documents
from .retrieval import Index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("--corpus", type=Path, default=Path("data/fixtures/filings.json"))
    parser.add_argument("--method", choices=["overlap", "hybrid"], default="hybrid")
    parser.add_argument("--document-id")
    parser.add_argument("--period", help="Exact fiscal period, e.g. 2024-12-31")
    parser.add_argument("--k", type=int, default=3)
    args = parser.parse_args()
    try:
        index = Index(load_documents(args.corpus))
        print(json.dumps(answer(index, args.question, method=args.method, k=args.k,
                                document_id=args.document_id, period=args.period), indent=2))
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(2, f"Question answering failed: {exc}\n")


if __name__ == "__main__":
    main()
