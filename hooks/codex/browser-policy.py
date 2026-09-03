#!/usr/bin/env python3
import json
import sys
from pathlib import Path

from hook_utils import is_invalid_payload, load_payload


BROWSER_APPROVAL_LINE = "browser-control: allow"
BROWSER_CODE_MARKERS = (
    "browser-client.mjs",
    "setupBrowserRuntime(",
    ".browsers.get(",
    ".browsers.getDefault(",
    ".browsers.getForUrl(",
    "cua.",
    "cua[",
)


def deny(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(2)


def extract_code(payload: dict) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        code = tool_input.get("code")
        if isinstance(code, str):
            return code
    return ""


def invoked_tool_name(payload: dict) -> str:
    for key in ("tool_name", "tool", "name"):
        value = payload.get(key)
        if isinstance(value, str):
            return value.casefold()
    return ""


def is_cua_tool(payload: dict) -> bool:
    return "cua_repl" in invoked_tool_name(payload)


def transcript_context(transcript_path: str) -> tuple[str, bool]:
    if not transcript_path:
        return "", False
    path = Path(transcript_path)
    try:
        transcript = path.open(encoding="utf-8")
    except (OSError, UnicodeError):
        return "", False

    latest_message = ""
    browser_runtime_seen = False
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
                    content = payload.get("content")
                    if isinstance(content, list):
                        texts = [part.get("text", "") for part in content if isinstance(part, dict) and isinstance(part.get("text"), str)]
                        latest_message = "\n".join(texts)
                    continue
                item = payload.get("item")
                if entry.get("type") != "event_msg" or not isinstance(item, dict):
                    continue
                if (
                    item.get("type") != "McpToolCall"
                    or item.get("server") not in {"node_repl", "cua_repl"}
                    or item.get("tool") != "js"
                ):
                    continue
                arguments = item.get("arguments")
                if isinstance(arguments, dict) and is_browser_code(str(arguments.get("code") or "")):
                    browser_runtime_seen = True
    except UnicodeError:
        return "", True
    return latest_message, browser_runtime_seen


def explicitly_requests_browser(message: str) -> bool:
    approval = BROWSER_APPROVAL_LINE.casefold()
    return any(line.strip().casefold() == approval for line in message.splitlines())


def is_browser_code(code: str) -> bool:
    compact = "".join(code.split())
    return any(marker in compact for marker in BROWSER_CODE_MARKERS)


def main() -> None:
    payload = load_payload(sys.stdin)
    if payload is None:
        return
    if is_invalid_payload(payload):
        deny("Blocked invalid hook payload.")

    message, browser_runtime_seen = transcript_context(str(payload.get("transcript_path") or ""))
    if not is_cua_tool(payload) and not is_browser_code(extract_code(payload)) and not browser_runtime_seen:
        return

    if not explicitly_requests_browser(message):
        deny(
            "Blocked Browser control because the latest user message did not include "
            f"the exact approval line: {BROWSER_APPROVAL_LINE}"
        )


if __name__ == "__main__":
    main()
