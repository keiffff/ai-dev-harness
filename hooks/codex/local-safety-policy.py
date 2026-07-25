#!/usr/bin/env python3
import re
import sys
from typing import Optional

from hook_utils import extract_command, first_command_name, is_invalid_payload, load_payload, normalize_command_tokens, split_segments, unsafe_shell_reason

DB_COMMANDS = {"p" + "sql", "my" + "sql", "mongo" + "sh", "mongo", "redis" + "-cli"}
PACKAGE_MANAGERS = {"npm", "pnpm", "yarn", "bun"}
RISKY_SCRIPT_RE = re.compile(r"(^|[:_-])(deploy|release|publish|migrate|migration|seed|db|database|prisma|drizzle|typeorm|knex|cdk|terraform|tf|sst|serverless|sam|pulumi|prod|production)($|[:_-])", re.IGNORECASE)
SENSITIVE_VAR_RE = re.compile(r"\$[{(]?(?:[A-Z0-9_]*(TOKEN|SECRET|PASSWORD|PASS|KEY|CREDENTIAL|AUTH)[A-Z0-9_]*)[})]?", re.IGNORECASE)
SENSITIVE_PATH_RE = re.compile(r"(^|/)(\.env(\..*)?|\.npmrc|\.pypirc|\.netrc|credentials|config|auth\.json|id_rsa|id_ed25519|known_hosts|\.git-credentials)$")


def deny(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(2)


def contains_recursive_force_remove(tokens: list[str]) -> bool:
    tokens = normalize_command_tokens(tokens)
    if not tokens:
        return False
    cmd = first_command_name(tokens)
    if cmd == "r" + "m":
        flags = "".join(token[1:] for token in tokens[1:] if token.startswith("-") and not token.startswith("--"))
        return "r" in flags and "f" in flags
    if cmd == "x" + "args" and any(token == "r" + "m" or token.endswith("/" + "r" + "m") for token in tokens[1:]):
        flags = "".join(token[1:] for token in tokens[1:] if token.startswith("-") and not token.startswith("--"))
        return "r" in flags and "f" in flags
    return False


def contains_sensitive_path(tokens: list[str]) -> bool:
    tokens = normalize_command_tokens(tokens)
    if not tokens:
        return False
    readers = {"cat", "less", "more", "head", "tail", "sed", "awk", "nl", "grep", "rg"}
    if first_command_name(tokens) not in readers:
        return False
    return any(SENSITIVE_PATH_RE.search(token) for token in tokens[1:] if not token.startswith("-"))


def package_script_name(tokens: list[str]) -> Optional[str]:
    tokens = normalize_command_tokens(tokens)
    if not tokens:
        return None
    cmd = first_command_name(tokens)
    if cmd == "npm":
        if len(tokens) >= 2 and tokens[1] == "publish":
            return "publish"
        if len(tokens) >= 3 and tokens[1] in {"run", "run-script"}:
            return tokens[2]
    if cmd == "pnpm":
        if len(tokens) >= 2 and tokens[1] == "publish":
            return "publish"
        if len(tokens) >= 3 and tokens[1] == "run":
            return tokens[2]
        if len(tokens) >= 2 and not tokens[1].startswith("-") and tokens[1] not in {"install", "add", "remove", "exec", "dlx"}:
            return tokens[1]
    if cmd == "yarn":
        if len(tokens) >= 3 and tokens[1] == "npm" and tokens[2] == "publish":
            return "publish"
        if len(tokens) >= 3 and tokens[1] == "run":
            return tokens[2]
        if len(tokens) >= 2 and not tokens[1].startswith("-") and tokens[1] not in {"install", "add", "remove", "exec", "dlx"}:
            return tokens[1]
    if cmd == "bun":
        if len(tokens) >= 2 and tokens[1] == "publish":
            return "publish"
        if len(tokens) >= 3 and tokens[1] == "run":
            return tokens[2]
        if len(tokens) >= 2 and not tokens[1].startswith("-"):
            return tokens[1]
    return None


def block_reason_for_tokens(tokens: list[str]) -> Optional[str]:
    tokens = normalize_command_tokens(tokens)
    if not tokens:
        return None
    cmd = first_command_name(tokens)
    if cmd in DB_COMMANDS:
        return "Blocked database CLI."
    if cmd in {"env", "printenv"}:
        return "Blocked environment dump."
    if cmd == "security" and len(tokens) >= 2 and tokens[1] == "find-generic-password":
        return "Blocked raw Keychain secret read."
    if cmd in {"export", "set"}:
        return "Blocked shell environment dump/setup command."
    if contains_sensitive_path(tokens):
        return "Blocked reading a sensitive credential/config file."
    if cmd in {"echo", "printf"} and SENSITIVE_VAR_RE.search(" ".join(tokens[1:])):
        return "Blocked command that may print a sensitive environment variable."
    if contains_recursive_force_remove(tokens):
        return "Blocked recursive force remove."
    if cmd == "find" and "-delete" in tokens:
        return "Blocked destructive find delete."
    if cmd == "git" and len(tokens) >= 2 and tokens[1] == "clean":
        return "Blocked git clean."
    if cmd in {"chmod", "chown", "chgrp"} and any(token in {"-R", "--recursive"} for token in tokens[1:]):
        return "Blocked recursive permission/ownership change."
    if cmd in PACKAGE_MANAGERS:
        script = package_script_name(tokens)
        if script and RISKY_SCRIPT_RE.search(script):
            return "Blocked risky package script."
    return None


def block_reason(command: str) -> Optional[str]:
    if not command:
        return None
    reason = unsafe_shell_reason(command)
    if reason:
        return reason
    segments = split_segments(command)
    if segments is None:
        return "Blocked malformed shell command."
    for segment in segments:
        reason = block_reason_for_tokens(segment)
        if reason:
            return reason
    return None


def main() -> None:
    payload = load_payload(sys.stdin)
    if payload is None:
        return
    if is_invalid_payload(payload):
        deny("Blocked invalid hook payload.")
    reason = block_reason(extract_command(payload))
    if reason:
        deny(reason)


if __name__ == "__main__":
    main()
