#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from hook_utils import is_invalid_payload, load_payload


DEFAULT_CONTRACT = Path(__file__).with_name("runtime-contract.md")
DEFAULT_STATE_DIR = Path.home() / ".codex" / "hook-state" / "runtime-contract"
SUPPORTED_EVENTS = {"SessionStart", "UserPromptSubmit"}


def configured_path(name: str, default: Path) -> Path:
    value = os.environ.get(name, "").strip()
    return Path(value).expanduser() if value else default


def state_path(state_dir: Path, session_id: str) -> Path:
    key = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
    return state_dir / f"{key}.json"


def read_contract(path: Path) -> tuple[str, str] | None:
    try:
        text = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return None
    if not text:
        return None
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return text, digest


def last_digest(path: Path) -> str:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return ""
    return value.get("digest", "") if isinstance(value, dict) else ""


def record_digest(path: Path, digest: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(f".{os.getpid()}.tmp")
        temporary.write_text(json.dumps({"digest": digest}, sort_keys=True), encoding="utf-8")
        os.replace(temporary, path)
    except OSError:
        pass


def main() -> None:
    payload = load_payload(sys.stdin)
    if payload is None or is_invalid_payload(payload):
        return
    event = payload.get("hook_event_name")
    session_id = payload.get("session_id")
    if event not in SUPPORTED_EVENTS or not isinstance(session_id, str) or not session_id:
        return

    contract = read_contract(configured_path("CODEX_RUNTIME_CONTRACT", DEFAULT_CONTRACT))
    if contract is None:
        return
    text, digest = contract
    state = state_path(
        configured_path("CODEX_RUNTIME_CONTRACT_STATE_DIR", DEFAULT_STATE_DIR),
        session_id,
    )
    force = event == "SessionStart" and payload.get("source") in {
        "startup",
        "resume",
        "clear",
        "compact",
    }
    if not force and last_digest(state) == digest:
        return

    output = {
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": (
                f"Current runtime contract ({digest[:12]}):\n{text}"
            ),
        }
    }
    print(json.dumps(output, ensure_ascii=False))
    record_digest(state, digest)


if __name__ == "__main__":
    main()
