"""Command-line interface; imports perform no I/O or training."""

import argparse
import logging
import tomllib
from pathlib import Path

from .data import read_manifest, split_patients
from .experiment import run, validate_config
from .fixtures import create_fixture


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Research-only patient-separated pathology experiments")
    sub = parser.add_subparsers(dest="command", required=True)
    fixture = sub.add_parser("fixture", help="Create artificial pipeline-check images")
    fixture.add_argument("--output", type=Path, required=True)
    for name in ("validate", "run"):
        command = sub.add_parser(name)
        command.add_argument("--manifest", type=Path, required=True)
        command.add_argument("--data-root", type=Path, required=True)
        command.add_argument("--provenance", type=Path, required=True)
        command.add_argument("--config", type=Path, default=Path("configs/default.toml"))
        if name == "run":
            command.add_argument("--model", choices=("baseline", "cnn"), required=True)
            command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        if args.command == "fixture":
            create_fixture(args.output)
        else:
            with args.config.open("rb") as handle:
                config = validate_config(tomllib.load(handle))
            if args.command == "validate":
                samples, _ = read_manifest(args.manifest, args.data_root, args.provenance)
                splits = split_patients(samples, config["seed"], config["validation_fraction"], config["test_fraction"])
                logging.info("Validated image counts: %s", {k: len(v) for k, v in splits.items()})
            else:
                run(args.manifest, args.data_root, args.provenance, args.output, config, args.model)
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as exc:
        logging.error("%s: %s", type(exc).__name__, exc)
        return 2
    return 0
