#!/usr/bin/env python3

import contextlib
import io
import runpy
import sys
from pathlib import Path


POLICIES = (
    "git-policy.py",
    "aws-policy.py",
    "gh-policy.py",
    "local-safety-policy.py",
    "gcloud-policy.py",
)


def run_policy(path: Path, payload: str) -> tuple[int, str]:
    namespace = runpy.run_path(str(path))
    previous_stdin = sys.stdin
    output = io.StringIO()
    try:
        sys.stdin = io.StringIO(payload)
        with contextlib.redirect_stdout(output):
            try:
                namespace["main"]()
            except SystemExit as exc:
                return int(exc.code or 0), output.getvalue()
    finally:
        sys.stdin = previous_stdin
    return 0, output.getvalue()


def main() -> None:
    payload = sys.stdin.read()
    hook_dir = Path(__file__).resolve().parent
    for name in POLICIES:
        status, output = run_policy(hook_dir / name, payload)
        if status:
            sys.stdout.write(output)
            raise SystemExit(status)


if __name__ == "__main__":
    main()
