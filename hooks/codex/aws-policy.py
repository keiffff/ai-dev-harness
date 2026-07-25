#!/usr/bin/env python3
import os
import re
import sys

from hook_utils import extract_command, first_command_name, is_approved_wrapper_segment, is_invalid_payload, load_payload, split_segments, unsafe_shell_reason

APPROVED_WRAPPER = os.environ.get("AWS_READONLY_WRAPPER", os.path.expanduser("~/.local/bin/aws-readonly"))
RAW_COMMANDS = {"aws"}


def deny(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(2)


def has_raw_fallback(command: str) -> bool:
    return bool(re.search(r"(^|[;&|]\s*|(?:^|\s)[A-Za-z_][A-Za-z0-9_]*=\S+\s+)(command\s+|\S*/)?(aws)(\s|$)", command))


def is_raw_command(command: str) -> bool:
    if not command:
        return False
    segments = split_segments(command)
    if segments is None:
        return has_raw_fallback(command)
    for segment in segments:
        if is_approved_wrapper_segment(segment, APPROVED_WRAPPER):
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
        deny("Blocked raw AWS CLI usage. Use " + APPROVED_WRAPPER + " for allowed read-only commands. For mutation or secret/token commands, present the command to the user instead of executing it.")


if __name__ == "__main__":
    main()
