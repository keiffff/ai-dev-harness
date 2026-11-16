"""Historical message roles must survive the replay container serialization."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import sqlite3

ROOT = Path(__file__).resolve().parents[1]


class ReplayHookTests(unittest.TestCase):
    def test_original_events_not_quoted_assistant_history_become_saved_requests(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root/'events.json'
            container = 'Frozen history: assistant suggested an extra condition. Current request follows.'
            prompts = ['Explain the observed behavior.', 'Prepare its short report.']
            history = [{'role':'user','text':prompts[0]},
                       {'role':'assistant','text':'Observed local output: the label is missing.'},
                       {'role':'user','text':prompts[-1]}]
            fixture.write_text(json.dumps({'actor_input_sha256': hashlib.sha256(container.encode()).hexdigest(),
                                           'submitted_prompts': prompts, 'history_messages':history}))
            receipt = root/'receipt.json'
            env = dict(os.environ, CODEX_SOURCE_LEDGER_DIR=str(root/'ledger'),
                       CODEX_RUNTIME_CONTRACT_STATE_DIR=str(root/'state'),
                       CODEX_THREAD_HISTORY_DB=str(root/'history.sqlite'))
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
            with sqlite3.connect(root/'history.sqlite') as db:
                saved = db.execute('SELECT item_type,item_json FROM thread_items ORDER BY created_at_ms').fetchall()
            self.assertEqual([kind for kind,_ in saved], ['userMessage','agentMessage','userMessage'])
            self.assertEqual(json.loads(saved[1][1])['text'], history[1]['text'])
            self.assertNotIn(container, (root/'history.sqlite').read_bytes().decode(errors='ignore'))
            export_env = dict(env, CODEX_THREAD_ID='synthetic')
            exported = subprocess.run([sys.executable, '-c',
                'import sys,json;sys.path.insert(0,sys.argv[1]);import source_ledger;'
                'print(json.dumps(source_ledger.original_inputs()))', str(ROOT/'hooks/codex')],
                env=export_env, text=True, capture_output=True)
            self.assertEqual(exported.returncode, 0, exported.stderr)
            original = json.loads(exported.stdout)
            self.assertEqual(original['current_request'], prompts[-1])
            self.assertEqual([turn['text'] for turn in original['saved_conversation']['turns']],
                             [prompts[0], history[1]['text']])
            later = send('Change only the label.')
            self.assertEqual(later.returncode, 0, later.stderr)
            self.assertEqual(json.loads(file.read_text().splitlines()[-1])['text'], 'Change only the label.')


if __name__ == '__main__':
    unittest.main()
