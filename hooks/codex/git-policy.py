#!/usr/bin/env python3
import os
import re
import sys
from typing import Optional

from hook_utils import extract_command, first_command_name, is_approved_wrapper_segment, is_invalid_payload, load_payload, normalize_command_tokens, split_segments, unsafe_shell_reason

APPROVED_WRAPPER = os.environ.get("GIT_USER_APPROVED_WRAPPER", os.path.expanduser("~/.local/bin/git-user-approved"))
BLOCKED_SUBCOMMANDS = {"commit", "push"}


def deny(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(2)


def git_subcommand(tokens: list[str]) -> Optional[str]:
    tokens = normalize_command_tokens(tokens)
    if not tokens or first_command_name(tokens) != "git":
        return None
    i = 1
    options_with_value = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
    while i < len(tokens):
        token = tokens[i]
        if token == "--":
            return None
        if token in options_with_value:
            i += 2
            continue
        if any(token.startswith(opt + "=") for opt in options_with_value if opt.startswith("--")):
            i += 1
            continue
        if token.startswith("-"):
            i += 1
            continue
        return token
    return None


def has_blocked_git_fallback(command: str) -> bool:
    pattern = re.compile(r"(^|[;&|]\s*)(command\s+|\S*/)?git(?:\s+(?:-[A-Za-z]+|--[A-Za-z0-9-]+(?:=\S+)?)(?:\s+\S+)?)*\s+(commit|push)\b")
    return bool(pattern.search(command))


def is_blocked_git_command(command: str) -> bool:
    if not command:
        return False
    segments = split_segments(command)
    if segments is None:
        return has_blocked_git_fallback(command)
    for segment in segments:
        if is_approved_wrapper_segment(segment, APPROVED_WRAPPER):
            continue
        if git_subcommand(segment) in BLOCKED_SUBCOMMANDS:
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
    if is_blocked_git_command(command):
        deny("Blocked raw git commit/push. Use " + APPROVED_WRAPPER + " commit|push only after the user explicitly asks for commit or push.")


if __name__ == "__main__":
    main()
