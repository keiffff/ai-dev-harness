#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

from hook_utils import is_invalid_payload, load_payload


BROWSER_APPROVAL_LINE = "browser-control: allow"


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


def browser_access(code: str) -> str:
    """Classify documented selectors, not arbitrary JavaScript execution."""
    remaining = code
    iab = False
    selectors = (
        r"\bcua\s*\.\s*createBrowserTab\s*\(\s*(['\"])iab\1\s*,",
        r"\bcua\s*\.\s*getTab\s*\(\s*[^,()]+,\s*\{\s*browser\s*:\s*(['\"])iab\1\s*,?\s*\}\s*\)",
        r"\.\s*browsers\s*\.\s*get\s*\(\s*(['\"])iab\1\s*\)",
    )
    selectors += (
        r"\bcua\s*\.\s*getBrowser\s*\(\s*\{\s*id\s*:\s*(['\"])iab\1\s*,?\s*\}\s*\)",
        r"\bcua\s*\.\s*listTabs\s*\(\s*\{\s*browser\s*:\s*(['\"])iab\1\s*(?:,\s*emit\s*:\s*(?:true|false)\s*)?,?\s*\}\s*\)",
    )
    for pattern in selectors:
        remaining, count = re.subn(pattern, "", remaining)
        iab = iab or bool(count)
    # Reject unknown/default selectors, inventory, selector aliases, and cells
    # mixing IAB with another target. Follow-up tab operations use the same REPL.
    if re.search(r"\bcua\b|\.\s*browsers\b", remaining):
        return "restricted"
    if iab:
        return "iab"
    if "browser-client.mjs" in code or "setupBrowserRuntime" in code:
        return "bootstrap"
    return "none"


def repl_server(tool_name: str) -> str:
    return "cua_repl" if "cua_repl" in tool_name else "node_repl"


def transcript_context(transcript_path: str, server: str) -> tuple[str, bool, bool]:
    if not transcript_path:
        return "", False, False
    try:
        transcript = Path(transcript_path).open(encoding="utf-8")
    except (OSError, UnicodeError):
        return "", False, False

    latest_message = ""
    browser_runtime_seen = False
    iab_selected = False
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
                if item.get("type") != "McpToolCall" or item.get("server") != server:
                    continue
                if item.get("tool") == "js_reset":
                    browser_runtime_seen = iab_selected = False
                    continue
                if item.get("tool") != "js":
                    continue
                arguments = item.get("arguments")
                if isinstance(arguments, dict):
                    access = browser_access(str(arguments.get("code") or ""))
                    if access != "none":
                        browser_runtime_seen = True
                        iab_selected = access == "iab"
    except UnicodeError:
        return "", True, False
    return latest_message, browser_runtime_seen, iab_selected


def explicitly_requests_browser(message: str) -> bool:
    approval = BROWSER_APPROVAL_LINE.casefold()
    return any(line.strip().casefold() == approval for line in message.splitlines())


def main() -> None:
    payload = load_payload(sys.stdin)
    if payload is None:
        return
    if is_invalid_payload(payload):
        deny("Blocked invalid hook payload.")
    tool_name = invoked_tool_name(payload)
    if tool_name.endswith("js_reset"):
        return
    code = extract_code(payload)
    access = browser_access(code)
    message, browser_runtime_seen, iab_selected = transcript_context(
        str(payload.get("transcript_path") or ""), repl_server(tool_name)
    )
    if access in {"iab", "bootstrap"} or (access == "none" and iab_selected):
        return
    if "cua_repl" not in tool_name and access == "none" and not browser_runtime_seen:
        return
    if not explicitly_requests_browser(message):
        deny(
            "Blocked non-IAB or unverified Browser/CUA access. "
            "Use an explicit iab selector; do not access the user's browser. "
            "In-app browser use does not require an approval line."
        )


if __name__ == "__main__":
    main()
