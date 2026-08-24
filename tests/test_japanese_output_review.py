from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "hooks" / "codex" / "japanese-output-review.py"
HOOK_PYTHON = Path("/usr/bin/python3")
if not HOOK_PYTHON.exists():
    HOOK_PYTHON = Path(sys.executable)


def run_hook(state_dir: str, payload: dict | str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["CODEX_JAPANESE_OUTPUT_STATE_DIR"] = state_dir
    hook_input = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        [str(HOOK_PYTHON), str(SCRIPT)],
        input=hook_input,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )


def prompt_payload(prompt: str, session_id: str = "session-1", turn_id: str = "turn-1") -> dict:
    return {
        "hook_event_name": "UserPromptSubmit",
        "session_id": session_id,
        "turn_id": turn_id,
        "prompt": prompt,
    }


def stop_payload(message: str, active: bool = False, session_id: str = "session-1", turn_id: str = "turn-1") -> dict:
    return {
        "hook_event_name": "Stop",
        "session_id": session_id,
        "turn_id": turn_id,
        "stop_hook_active": active,
        "last_assistant_message": message,
    }


class JapaneseOutputReviewTests(unittest.TestCase):
    def test_blocks_first_japanese_prose_response_with_editing_instructions(self):
        with tempfile.TemporaryDirectory() as state_dir:
            result = run_hook(state_dir, stop_payload("調査結果です。運営側の設定を正本へ投影します。"))

        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["decision"], "block")
        self.assertIn("推敲後の回答だけ", output["reason"])
        self.assertIn("誰が何をどうするか", output["reason"])
        self.assertIn("「正本」", output["reason"])
        self.assertIn("「投影」", output["reason"])

    def test_allows_second_stop_after_one_continuation(self):
        with tempfile.TemporaryDirectory() as state_dir:
            result = run_hook(state_dir, stop_payload("自然な日本語です。", active=True))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_allows_non_prose_and_non_japanese_outputs(self):
        outputs = (
            "```python\nprint('こんにちは')\n```",
            '{"message":"こんにちは"}',
            "name,value\nfoo,1\nbar,2",
            "The change is ready.",
        )
        with tempfile.TemporaryDirectory() as state_dir:
            results = [run_hook(state_dir, stop_payload(output)) for output in outputs]

        for result in results:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_user_bypass_applies_only_to_matching_turn(self):
        with tempfile.TemporaryDirectory() as state_dir:
            submitted = run_hook(state_dir, prompt_payload("そのまま返して [ja-output-bypass]"))
            bypassed = run_hook(state_dir, stop_payload("日本語の回答です。"))
            next_turn = run_hook(state_dir, stop_payload("次の日本語回答です。", turn_id="turn-2"))

        self.assertEqual(submitted.returncode, 0, submitted.stderr)
        self.assertEqual(submitted.stdout, "")
        self.assertEqual(bypassed.stdout, "")
        self.assertEqual(json.loads(next_turn.stdout)["decision"], "block")

    def test_explicit_exact_output_request_is_exempt(self):
        with tempfile.TemporaryDirectory() as state_dir:
            run_hook(state_dir, prompt_payload("次の文章を一字一句そのまま出力してください"))
            result = run_hook(state_dir, stop_payload("指定された日本語です。"))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_negated_exact_output_phrase_does_not_exempt_review(self):
        with tempfile.TemporaryDirectory() as state_dir:
            run_hook(state_dir, prompt_payload("そのまま返すのではなく、自然な日本語に直してください"))
            result = run_hook(state_dir, stop_payload("修正した日本語です。"))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_reference_to_raw_data_does_not_exempt_review(self):
        with tempfile.TemporaryDirectory() as state_dir:
            run_hook(state_dir, prompt_payload("生データを要約して、コードだけではなく説明も付けてください"))
            result = run_hook(state_dir, stop_payload("要約した日本語です。"))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_invalid_empty_or_unrelated_input_fails_open(self):
        with tempfile.TemporaryDirectory() as state_dir:
            results = (
                run_hook(state_dir, "{not json"),
                run_hook(state_dir, ""),
                run_hook(state_dir, {"hook_event_name": "PreToolUse"}),
                run_hook(state_dir, stop_payload("")),
            )

        for result in results:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
