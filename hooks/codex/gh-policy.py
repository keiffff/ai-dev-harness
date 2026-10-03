#!/usr/bin/env python3
import os
import re
import sys

from hook_utils import extract_command, first_command_name, is_approved_wrapper_segment, is_invalid_payload, load_payload, split_segments, unsafe_shell_reason

APPROVED_WRAPPER = os.environ.get("GH_READONLY_WRAPPER", os.path.expanduser("~/.local/bin/gh-readonly"))
USER_APPROVED_WRAPPER = os.environ.get("GH_USER_APPROVED_WRAPPER", os.path.expanduser("~/.local/bin/gh-user-approved"))
RAW_COMMANDS = {"gh"}


def deny(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(2)


def has_raw_fallback(command: str) -> bool:
    return bool(re.search(r"(^|[;&|]\s*|(?:^|\s)[A-Za-z_][A-Za-z0-9_]*=\S+\s+)(command\s+|\S*/)?(gh)(\s|$)", command))


def is_raw_command(command: str) -> bool:
    if not command:
        return False
    segments = split_segments(command)
    if segments is None:
        return has_raw_fallback(command)
    for segment in segments:
        if any(is_approved_wrapper_segment(segment, wrapper) for wrapper in (APPROVED_WRAPPER, USER_APPROVED_WRAPPER)):
            continue
        if first_command_name(segment) in RAW_COMMANDS:
            return True
    return False


def main() -> None:
    payload = load_payload(sys.stdin)
    if payload is None:
        return
    if is_invalid_payload(payload):
        deny("Blocked invalid hook payload.")
    command = extract_command(payload)
    reason = unsafe_shell_reason(command)
    if reason:
        deny(reason)
    if is_raw_command(command):
        deny("Blocked raw GitHub CLI usage. Use " + APPROVED_WRAPPER + " for read-only commands or " + USER_APPROVED_WRAPPER + " for explicitly requested PR operations. Other mutations and secret/token commands remain prohibited.")


if __name__ == "__main__":
    main()
