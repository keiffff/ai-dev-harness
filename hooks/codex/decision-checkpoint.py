#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys


MARKER = "CODEX_DECISION_CHECKPOINT"
ALLOWED_BASES = {
    "NEW": {"initial"},
    "HOLD": {"current-contract", "evidence-reviewed"},
    "REVISE": {"new-evidence", "contract-change", "objective-change", "proven-error"},
    "SUSPEND": {"evidence-conflict"},
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a decision transition before write-bearing tools.")
    parser.add_argument("--decision-key", required=True)
    parser.add_argument("--transition", required=True, choices=sorted(ALLOWED_BASES))
    parser.add_argument("--basis", required=True)
    parser.add_argument("--evidence", action="append", default=[])
    return parser.parse_args(argv)


def checkpoint(args: argparse.Namespace) -> dict:
    decision_key = args.decision_key.strip()
    if not decision_key or len(decision_key) > 128:
        raise ValueError("decision key must contain 1-128 characters")
    if args.basis not in ALLOWED_BASES[args.transition]:
        allowed = ", ".join(sorted(ALLOWED_BASES[args.transition]))
        raise ValueError(f"{args.transition} requires one of: {allowed}")

    evidence = [value.strip() for value in args.evidence if value.strip()]
    if args.transition in {"REVISE", "SUSPEND"} and not evidence:
        raise ValueError(f"{args.transition} requires at least one evidence reference")
    if any(len(value) > 512 for value in evidence):
        raise ValueError("evidence references must not exceed 512 characters")

    return {
        "schemaVersion": 1,
        "decisionKey": decision_key,
        "transition": args.transition,
        "basis": args.basis,
        "evidence": evidence,
    }


def main(argv: list[str] | None = None) -> int:
    try:
        value = checkpoint(parse_args(argv if argv is not None else sys.argv[1:]))
    except ValueError as exc:
        print(f"Invalid decision checkpoint: {exc}", file=sys.stderr)
        return 2
    print(f"{MARKER} {json.dumps(value, ensure_ascii=False, sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
