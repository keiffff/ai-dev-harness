#!/usr/bin/env python3

import json
import os
import re
import sys
from pathlib import Path

from hook_utils import first_command_name, is_invalid_payload, load_payload, normalize_command_tokens, shell_tokens, split_segments


MARKER_RE = re.compile(r"CODEX_DECISION_CHECKPOINT\s+(\{[^\r\n]+\})")
ALLOWED_BASES = {
    "NEW": {"initial"},
    "HOLD": {"current-contract", "evidence-reviewed"},
    "REVISE": {"new-evidence", "contract-change", "objective-change", "proven-error"},
    "SUSPEND": {"evidence-conflict"},
}
READ_ONLY_COMMANDS = {
    "basename", "cat", "date", "diff", "dirname", "du", "find", "git", "grep",
    "head", "jq", "ls", "md5", "nl", "pwd", "readlink", "realpath", "rg", "sed",
    "sha256sum", "shasum", "sort", "stat", "tail", "tree", "type", "uniq", "wc", "which",
}
READ_ONLY_GIT = {
    "cat-file", "diff", "fetch", "grep", "log", "ls-files", "ls-tree", "merge-base",
    "rev-list", "rev-parse", "show", "status",
}


def deny(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(2)


def tool_name(payload: dict) -> str:
    for key in ("tool_name", "tool", "name"):
        value = payload.get(key)
        if isinstance(value, str):
            return value.casefold()
    return ""


def tool_input(payload: dict) -> dict:
    value = payload.get("tool_input") or payload.get("input") or {}
    return value if isinstance(value, dict) else {}


def checkpoint_command(tokens: list[str]) -> bool:
    tokens = normalize_command_tokens(tokens)
    if not tokens:
        return False
    candidate = ""
    if first_command_name(tokens) == "decision-checkpoint.py":
        candidate = tokens[0]
    elif first_command_name(tokens) in {"python", "python3"} and len(tokens) >= 2:
        candidate = tokens[1]
    if not candidate:
        return False
    expected = Path(__file__).with_name("decision-checkpoint.py").resolve()
    return Path(candidate).expanduser().resolve() == expected


def git_subcommand(tokens: list[str]) -> str:
    tokens = normalize_command_tokens(tokens)
    if not tokens or first_command_name(tokens) != "git":
        return ""
    for token in tokens[1:]:
        if not token.startswith("-"):
            return token
    return ""


def segment_is_read_only(tokens: list[str]) -> bool:
    tokens = normalize_command_tokens(tokens)
    if not tokens or checkpoint_command(tokens):
        return True
    command = first_command_name(tokens)
    if command not in READ_ONLY_COMMANDS:
        return False
    if command == "git":
        return git_subcommand(tokens) in READ_ONLY_GIT
    if command == "find" and any(token in {"-delete", "-exec", "-execdir", "-ok", "-okdir"} for token in tokens):
        return False
    if command == "sed" and any(token == "-i" or token.startswith("-i") for token in tokens[1:]):
        return False
    return True


def shell_requires_checkpoint(command: str) -> bool:
    if not command:
        return False
    tokens = shell_tokens(command)
    if tokens is None:
        return True
    if any(token in {">", ">>", "<", "<<"} for token in tokens) or "\n" in command or "\r" in command:
        return True
    segments = split_segments(command)
    if segments is None:
        return True
    return any(not segment_is_read_only(segment) for segment in segments)


def requires_checkpoint(payload: dict) -> bool:
    name = tool_name(payload)
    inputs = tool_input(payload)
    if "apply_patch" in name or "apply-patch" in name or "patch" in inputs:
        return True
    if name == "bash" or "command" in inputs or "cmd" in inputs:
        command = inputs.get("command") or inputs.get("cmd") or ""
        return shell_requires_checkpoint(command if isinstance(command, str) else "")
    return False


def valid_checkpoint(value: object) -> bool:
    if not isinstance(value, dict) or value.get("schemaVersion") != 1:
        return False
    transition = value.get("transition")
    basis = value.get("basis")
    decision_key = value.get("decisionKey")
    evidence = value.get("evidence")
    if transition not in ALLOWED_BASES or basis not in ALLOWED_BASES[transition]:
        return False
    if not isinstance(decision_key, str) or not decision_key.strip():
        return False
    if not isinstance(evidence, list) or not all(isinstance(item, str) for item in evidence):
        return False
    return transition not in {"REVISE", "SUSPEND"} or bool(evidence)


def checkpoint_execution_output(item: object) -> str:
    if not isinstance(item, dict) or item.get("type") != "CommandExecution":
        return ""
    if item.get("status") != "completed" or item.get("exit_code") != 0:
        return ""
    command = item.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(token, str) for token in command):
        return ""
    if first_command_name(command) in {"sh", "bash", "zsh", "dash", "ksh"}:
        if len(command) != 3 or command[1] not in {"-c", "-lc"}:
            return ""
        segments = split_segments(command[2])
        if segments is None or len(segments) != 1 or not checkpoint_command(segments[0]):
            return ""
    elif not checkpoint_command(command):
        return ""
    stdout = item.get("stdout")
    return stdout if isinstance(stdout, str) else ""


def current_turn_has_checkpoint(transcript_path: str) -> bool:
    if not transcript_path:
        return False
    try:
        transcript = Path(transcript_path).open(encoding="utf-8")
    except (OSError, UnicodeError):
        return False

    found = False
    try:
        with transcript:
            for line in transcript:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                payload = entry.get("payload")
                if not isinstance(payload, dict):
                    continue
                if entry.get("type") == "response_item" and payload.get("type") == "message" and payload.get("role") == "user":
                    found = False
                    continue
                if entry.get("type") != "event_msg" or payload.get("type") != "item_completed":
                    continue
                stdout = checkpoint_execution_output(payload.get("item"))
                for match in MARKER_RE.finditer(stdout):
                    try:
                        candidate = json.loads(match.group(1))
                    except json.JSONDecodeError:
                        continue
                    if valid_checkpoint(candidate):
                        found = True
    except UnicodeError:
        return False
    return found


def main() -> None:
    payload = load_payload(sys.stdin)
    if payload is None:
        return
    if is_invalid_payload(payload):
        deny("Blocked invalid hook payload.")
    if not requires_checkpoint(payload):
        return
    if not current_turn_has_checkpoint(str(payload.get("transcript_path") or "")):
        checkpoint_path = Path(__file__).with_name("decision-checkpoint.py")
        deny(
            "Blocked write-bearing tool call without a decision checkpoint for the current user turn. "
            f"Run /usr/bin/python3 {checkpoint_path} --decision-key <key> "
            "--transition NEW|HOLD|REVISE|SUSPEND --basis <basis> "
            "[--evidence <reference>], then retry. Allowed bases: NEW=initial; "
            "HOLD=current-contract|evidence-reviewed; "
            "REVISE=new-evidence|contract-change|objective-change|proven-error; "
            "SUSPEND=evidence-conflict."
        )


if __name__ == "__main__":
    main()
