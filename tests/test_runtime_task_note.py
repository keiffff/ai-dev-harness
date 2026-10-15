import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / 'hooks/codex/runtime-contract-context.py'


class RuntimeTaskNoteTests(unittest.TestCase):
    def prepare(self, directory):
        root = Path(directory)
        contract = root / 'contract.md'
        contract.write_text('Shared operating contract')
        note = root / 'note.md'
        note.write_text('Goal: repair normal generation.\nUnfinished: execute the normal entry.\n')
        env = os.environ.copy()
        env.update(CODEX_THREAD_ID='task-a', CODEX_RUNTIME_CONTRACT=str(contract),
                   CODEX_RUNTIME_CONTRACT_STATE_DIR=str(root / 'state'))
        return root, note, env

    def maintain(self, env, note):
        result = subprocess.run(['python3', '-B', str(HOOK), '--task-note', str(note)],
                                env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return Path(json.loads(result.stdout)['task_note'])

    def context(self, env, session='task-a', event='UserPromptSubmit', source=None):
        payload = {'session_id': session, 'hook_event_name': event}
        if source:
            payload['source'] = source
        result = subprocess.run(['python3', '-B', str(HOOK)], input=json.dumps(payload),
                                env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)['hookSpecificOutput']['additionalContext'] if result.stdout else ''

    def test_maintained_outcome_survives_compaction_and_is_task_local(self):
        with tempfile.TemporaryDirectory() as directory:
            root, note, env = self.prepare(directory)
            path = self.maintain(env, note)
            self.assertEqual(path.name, hashlib.sha256(b'task-a').hexdigest() + '.task.md')
            self.assertEqual(path.read_text(), note.read_text())
            first = self.context(env)
            self.assertIn('Unfinished: execute the normal entry.', first)
            self.assertEqual(self.context(env), '')
            self.assertIn('Unfinished: execute the normal entry.',
                          self.context(env, event='SessionStart', source='compact'))
            other = self.context(env, session='task-b')
            self.assertIn('Shared operating contract', other)
            self.assertNotIn('normal generation', other)

    def test_updating_evidence_reinjects_without_changing_shared_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            root, note, env = self.prepare(directory)
            self.maintain(env, note)
            self.context(env)
            note.write_text('Goal: repair normal generation.\nCompleted: normal entry passed.\nEvidence: output inspected.\n')
            self.maintain(env, note)
            changed = self.context(env)
            self.assertIn('Completed: normal entry passed.', changed)
            self.assertNotIn('Unfinished: execute', changed)
            self.assertIn('not new authority', changed)
            self.assertEqual((root / 'contract.md').read_text(), 'Shared operating contract')

    def test_missing_thread_binding_does_not_create_another_task_note(self):
        with tempfile.TemporaryDirectory() as directory:
            root, note, env = self.prepare(directory)
            env.pop('CODEX_THREAD_ID', None)
            result = subprocess.run(['python3', '-B', str(HOOK), '--task-note', str(note)],
                                    env=env, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / 'state').exists())


if __name__ == '__main__':
    unittest.main()
