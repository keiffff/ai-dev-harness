import json
import os
import shlex

CONTROL_TOKENS = {";", "&&", "||", "|", "&"}
GROUPING_TOKENS = {"(", ")", "{", "}"}
WRAPPER_COMMANDS = {"command", "exec"}
SHELL_INTERPRETERS = {"sh", "bash", "zsh", "dash", "ksh", "fish"}
UNSAFE_WRAPPERS = {"sudo", "xargs"}
ENV_ALLOWED_OPTIONS = {"-i", "-0", "--ignore-environment", "--null"}
INVALID_PAYLOAD_KEY = "__invalid_hook_payload__"


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        for key in ("command", "cmd"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
        args = tool_input.get("args")
        if isinstance(args, list) and all(isinstance(v, str) for v in args):
            return shlex.join(args)
    for key in ("command", "cmd"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return ""


def load_payload(stdin) -> dict | None:
    raw = stdin.read()
    if not raw.strip():
        return None
    try:
        value = json.loads(raw)
    except Exception:
        return {INVALID_PAYLOAD_KEY: True}
    return value if isinstance(value, dict) else {INVALID_PAYLOAD_KEY: True}


def is_invalid_payload(payload: dict) -> bool:
    return payload.get(INVALID_PAYLOAD_KEY) is True


def shell_tokens(command: str) -> list[str] | None:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError:
        return None


def split_segments(command: str) -> list[list[str]] | None:
    tokens = shell_tokens(command)
    if tokens is None:
        return None
    return _split_segments_from_tokens(tokens)


def _split_segments_from_tokens(tokens: list[str]) -> list[list[str]]:
    segments = []
    current = []
    for token in tokens:
        if token in CONTROL_TOKENS:
            if current:
                segments.append(current)
                current = []
            continue
        current.append(token)
    if current:
        segments.append(current)
    return segments


def unsafe_shell_reason(command: str) -> str | None:
    if not command:
        return None
    if "\n" in command or "\r" in command:
        return "Blocked multiline shell command."
    if "$" + "(" in command or "`" in command or "<" + "(" in command or ">" + "(" in command:
        return "Blocked shell command substitution or process substitution."
    tokens = shell_tokens(command)
    if tokens is None:
        return "Blocked malformed shell command."
    if any(token in GROUPING_TOKENS for token in tokens):
        return "Blocked shell grouping."
    for segment in _split_segments_from_tokens(tokens):
        reason = unsafe_segment_reason(segment)
        if reason:
            return reason
    return None


def unsafe_segment_reason(tokens: list[str]) -> str | None:
    raw_tokens = strip_env_assignments(tokens)
    if raw_tokens and command_name(raw_tokens[0]) == "env":
        reason = _env_reason(raw_tokens[1:])
        if reason:
            return reason

    normalized = normalize_command_tokens(tokens)
    if not normalized:
        return None
    first = command_name(normalized[0])
    if first in SHELL_INTERPRETERS:
        return "Blocked shell interpreter execution."
    if first in UNSAFE_WRAPPERS:
        return f"Blocked unsafe command wrapper: {first}."
    if first == "env":
        return _env_reason(normalized[1:]) or "Blocked unsupported env wrapper."
    return None


def command_name(token: str) -> str:
    return os.path.basename(token)


def strip_env_assignments(tokens: list[str]) -> list[str]:
    i = 0
    while i < len(tokens) and _is_env_assignment(tokens[i]):
        i += 1
    return tokens[i:]


def normalize_command_tokens(tokens: list[str]) -> list[str]:
    tokens = strip_env_assignments(tokens)
    changed = True
    while changed and tokens:
        changed = False
        name = command_name(tokens[0])
        if name in WRAPPER_COMMANDS:
            tokens = tokens[1:]
            changed = True
            continue
        if name == "env":
            stripped = _strip_env(tokens[1:])
            if stripped is None:
                return tokens
            tokens = stripped
            changed = True
    return tokens


def first_command_name(tokens: list[str]) -> str:
    normalized = normalize_command_tokens(tokens)
    return command_name(normalized[0]) if normalized else ""


def is_approved_wrapper_segment(tokens: list[str], approved_wrapper: str) -> bool:
    normalized = normalize_command_tokens(tokens)
    return bool(normalized) and normalized[0] == approved_wrapper


def _is_env_assignment(token: str) -> bool:
    if "=" not in token:
        return False
    name = token.split("=", 1)[0]
    return bool(name) and name.replace("_", "A").isalnum() and not name[0].isdigit()


def _env_reason(tokens: list[str]) -> str | None:
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if _is_env_assignment(token):
            i += 1
            continue
        if token in ENV_ALLOWED_OPTIONS:
            i += 1
            continue
        if token.startswith("-"):
            return f"Blocked unsupported env option: {token}."
        break
    if i < len(tokens) and command_name(tokens[i]) in SHELL_INTERPRETERS | UNSAFE_WRAPPERS:
        return "Blocked env wrapping an unsafe command."
    return None


def _strip_env(tokens: list[str]) -> list[str] | None:
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if _is_env_assignment(token) or token in ENV_ALLOWED_OPTIONS:
            i += 1
            continue
        if token.startswith("-"):
            return None
        return tokens[i:]
    return []
