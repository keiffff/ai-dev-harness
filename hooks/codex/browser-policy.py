#!/usr/bin/env python3
import json
import sys
from pathlib import Path

from hook_utils import is_invalid_payload, load_payload


BROWSER_PLUGIN_MENTION = "plugin://browser@openai-bundled"
BROWSER_CODE_MARKERS = (
    "browser-client.mjs",
    "setupBrowserRuntime(",
    ".browsers.get(",
    ".browsers.getDefault(",
    ".browsers.getForUrl(",
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
                if item.get("type") != "McpToolCall" or item.get("server") != "node_repl" or item.get("tool") != "js":
                    continue
                arguments = item.get("arguments")
                if isinstance(arguments, dict) and is_browser_code(str(arguments.get("code") or "")):
                    browser_runtime_seen = True
    except UnicodeError:
        return "", True
    return latest_message, browser_runtime_seen


def explicitly_requests_browser(message: str) -> bool:
    return BROWSER_PLUGIN_MENTION in message.casefold()


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
    if not is_browser_code(extract_code(payload)) and not browser_runtime_seen:
        return

    if not explicitly_requests_browser(message):
        deny("Blocked Browser use because the latest user message did not explicitly request a browser.")


if __name__ == "__main__":
    main()
