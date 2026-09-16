#!/usr/bin/env python3
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional

DEFAULT_STATE_DIR = Path.home() / ".codex" / "hook-state" / "compaction-handoff"
STATE_DIR_ENV = "CODEX_HANDOFF_STATE_DIR"
REMINDER = (
    "This root task has compacted at least three times. At the next safe checkpoint, "
    "use `codex-thread-handoff` to assess context health. Compaction alone is not "
    "enough to suggest a handoff; require another independent degradation signal. "
    "Make at most one proactive handoff suggestion for this task. A general proposal must "
    "cover the whole root task; do not narrow "
    "it to the latest subproblem unless the user explicitly asks to split the work. "
    "Do not interrupt active commands, edits, tests, approvals, or unresolved failures. "
    "Do not create, fork, archive, or otherwise mutate a task without explicit user "
    "approval."
)


def load_payload() -> Optional[dict]:
    raw = sys.stdin.read()
    if not raw.strip():
        return None
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        return None
    return value if isinstance(value, dict) else None


def state_path(session_id: str) -> Path:
    state_dir = Path(os.environ.get(STATE_DIR_ENV, DEFAULT_STATE_DIR)).expanduser()
    session_key = hashlib.sha256(session_id.encode()).hexdigest()
    return state_dir / f"{session_key}.json"


def load_state(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError, TypeError):
        return {"compaction_count": 0, "reminder_emitted": False}
    if not isinstance(value, dict):
        return {"compaction_count": 0, "reminder_emitted": False}
    count = value.get("compaction_count", 0)
    if not isinstance(count, int) or count < 0:
        return {"compaction_count": 0, "reminder_emitted": False}
    raw_emitted = value.get("reminder_emitted")
    emitted = raw_emitted if isinstance(raw_emitted, bool) else count >= 2
    return {
        "compaction_count": count,
        "reminder_emitted": emitted,
    }


def save_state(path: Path, state: dict) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(f".{os.getpid()}.tmp")
        temporary.write_text(json.dumps(state))
        os.replace(temporary, path)
    except OSError:
        return False
    return True


def main() -> None:
    payload = load_payload()
    if payload is None:
        return
    if payload.get("hook_event_name") != "SessionStart" or payload.get("source") != "compact":
        return

    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return

    path = state_path(session_id)
    state = load_state(path)
    state["compaction_count"] += 1
    should_remind = state["compaction_count"] >= 3 and not state["reminder_emitted"]
    if should_remind:
        state["reminder_emitted"] = True
    if not save_state(path, state) or not should_remind:
        return

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": REMINDER,
        }
    }))


if __name__ == "__main__":
    main()
