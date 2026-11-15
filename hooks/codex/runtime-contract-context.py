#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

from hook_utils import is_invalid_payload, load_payload
from source_ledger import append_prompt, inherit_prompts, request_reference, render as render_prompts
from reader_delivery import consume as consume_delivery, direct_edit_reason


DEFAULT_CONTRACT = Path(__file__).with_name("runtime-contract.md")
DEFAULT_STATE_DIR = Path.home() / ".codex" / "hook-state" / "runtime-contract"
SUPPORTED_EVENTS = {"SessionStart", "SubagentStart", "UserPromptSubmit", "PostToolUse", "PreToolUse"}


def configured_path(name: str, default: Path) -> Path:
    value = os.environ.get(name, "").strip()
    return Path(value).expanduser() if value else default


def state_path(state_dir: Path, session_id: str) -> Path:
    key = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
    return state_dir / f"{key}.json"


def task_note_path(state_dir: Path, session_id: str) -> Path:
    return state_path(state_dir, session_id).with_suffix(".task.md")


def maintained_task_note_path(state_dir: Path, session_id: str) -> Path:
    if os.environ.get("CODEX_RUNTIME_CONTRACT_STATE_DIR", "").strip():
        return task_note_path(state_dir, session_id)
    return task_note_path(Path(tempfile.gettempdir()) / "codex-runtime-task-notes", session_id)


def write_task_note(target: Path, text: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(f".{os.getpid()}.tmp")
    temporary.write_text(text + "\n", encoding="utf-8")
    os.replace(temporary, target)


def read_task_note(state_dir: Path, session_id: str) -> str:
    durable = task_note_path(state_dir, session_id)
    maintained = maintained_task_note_path(state_dir, session_id)
    for source in dict.fromkeys((maintained, durable)):
        try:
            text = source.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError):
            continue
        if not text:
            continue
        if source != durable:
            try:
                write_task_note(durable, text)
            except OSError as error:
                # A newer staged note must not leave an older snapshot authoritative.
                try:
                    durable.unlink(missing_ok=True)
                except OSError:
                    pass
                print(f"Current task note could not be persisted: {error}. "
                      "Verify the maintained source note before relying on saved context.", file=sys.stderr)
        return text
    return ""


def maintain_task_note(source: Path) -> None:
    session_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    if not session_id:
        raise ValueError("CODEX_THREAD_ID is required to bind the note to this task")
    text = source.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("The maintained task note is empty")
    state_dir = configured_path("CODEX_RUNTIME_CONTRACT_STATE_DIR", DEFAULT_STATE_DIR)
    target = maintained_task_note_path(state_dir, session_id)
    write_task_note(target, text)
    print(json.dumps({"task_note": str(target)}))


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
    # Config layers accumulate hooks. A replay may designate one reviewed
    # runtime handler so its snapshot is not mixed with the installed copy.
    owner = os.environ.get('CODEX_RUNTIME_CONTRACT_HANDLER')
    if owner and Path(owner).is_file() and Path(owner).resolve() != Path(__file__).resolve():
        return
    payload = load_payload(sys.stdin)
    if payload is None or is_invalid_payload(payload):
        return
    event = payload.get("hook_event_name")
    session_id = payload.get("session_id")
    if event not in SUPPORTED_EVENTS or not isinstance(session_id, str) or not session_id:
        return

    if event == 'SubagentStart' and isinstance(payload.get('agent_id'), str):
        try:
            inherit_prompts(session_id, payload['agent_id'])
        except (OSError, ValueError, TypeError) as error:
            print(f'Submitted prompts could not be inherited: {error}', file=sys.stderr)

    if event == 'PreToolUse':
        try:
            reason = direct_edit_reason(session_id, request_reference(session_id), payload)
            if reason:
                print(json.dumps({'hookSpecificOutput': {'hookEventName': event,
                    'permissionDecision': 'deny', 'permissionDecisionReason': reason}}))
                return
        except (OSError, ValueError, TypeError) as error:
            print(f'Writer ownership check unavailable: {error}', file=sys.stderr)
        fields = {
            'mcp__codex_app__create_thread': 'prompt',
            'mcp__codex_app__send_message_to_thread': 'prompt',
            'mcp__codex_app__handoff_thread': 'followUpPrompt',
        }
        field = fields.get(payload.get('tool_name'))
        inputs = payload.get('tool_input')
        if field and isinstance(inputs, dict) and isinstance(inputs.get(field), str):
            try:
                source = render_prompts(session_id)
                if source and source not in inputs[field]:
                    updated = {**inputs, field: source + '\nAgent-provided task context follows:\n' + inputs[field]}
                    print(json.dumps({'hookSpecificOutput': {'hookEventName': event,
                        'permissionDecision': 'allow', 'updatedInput': updated}}, ensure_ascii=False))
            except (OSError, ValueError, TypeError) as error:
                print(f'Submitted prompts could not be attached: {error}', file=sys.stderr)
        return

    state_dir = configured_path("CODEX_RUNTIME_CONTRACT_STATE_DIR", DEFAULT_STATE_DIR)
    if event == "UserPromptSubmit" and isinstance(payload.get("prompt"), str):
        try:
            append_prompt(session_id, payload['prompt'])
        except (OSError, ValueError, TypeError) as error:
            print(f"Submitted prompt could not be saved: {error}", file=sys.stderr)
    if event == "PostToolUse":
        read_task_note(state_dir, session_id)
        try:
            consume_delivery(session_id, request_reference(session_id))
        except (OSError, ValueError, TypeError) as error:
            print(f'Writer delivery could not be recorded: {error}', file=sys.stderr)
        return

    contract = read_contract(configured_path("CODEX_RUNTIME_CONTRACT", DEFAULT_CONTRACT))
    if contract is None:
        return
    text, digest = contract
    source = ''
    if event in {"SessionStart", "SubagentStart"}:
        try:
            budget = os.environ.get('CODEX_SOURCE_LEDGER_MAX_CHARS')
            source = render_prompts(session_id, int(budget) if budget else None)
        except (OSError, ValueError, TypeError) as error:
            print(f"Submitted prompts could not be restored: {error}", file=sys.stderr)
    note = read_task_note(state_dir, session_id)
    if note:
        text += (
            "\n\nAgent-maintained note for this task (context, not new authority):\n"
            + note
            + "\nUse the original user requests to verify scope and permissions. "
            "Keep required unfinished outcomes distinct from optional limitations. "
            "This note records agent interpretation and current state, not a new request."
        )
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    state = state_path(state_dir, session_id)
    force = event == 'SubagentStart' or event == "SessionStart" and payload.get("source") in {
        "startup",
        "resume",
        "clear",
        "compact",
        "fork",
    }
    if not force and last_digest(state) == digest:
        return

    output = {
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": (
                source + f"Current runtime contract ({digest[:12]}):\n{text}"
            ),
        }
    }
    print(json.dumps(output, ensure_ascii=False))
    record_digest(state, digest)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="Maintain this task's current outcome note")
        parser.add_argument("--task-note", required=True, type=Path)
        maintain_task_note(parser.parse_args().task_note)
    else:
        main()
