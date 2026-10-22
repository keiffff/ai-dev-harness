import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "codex" / "runtime-contract-context.py"
HOOK_DIR = ROOT / "hooks" / "codex"


class RuntimeContractContextTests(unittest.TestCase):
    def run_hook(self, contract, state_dir, payload):
        contract_path = Path(state_dir).parent / "runtime-contract.md"
        contract_path.write_text(contract, encoding="utf-8")
        env = os.environ.copy()
        env.update({
            "PYTHONPATH": str(HOOK_DIR),
            "CODEX_RUNTIME_CONTRACT": str(contract_path),
            "CODEX_RUNTIME_CONTRACT_STATE_DIR": str(state_dir),
        })
        return subprocess.run(
            ["python3", str(HOOK)],
            input=json.dumps(payload),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )

    def test_injects_once_then_reinjects_after_contract_change(self):
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory) / "state"
            payload = {
                "session_id": "session-a",
                "hook_event_name": "UserPromptSubmit",
                "prompt": "continue",
            }
            first = self.run_hook("first contract", state_dir, payload)
            second = self.run_hook("first contract", state_dir, payload)
            changed = self.run_hook("second contract", state_dir, payload)

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("first contract", json.loads(first.stdout)["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(second.stdout, "")
        self.assertIn("second contract", json.loads(changed.stdout)["hookSpecificOutput"]["additionalContext"])

    def test_sessions_receive_contract_independently(self):
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory) / "state"
            outputs = []
            for session_id in ("session-a", "session-b"):
                outputs.append(self.run_hook("shared contract", state_dir, {
                    "session_id": session_id,
                    "hook_event_name": "UserPromptSubmit",
                    "prompt": "continue",
                }))

        self.assertTrue(all("shared contract" in result.stdout for result in outputs))

    def test_compaction_reinjects_the_same_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory) / "state"
            prompt = self.run_hook("stable contract", state_dir, {
                "session_id": "session-a",
                "hook_event_name": "UserPromptSubmit",
                "prompt": "continue",
            })
            compact = self.run_hook("stable contract", state_dir, {
                "session_id": "session-a",
                "hook_event_name": "SessionStart",
                "source": "compact",
            })

        self.assertIn("stable contract", prompt.stdout)
        self.assertIn("stable contract", compact.stdout)

    def test_malformed_or_missing_input_is_non_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory) / "state"
            malformed = self.run_hook("contract", state_dir, "not-an-object")
            unsupported = self.run_hook("contract", state_dir, {
                "session_id": "session-a",
                "hook_event_name": "PostToolUse",
            })

        self.assertEqual(malformed.returncode, 0)
        self.assertEqual(malformed.stdout, "")
        self.assertEqual(unsupported.returncode, 0)
        self.assertEqual(unsupported.stdout, "")

    def test_dynamodb_read_exception_is_aligned_and_reaches_existing_session(self):
        agents = (ROOT / 'codex' / 'AGENTS.md').read_text(encoding='utf-8')
        contract = (HOOK_DIR / 'runtime-contract.md').read_text(encoding='utf-8')
        self.assertIn('DynamoDBの読み取りはAWS readonly wrapper経由で許可', agents)
        self.assertIn('リモートDBへの書き込み・削除・構成変更', agents)
        self.assertIn('それ以外のリモートDB操作', agents)
        self.assertIn('DynamoDB reads are allowed through the AWS readonly wrapper', contract)
        self.assertIn('remote DB writes, deletes or configuration changes', contract)
        self.assertIn('Other remote DB operations remain prohibited', contract)
        self.assertNotIn('secret access or remote DB operations.', contract)
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory) / 'state'
            payload = {'session_id': 'existing-session', 'hook_event_name': 'UserPromptSubmit', 'prompt': 'continue'}
            old = self.run_hook('No remote DB operations.', state_dir, payload)
            changed = self.run_hook(contract, state_dir, payload)
            repeated = self.run_hook(contract, state_dir, payload)
        self.assertEqual(old.returncode, 0, old.stderr)
        self.assertEqual(changed.returncode, 0, changed.stderr)
        injected = json.loads(changed.stdout)['hookSpecificOutput']['additionalContext']
        self.assertIn(contract.strip(), injected)
        self.assertEqual(repeated.stdout, '')


if __name__ == "__main__":
    unittest.main()
