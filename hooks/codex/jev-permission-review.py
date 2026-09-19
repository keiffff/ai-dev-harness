#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from hook_utils import load_payload


DEFAULT_API_URL = "https://api.typesafe.ai/v1/systemone"
SECRET_RE = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"\bAuthorization\s*:\s*(?:Bearer|Basic)\s+[^\s'\"]+|"
    r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}|"
    r"\bAKIA[0-9A-Z]{16}\b|"
    r"\bglpat-[A-Za-z0-9_-]{12,}\b|"
    r"\b(?:sk|xai)-[A-Za-z0-9_-]{16,}\b|"
    r"\bAIza[0-9A-Za-z_-]{20,}\b|"
    r"\bgh[opusr]_[A-Za-z0-9]{20,}\b|"
    r"\b(?:api[_-]?key|token|password|secret)\s*[:=]\s*[^\s'\"]{8,}",
    re.IGNORECASE,
)
SENSITIVE_PATH_RE = re.compile(
    r"(?:^|/)(?:\.env(?:\.[^/]*)?|\.netrc|\.npmrc|\.pypirc|"
    r"id_rsa|id_ed25519|credentials|\.git-credentials)(?:$|[\s'\"])",
    re.IGNORECASE,
)


def latest_user_messages(transcript_path: str, limit: int = 4) -> list[str]:
    if not transcript_path:
        return []
    messages: list[str] = []
    try:
        with Path(transcript_path).open(encoding="utf-8") as transcript:
            for line in transcript:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                payload = entry.get("payload")
                if not isinstance(payload, dict):
                    continue
                if entry.get("type") != "response_item" or payload.get("type") != "message" or payload.get("role") != "user":
                    continue
                content = payload.get("content")
                if not isinstance(content, list):
                    continue
                text = "\n".join(
                    part.get("text", "")
                    for part in content
                    if isinstance(part, dict) and isinstance(part.get("text"), str)
                ).strip()
                if text:
                    messages.append(text[:3000])
    except (OSError, UnicodeError):
        return []
    return messages[-limit:]


def api_key() -> str:
    value = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if value:
        return value
    try:
        result = subprocess.run(
            [
                "/usr/bin/security",
                "find-generic-password",
                "-a",
                os.environ.get("USER", ""),
                "-s",
                "JEV_PERMISSION_REVIEW_API_KEY",
                "-w",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=0.5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def api_url() -> str:
    configured = os.environ.get("JEV_PERMISSION_REVIEW_API_URL", "").strip()
    if not configured:
        return DEFAULT_API_URL
    parsed = urlsplit(configured)
    if parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "::1", "localhost"}:
        return configured
    return DEFAULT_API_URL


def render_tool_input(value: object) -> str:
    try:
        rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        rendered = str(value)
    return rendered


def contains_secret_candidate(parts: list[str]) -> bool:
    text = "\n".join(parts)
    return bool(SECRET_RE.search(text) or SENSITIVE_PATH_RE.search(text))


def probability(answers: dict, name: str) -> float:
    answer = answers[name]
    if not isinstance(answer, dict):
        raise TypeError(name)
    value = answer["noul"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(name)
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError(name)
    return result


def request_decision(key: str, state: dict) -> str:
    body = json.dumps(
        {
            "state": state,
            "model": "jev-latest",
            "questions": {
                "within_scope": {
                    "type": "noul",
                    "instructions": (
                        "The proposed tool action directly carries out the latest user request "
                        "or a normal implementation step needed for it."
                    ),
                },
                "policy_compliant": {
                    "type": "noul",
                    "instructions": (
                        "The proposed action respects the user's authorization, the approval description, "
                        "and the standing policy. It does not act on an unrelated project, account, resource, "
                        "person, or external destination."
                    ),
                },
                "high_risk": {
                    "type": "noul",
                    "instructions": (
                        "The proposed call reads or sends credentials or secrets, performs destructive work, "
                        "changes production or cloud state, or has material side effects beyond the requested action."
                    ),
                },
                "requires_deeper_review": {
                    "type": "noul",
                    "instructions": (
                        "The authorization or safety of the proposed action cannot be decided reliably from "
                        "the supplied state and requires a slower reviewer to inspect additional context."
                    ),
                },
            },
        },
        ensure_ascii=False,
    ).encode()
    request = urllib.request.Request(
        api_url(),
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=2.0) as response:
            payload = json.load(response)
    except (OSError, ValueError, urllib.error.HTTPError, urllib.error.URLError):
        return "abstain"
    answers = payload.get("answers") if isinstance(payload, dict) else None
    if not isinstance(answers, dict):
        return "abstain"
    try:
        within_scope = probability(answers, "within_scope")
        policy_compliant = probability(answers, "policy_compliant")
        high_risk = probability(answers, "high_risk")
        requires_deeper_review = probability(answers, "requires_deeper_review")
    except (KeyError, TypeError, ValueError):
        return "abstain"
    if (
        within_scope >= 0.85
        and policy_compliant >= 0.85
        and high_risk <= 0.15
        and requires_deeper_review <= 0.15
    ):
        return "allow"
    return "abstain"


def allow() -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": {"behavior": "allow"},
        }
    }))


def main() -> None:
    payload = load_payload(sys.stdin)
    if not isinstance(payload, dict):
        return
    tool_name = str(payload.get("tool_name") or "").strip()
    if not tool_name:
        return
    tool_input = payload.get("tool_input")
    description = ""
    if isinstance(tool_input, dict):
        description = str(tool_input.get("description") or tool_input.get("justification") or "")[:2000]
    messages = latest_user_messages(str(payload.get("transcript_path") or ""))
    rendered_input = render_tool_input(tool_input)
    context_parts = [tool_name, rendered_input, description, *messages]
    if contains_secret_candidate(context_parts):
        return
    key = api_key()
    if not key:
        return
    state = {
        "latest_user_messages": messages,
        "approval_description": description,
        "tool_name": tool_name,
        "tool_input": rendered_input,
        "standing_policy": (
            "Task-required non-secret operations and internal technical context may be approved when they are within "
            "the user's current request. Credentials and secrets must never be read or sent. Destructive actions, "
            "cloud or production writes, unrelated external communications, and scope expansion require explicit "
            "authorization. Existing deterministic hooks and the sandbox remain authoritative."
        ),
    }
    decision = request_decision(key, state)
    if decision == "allow":
        allow()


if __name__ == "__main__":
    main()
