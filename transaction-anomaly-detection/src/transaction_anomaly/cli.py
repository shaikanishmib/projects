"""Local batch commands; no network access or implicit dataset acquisition."""

import argparse
import logging
from pathlib import Path

from .data import synthetic_records
from .pipeline import run_experiment, score_batch, sha256, write_json


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate", help="Create explicitly synthetic labelled data")
    generate.add_argument("--output", type=Path, required=True)
    generate.add_argument("--rows", type=int, default=12000)
    generate.add_argument("--seed", type=int, default=42)
    train = commands.add_parser("train", help="Fit and evaluate an immutable local run")
    train.add_argument("--data", type=Path, required=True)
    train.add_argument("--output", type=Path, required=True)
    train.add_argument("--train-end", default="2025-02-24T00:00:00Z")
    train.add_argument("--validation-end", default="2025-03-14T00:00:00Z")
    train.add_argument("--seed", type=int, default=42)
    score = commands.add_parser("score", help="Score using a trusted local run artifact")
    score.add_argument("--model", type=Path, required=True)
    score.add_argument("--data", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        if args.command == "generate":
            provenance = args.output.with_suffix(args.output.suffix + ".provenance.json")
            if args.output.exists() or provenance.exists():
                raise ValueError("Dataset or provenance output already exists")
            frame = synthetic_records(args.rows, args.seed)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            frame.to_csv(args.output, index=False)
            write_json(provenance, {
                "kind": "explicitly_synthetic", "generator": "transaction_anomaly.data.synthetic_records",
                "seed": args.seed, "rows": args.rows, "sha256": sha256(args.output),
                "license": "CC0-1.0", "contains_real_transactions": False,
            })
        elif args.command == "train":
            run_experiment(args.data, args.output, args.train_end, args.validation_end, args.seed)
        else:
            score_batch(args.model, args.data, args.output)
    except (ValueError, OSError, KeyError, RuntimeError) as exc:
        logging.getLogger(__name__).error("%s", exc)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
