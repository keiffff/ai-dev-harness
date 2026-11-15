"""Historical message roles must survive the replay container serialization."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReplayHookTests(unittest.TestCase):
    def test_original_events_not_quoted_assistant_history_become_saved_requests(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root/'events.json'
            container = 'Frozen history: assistant suggested an extra condition. Current request follows.'
            prompts = ['Explain the observed behavior.', 'Prepare its short report.']
            fixture.write_text(json.dumps({'actor_input_sha256': hashlib.sha256(container.encode()).hexdigest(),
                                           'submitted_prompts': prompts}))
            receipt = root/'receipt.json'
            env = dict(os.environ, CODEX_SOURCE_LEDGER_DIR=str(root/'ledger'),
                       CODEX_RUNTIME_CONTRACT_STATE_DIR=str(root/'state'))
            env.pop('CODEX_RUNTIME_CONTRACT_HANDLER', None)
            command = [sys.executable, str(ROOT/'evals/instruction-load/replay_hook.py'),
                       '--handler', str(ROOT/'hooks/codex/runtime-contract-context.py'),
                       '--fixture', str(fixture), '--receipt', str(receipt)]
            def send(text):
                return subprocess.run(command, input=json.dumps({'hook_event_name': 'UserPromptSubmit',
                    'session_id': 'synthetic', 'prompt': text}), text=True, capture_output=True, env=env)
            result = send(container)
            self.assertEqual(result.returncode, 0, result.stderr)
            file = next((root/'ledger').glob('*.jsonl'))
            records = [json.loads(line) for line in file.read_text().splitlines()]
            self.assertEqual([r['text'] for r in records], prompts)
            self.assertNotIn('assistant suggested', file.read_text())
            self.assertEqual(json.loads(receipt.read_text())['current_prompt_sha256'],
                             hashlib.sha256(prompts[-1].encode()).hexdigest())
            later = send('Change only the label.')
            self.assertEqual(later.returncode, 0, later.stderr)
            self.assertEqual(json.loads(file.read_text().splitlines()[-1])['text'], 'Change only the label.')


if __name__ == '__main__':
    unittest.main()
