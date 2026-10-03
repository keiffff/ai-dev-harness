import contextlib
import io
import json
import runpy
import signal
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


class ReleaseCompatibilityTests(unittest.TestCase):
    def wrapper(self, name):
        return runpy.run_path(str(ROOT / 'wrappers' / 'bin' / f'{name}.example'))

    def test_claude_rejects_bare_unavailable_without_running_a_model(self):
        for name in ('claude-strategic-review', 'claude-html-report'):
            with self.subTest(name=name):
                wrapper = self.wrapper(name)
                check = wrapper['require_safe_mode']
                result = subprocess.CompletedProcess([], 0, '--safe-mode', '')
                with mock.patch.object(check.__globals__['subprocess'], 'run', return_value=result) as run:
                    with contextlib.redirect_stderr(io.StringIO()) as diagnostic:
                        with self.assertRaises(SystemExit) as exit_result:
                            check('/synthetic/claude')
                self.assertEqual(exit_result.exception.code, 1)
                self.assertIn('required --bare', diagnostic.getvalue())
                self.assertEqual(run.call_count, 1)
                self.assertEqual(run.call_args.args[0], ['/synthetic/claude', '--help'])

    def test_claude_timeout_kills_process_group_after_term_does_not_close_pipes(self):
        for name, function_name, extra in (
            ('claude-strategic-review', 'run_review', []),
            ('claude-html-report', 'run_claude', ['opus']),
        ):
            with self.subTest(name=name):
                wrapper = self.wrapper(name)
                function = wrapper[function_name]
                globals_ = function.__globals__
                process = mock.Mock(pid=12345)
                process.communicate.side_effect = [
                    subprocess.TimeoutExpired('synthetic', 1),
                    subprocess.TimeoutExpired('synthetic', 5),
                    ('partial output', ''),
                ]
                with mock.patch.object(globals_['subprocess'], 'Popen', return_value=process) as popen:
                    with mock.patch.object(globals_['time'], 'monotonic', side_effect=[0, 0, 1, 2]):
                        with mock.patch.object(globals_['os'], 'killpg') as killpg:
                            with contextlib.redirect_stderr(io.StringIO()):
                                with self.assertRaises(SystemExit) as exit_result:
                                    function('synthetic prompt', 'synthetic-token', 1, '/synthetic/claude', *extra)
                self.assertEqual(exit_result.exception.code, 124)
                self.assertEqual(killpg.call_args_list, [
                    mock.call(12345, signal.SIGTERM), mock.call(12345, signal.SIGKILL),
                ])
                self.assertTrue(popen.call_args.kwargs['start_new_session'])
                command = popen.call_args.args[0]
                self.assertIn('--bare', command)
                self.assertIn('--safe-mode', command)
                self.assertEqual(command[command.index('--tools') + 1], '')
                self.assertEqual(command[command.index('--max-turns') + 1], '1')
                self.assertIn('--no-session-persistence', command)
                self.assertNotIn('--permission-mode', command)

    def test_gemini_quota_errors_are_not_retried_by_wrapper(self):
        wrapper = self.wrapper('gemini-japanese-polish')
        call = wrapper['call_gemini']
        for message in ('daily quota exhausted', 'billing spend cap exceeded', 'prepaid credits depleted'):
            with self.subTest(message=message):
                result = {'status': 'ERROR', 'error': message + ' synthetic-key'}
                completed = subprocess.CompletedProcess([], 1, json.dumps({'event': 'result', 'result': result}), '')
                with mock.patch.dict(call.__globals__, {'antigravity_cli': lambda: Path(sys.executable)}):
                    with mock.patch.object(call.__globals__['subprocess'], 'run', return_value=completed) as run:
                        with contextlib.redirect_stderr(io.StringIO()) as diagnostic:
                            with self.assertRaises(SystemExit) as exit_result:
                                call('synthetic prompt', 'synthetic-key', 5)
                self.assertEqual(exit_result.exception.code, 1)
                self.assertEqual(run.call_count, 1)
                self.assertIn(message, diagnostic.getvalue())
                self.assertNotIn('synthetic-key', diagnostic.getvalue())
                self.assertIn('[REDACTED]', diagnostic.getvalue())

    def test_gemini_accepts_cli_recovered_structured_result_with_progress_events(self):
        wrapper = self.wrapper('gemini-japanese-polish')
        call = wrapper['call_gemini']
        output = {'revised_text': '確認済みの文章', 'changes': [], 'warnings': []}
        result = {'status': 'SUCCESS', 'structured_output': output}
        stream = '\n'.join(json.dumps(event, ensure_ascii=False) for event in (
            {'event': 'init'}, {'event': 'progress', 'message': 'transient rate limit'},
            {'event': 'result', 'result': result},
        ))
        completed = subprocess.CompletedProcess([], 0, stream, '')
        with mock.patch.dict(call.__globals__, {'antigravity_cli': lambda: Path(sys.executable)}):
            with mock.patch.object(call.__globals__['subprocess'], 'run', return_value=completed) as run:
                response = call('synthetic prompt', 'synthetic-key', 5)
        self.assertEqual(wrapper['extract_structured_output'](response), output)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.kwargs['timeout'], 20)
        command = run.call_args.args[0]
        self.assertIn('--sandbox', command)
        self.assertEqual(command[command.index('--json-schema') + 1], json.dumps(wrapper['response_schema'](), ensure_ascii=False, separators=(',', ':')))

    def test_gemini_outer_timeout_does_not_start_another_cli_call(self):
        wrapper = self.wrapper('gemini-japanese-polish')
        call = wrapper['call_gemini']
        with mock.patch.dict(call.__globals__, {'antigravity_cli': lambda: Path(sys.executable)}):
            with mock.patch.object(call.__globals__['subprocess'], 'run', side_effect=subprocess.TimeoutExpired('synthetic', 20)) as run:
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as exit_result:
                        call('synthetic prompt', 'synthetic-key', 5)
        self.assertEqual(exit_result.exception.code, 124)
        self.assertEqual(run.call_count, 1)

    def test_openspec_skill_requires_exact_current_task_location(self):
        skill = (ROOT / 'codex' / 'skills' / 'codex-openspec-workflow' / 'SKILL.md').read_text()
        for requirement in (
            '`sourcePath` and `line`', '1-based line', 'reread the file',
            'same task checkbox and text', 'duplicate task text',
            'refresh apply instructions', 'do not edit the stale location',
            'do not synthesize `sourcePath` or `line`',
        ):
            self.assertIn(requirement, skill)


if __name__ == '__main__':
    unittest.main()
