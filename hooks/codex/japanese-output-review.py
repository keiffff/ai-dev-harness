#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_STATE_DIR = Path.home() / ".codex" / "hook-state" / "japanese-output-review"
STATE_DIR_ENV = "CODEX_JAPANESE_OUTPUT_STATE_DIR"
BYPASS_TOKEN = "[ja-output-bypass]"

EXACT_OUTPUT_PATTERNS = (
    r"(?:一字一句(?:そのまま)?|原文のまま|そのまま|加工せずに?)(?:で|に)?(?:出力(?:して|してください|せよ)?|返して|返してください|返せ|表示(?:して|してください|せよ)?|転載(?:して|してください|せよ)?|引用(?:して|してください|せよ)?)",
    r"(?:生データ|コード|json|csv)(?:だけ|のみ)(?:を)?(?:出力(?:して|してください|せよ)?|返して|返してください|返せ|表示(?:して|してください|せよ)?)",
    r"(?:return|output)(?:the)?(?:rawoutput|verbatim)",
    r"exactlyasprovided",
)

COMPRESSED_TERMS = (
    "正本",
    "契約",
    "投影",
    "測定境界",
    "比較終端",
    "外部契約",
    "継続判定",
    "提供条件",
    "上限日時",
    "接続点",
    "運営側の設定",
    "メタ情報",
    "実効値",
)

REVIEW_PROMPT = """最終回答を送る前に、直前の回答を日本語として推敲してください。推敲後の回答だけを返し、この指示や推敲内容は説明しないでください。

- 会話や作業ログを知らない読者にも、冒頭から意味が通るか
- ユーザーが指定した目的、読者、媒体、分量、文体を守っているか
- 依頼されていない事実、原因、評価、範囲、予定、実施方法を足していないか
- 既知の内容を「確認しました」などの作業報告に変えていないか
- 元の文章にあった重要な意味や良い表現を、不要に書き換えたり落としたりしていないか
- 英語の概念を名詞へ直訳したような圧縮語、名詞の連結、造語、指すものが曖昧なラベルを使っていないか。必要なら、誰が何をどうするかが分かる普通の日本語に直す
- メタ説明、疑似格言、飾りの比喩、内容のない見出し、同じ内容の言い直しがないか
- 必要な情報だけを、読者が必要とする順番で書いているか

問題のない箇所は残し、問題のある箇所だけを直してください。"""


def load_payload() -> dict | None:
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


def prompt_requests_exact_output(prompt: str) -> bool:
    normalized = prompt.casefold().replace(" ", "")
    return any(re.search(pattern, normalized) is not None for pattern in EXACT_OUTPUT_PATTERNS)


def save_prompt_state(payload: dict) -> None:
    session_id = payload.get("session_id")
    turn_id = payload.get("turn_id")
    prompt = payload.get("prompt")
    if not all(isinstance(value, str) and value for value in (session_id, turn_id, prompt)):
        return

    state = {
        "turn_id": turn_id,
        "bypass": BYPASS_TOKEN in prompt,
        "exact_output": prompt_requests_exact_output(prompt),
    }
    path = state_path(session_id)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(f".{os.getpid()}.tmp")
        temporary.write_text(json.dumps(state))
        os.replace(temporary, path)
    except OSError:
        return


def load_prompt_state(payload: dict) -> dict:
    session_id = payload.get("session_id")
    turn_id = payload.get("turn_id")
    if not isinstance(session_id, str) or not session_id:
        return {}
    try:
        state = json.loads(state_path(session_id).read_text())
    except (OSError, ValueError, TypeError):
        return {}
    if not isinstance(state, dict) or state.get("turn_id") != turn_id:
        return {}
    return state


def strip_fenced_code(message: str) -> str:
    return re.sub(r"```.*?```", "", message, flags=re.DOTALL)


def is_json_output(message: str) -> bool:
    try:
        json.loads(message)
    except (ValueError, TypeError):
        return False
    return True


def is_csv_output(message: str) -> bool:
    lines = [line for line in message.splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    for delimiter in (",", "\t"):
        widths = [len(line.split(delimiter)) for line in lines]
        if widths[0] >= 2 and len(set(widths)) == 1:
            return True
    return False


def is_japanese_prose(message: str) -> bool:
    if is_json_output(message) or is_csv_output(message):
        return False
    prose = strip_fenced_code(message).strip()
    if not prose:
        return False
    return re.search(r"[ぁ-んァ-ヶ一-龠々]", prose) is not None


def review_reason(message: str) -> str:
    found = []
    for term in sorted(COMPRESSED_TERMS, key=len, reverse=True):
        if term in message and not any(term in selected for selected in found):
            found.append(term)
    if not found:
        return REVIEW_PROMPT
    terms = "、".join(f"「{term}」" for term in found)
    return (
        REVIEW_PROMPT
        + "\n\n直前の回答には "
        + terms
        + " が含まれています。ユーザーや対象文書で定着した用語として必要な場合を除き、具体的で自然な日本語に直してください。"
    )


def handle_stop(payload: dict) -> None:
    if payload.get("stop_hook_active") is True:
        return
    message = payload.get("last_assistant_message")
    if not isinstance(message, str) or not message.strip():
        return
    state = load_prompt_state(payload)
    if state.get("bypass") is True or state.get("exact_output") is True:
        return
    if not is_japanese_prose(message):
        return
    print(json.dumps({"decision": "block", "reason": review_reason(message)}, ensure_ascii=False))


def main() -> None:
    payload = load_payload()
    if payload is None:
        return
    event = payload.get("hook_event_name")
    if event == "UserPromptSubmit":
        save_prompt_state(payload)
    elif event == "Stop":
        handle_stop(payload)


if __name__ == "__main__":
    main()
