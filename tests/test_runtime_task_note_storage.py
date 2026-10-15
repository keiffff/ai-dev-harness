import importlib.util
import io
import json
import os
import sys
import tempfile
import tomllib
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

HOOK = Path(__file__).resolve().parents[1] / 'hooks/codex/runtime-contract-context.py'


class DefaultTaskNoteStorageTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('runtime_task_note_hook', HOOK)
        self.hook = importlib.util.module_from_spec(spec)
        with patch.object(sys, 'path', [str(HOOK.parent), *sys.path]):
            spec.loader.exec_module(self.hook)

    def deliver(self, session='default-task', source='startup'):
        payload = {'session_id': session, 'hook_event_name': 'SessionStart', 'source': source}
        out = io.StringIO()
        with patch.object(sys, 'stdin', io.StringIO(json.dumps(payload))), redirect_stdout(out):
            self.hook.main()
        return json.loads(out.getvalue())['hookSpecificOutput']['additionalContext']

    def test_sandbox_registration_is_persisted_by_hook_and_survives_temp_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            note = root / 'note.md'
            note.write_text('Goal: repair entry. Unfinished: verify normal output.')
            contract = root / 'contract.md'
            contract.write_text('Shared contract')
            with patch.object(self.hook, 'DEFAULT_STATE_DIR', root / 'durable'), patch.object(self.hook.tempfile, 'gettempdir', return_value=str(root / 'temporary')), patch.dict(os.environ, {'CODEX_THREAD_ID': 'default-task', 'CODEX_RUNTIME_CONTRACT': str(contract)}):
                os.environ.pop('CODEX_RUNTIME_CONTRACT_STATE_DIR', None)
                out = io.StringIO()
                with redirect_stdout(out):
                    self.hook.maintain_task_note(note)
                staged = Path(json.loads(out.getvalue())['task_note'])
                self.assertTrue(staged.is_relative_to(root / 'temporary'))
                self.assertFalse((root / 'durable').exists())
                self.assertIn('Unfinished: verify normal output.', self.deliver())
                durable = self.hook.task_note_path(root / 'durable', 'default-task')
                self.assertEqual(durable.read_text().strip(), note.read_text())
                staged.unlink()
                self.assertIn('Unfinished: verify normal output.', self.deliver(source='compact'))
                self.assertNotIn('repair entry', self.deliver(session='other-task'))

    def test_new_staged_completion_replaces_earlier_durable_unfinished_work(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            note = root / 'note.md'
            contract = root / 'contract.md'
            contract.write_text('Shared contract')
            with patch.object(self.hook, 'DEFAULT_STATE_DIR', root / 'durable'), patch.object(self.hook.tempfile, 'gettempdir', return_value=str(root / 'temporary')), patch.dict(os.environ, {'CODEX_THREAD_ID': 'default-task', 'CODEX_RUNTIME_CONTRACT': str(contract)}):
                os.environ.pop('CODEX_RUNTIME_CONTRACT_STATE_DIR', None)
                note.write_text('Unfinished: verify output.')
                with redirect_stdout(io.StringIO()):
                    self.hook.maintain_task_note(note)
                self.deliver()
                note.write_text('Completed: output verified. No required unfinished work.')
                with redirect_stdout(io.StringIO()):
                    self.hook.maintain_task_note(note)
                context = self.deliver(source='resume')
                self.assertIn('Completed: output verified.', context)
                self.assertNotIn('Unfinished: verify output.', context)
                self.assertEqual(self.hook.task_note_path(root / 'durable', 'default-task').read_text().strip(), note.read_text())


    def test_failed_persistence_invalidates_stale_snapshot_before_temp_disappears(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            note = root / 'note.md'
            contract = root / 'contract.md'
            contract.write_text('Shared contract')
            with patch.object(self.hook, 'DEFAULT_STATE_DIR', root / 'durable'), patch.object(self.hook.tempfile, 'gettempdir', return_value=str(root / 'temporary')), patch.dict(os.environ, {'CODEX_THREAD_ID': 'default-task', 'CODEX_RUNTIME_CONTRACT': str(contract)}):
                os.environ.pop('CODEX_RUNTIME_CONTRACT_STATE_DIR', None)
                note.write_text('Unfinished: verify output.')
                with redirect_stdout(io.StringIO()):
                    self.hook.maintain_task_note(note)
                self.deliver()
                note.write_text('Completed: output verified.')
                with redirect_stdout(io.StringIO()):
                    self.hook.maintain_task_note(note)
                with patch.object(self.hook, 'write_task_note', side_effect=OSError('storage unavailable')), patch.object(sys, 'stderr', io.StringIO()) as diagnostic:
                    self.assertIn('Completed: output verified.', self.deliver())
                    self.assertIn('could not be persisted', diagnostic.getvalue())
                self.assertFalse(self.hook.task_note_path(root / 'durable', 'default-task').exists())
                self.hook.maintained_task_note_path(root / 'durable', 'default-task').unlink()
                self.assertNotIn('Unfinished: verify output.', self.deliver(source='resume'))


    def test_post_tool_persists_registration_without_injecting_context(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            note = root / 'note.md'
            note.write_text('Completed: normal entry verified.')
            with patch.object(self.hook, 'DEFAULT_STATE_DIR', root / 'durable'), patch.object(self.hook.tempfile, 'gettempdir', return_value=str(root / 'temporary')), patch.dict(os.environ, {'CODEX_THREAD_ID': 'default-task'}):
                os.environ.pop('CODEX_RUNTIME_CONTRACT_STATE_DIR', None)
                with redirect_stdout(io.StringIO()):
                    self.hook.maintain_task_note(note)
                payload = {'session_id': 'default-task', 'hook_event_name': 'PostToolUse', 'tool_name': 'Bash'}
                out = io.StringIO()
                with patch.object(sys, 'stdin', io.StringIO(json.dumps(payload))), redirect_stdout(out):
                    self.hook.main()
                self.assertEqual(out.getvalue(), '')
                self.assertEqual(self.hook.task_note_path(root / 'durable', 'default-task').read_text().strip(), note.read_text())
                self.assertFalse(self.hook.state_path(root / 'durable', 'default-task').exists())
        config = tomllib.loads((HOOK.parents[2] / 'codex/config.example.toml').read_text())
        self.assertTrue(any(group['matcher'] == '^Bash$' and any(handler['command'].endswith('/runtime-contract-context.py') for handler in group['hooks']) for group in config['hooks']['PostToolUse']))


if __name__ == '__main__':
    unittest.main()
