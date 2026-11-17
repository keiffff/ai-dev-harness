import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from test_ci_events import ci

c = ci.continuations


class ContinuationsTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.thread = '12345678-1234-1234-1234-123456789abc'
        self.sha = 'a'*40
        self.run = {'id': 41, 'head_sha': self.sha, 'status': 'completed', 'conclusion': 'success',
                    'path': '.github/workflows/deploy.yml', 'run_attempt': 1}

    def register(self, kind='run', **cfg):
        return c.register(ci, self.root, kind, self.thread, self.root,
                          'When this requested job ends, report its output.', 'Read its output and report.',
                          {'repo': 'example/project', 'run_id': 41, 'sha': self.sha, **cfg})

    def row(self, ident):
        with ci.database(self.root) as db:
            return dict(db.execute('SELECT * FROM waits WHERE id=?', (ident,)).fetchone())

    def test_exact_run_terminal_states_are_durable_and_delivered_once(self):
        for result in ('success', 'failure', 'cancelled', 'timed_out'):
            ident = self.register()
            with patch.object(ci, 'gh', return_value={**self.run, 'status': 'in_progress'}):
                self.assertEqual(c.collect(ci, self.root), 0)
            with patch.object(ci, 'gh', return_value={**self.run, 'conclusion': result}):
                self.assertEqual(c.collect(ci, self.root), 1)
                self.assertEqual(c.collect(ci, self.root), 0)
            with patch.object(ci, 'queue_message') as queue, patch.object(ci, 'open_chat'):
                self.assertEqual(c.dispatch(ci, self.root, 'codex', 3)[0]['status'], 'queued')
                self.assertEqual(c.dispatch(ci, self.root, 'codex', 3), [])
                queue.assert_called_once()
            self.assertEqual(self.row(ident)['result'], result)
            self.assertEqual(self.row(ident)['status'], 'queued')

    def test_run_sha_mismatch_never_becomes_success(self):
        ident = self.register()
        with patch.object(ci, 'gh', return_value={**self.run, 'head_sha': 'b'*40}):
            with self.assertRaisesRegex(ValueError, 'identity changed'):
                c.collect(ci, self.root)
        self.assertEqual(self.row(ident)['status'], 'waiting')

    def test_merge_does_not_finish_deployment_and_ci_binding_closure_does_not_remove_wait(self):
        ident = self.register('deployment', pr=7, workflow='.github/workflows/deploy.yml', environment='test env')
        deploy = {'id': 9, 'sha': self.sha, 'environment': 'test env'}
        def api(*args):
            path = args[1]
            if args[0] == 'pr':
                return {'state': 'MERGED', 'mergeCommit': {'oid': self.sha}}
            if '/actions/runs?' in path:
                return [{'workflow_runs': [self.run]}]
            if '/deployments?' in path:
                self.assertIn('environment=test%20env', path)
                return [[deploy]]
            return []
        with patch.object(ci, 'gh', side_effect=api):
            self.assertEqual(c.collect(ci, self.root), 0)
        self.assertEqual(self.row(ident)['status'], 'waiting')
        with patch.object(ci, 'gh', side_effect=lambda *a: [{'state': 'success'}] if '/statuses' in a[1] else api(*a)):
            self.assertEqual(c.collect(ci, self.root), 1)
        self.assertEqual(self.row(ident)['result'], 'success')

    def test_unmerged_closure_and_failed_workflow_are_reported(self):
        for state in ('CLOSED', 'MERGED'):
            ident = self.register('deployment', pr=7, workflow='.github/workflows/deploy.yml', environment='test')
            replies = [{'state': state, 'mergeCommit': {'oid': self.sha}},
                       [{'workflow_runs': [{**self.run, 'conclusion': 'failure'}]}], []]
            with patch.object(ci, 'gh', side_effect=replies):
                self.assertEqual(c.collect(ci, self.root), 1)
            self.assertEqual(self.row(ident)['result'], 'cancelled' if state == 'CLOSED' else 'failure')

    def test_wrong_deployment_environment_or_sha_does_not_finish(self):
        ident = self.register('deployment', pr=7, workflow='.github/workflows/deploy.yml', environment='test')
        with patch.object(ci, 'gh', side_effect=[{'state': 'MERGED', 'mergeCommit': {'oid': self.sha}},
                [{'workflow_runs': [self.run]}], [[{'id': 1, 'sha': 'b'*40, 'environment': 'test'},
                                                 {'id': 2, 'sha': self.sha, 'environment': 'other'}]]]):
            self.assertEqual(c.collect(ci, self.root), 0)
        self.assertEqual(self.row(ident)['status'], 'waiting')

    def test_app_open_retry_does_not_duplicate_queue_and_finish_needs_owning_chat(self):
        ident = self.register()
        c.ready(ci, self.root, ident, 'success', {'exit_code': 0})
        with patch.object(ci, 'queue_message') as queue, patch.object(ci, 'notify'), \
                patch.object(ci, 'open_chat', side_effect=[ci.MonitorError('app unavailable', retryable=True), None]):
            self.assertEqual(c.dispatch(ci, self.root, 'codex', 3)[0]['status'], 'queued_not_opened')
            self.assertEqual(c.dispatch(ci, self.root, 'codex', 3)[0]['status'], 'queued')
            queue.assert_called_once()
        result_file = self.root/'result.txt'
        result_file.write_text('Read the output and reported its result.')
        args = argparse.Namespace(command='finish', state_dir=self.root, id=ident, result_file=result_file)
        with patch.dict(os.environ, CODEX_THREAD_ID='another-chat'):
            with self.assertRaisesRegex(ValueError, 'owning chat'):
                c.command(ci, args)
        with patch.dict(os.environ, CODEX_THREAD_ID=self.thread):
            self.assertEqual(c.command(ci, args)['status'], 'completed')
        self.assertEqual(self.row(ident)['status'], 'completed')

    def test_changed_checkout_still_reports_but_does_not_request_edits(self):
        ident = self.register()
        with ci.database(self.root) as db:
            cfg = json.loads(self.row(ident)['config'])
            cfg['checkout'] = {'head': self.sha, 'branch': 'work', 'remote': 'example'}
            db.execute('UPDATE waits SET config=? WHERE id=?', (json.dumps(cfg), ident))
        c.ready(ci, self.root, ident, 'success', {})
        with patch.object(ci, 'git', return_value='changed'), patch.object(ci, 'queue_message') as queue, patch.object(ci, 'open_chat'):
            c.dispatch(ci, self.root, 'codex', 3)
            prompt = queue.call_args.args[-1]
        self.assertIn('"checkout_changed": true', prompt)
        self.assertIn('without editing', prompt)

    def test_uncertain_queue_failure_stops_and_cancelled_wait_never_dispatches(self):
        ident = self.register()
        c.ready(ci, self.root, ident, 'success', {})
        with patch.object(ci, 'queue_message', side_effect=ci.MonitorError('uncertain', retryable=False)) as queue, \
                patch.object(ci, 'notify'), patch.object(ci, 'open_chat') as opened:
            self.assertEqual(c.dispatch(ci, self.root, 'codex', 3)[0]['status'], 'failed')
            self.assertEqual(c.dispatch(ci, self.root, 'codex', 3), [])
            queue.assert_called_once()
            opened.assert_not_called()
        c.command(ci, argparse.Namespace(state_dir=self.root, command='cancel-wait', id=ident))
        self.assertEqual(c.dispatch(ci, self.root, 'codex', 3), [])

    def start_local(self, script):
        request = self.root/'request.txt'
        request.write_text('Run this local fixture and report the result.')
        return c.command(ci, argparse.Namespace(command='run-local', state_dir=self.root, thread=self.thread,
            cwd=self.root, request_file=request, next_action='Report fixture output.',
            argv=['--', sys.executable, '-c', script]))['wait_id']

    def wait_ready(self, ident):
        deadline = time.monotonic()+5
        while self.row(ident)['status'] == 'waiting' and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertEqual(self.row(ident)['status'], 'ready')
        return self.row(ident)

    def test_actual_detached_worker_records_exit_and_log_for_a_later_monitor(self):
        for code in (0, 3):
            ident = self.start_local(f'print("fixture result"); raise SystemExit({code})')
            row = self.wait_ready(ident)
            self.assertEqual(row['result'], 'success' if code == 0 else 'failure')
            evidence = json.loads(row['evidence'])
            self.assertEqual(evidence['exit_code'], code)
            self.assertIn('fixture result', Path(evidence['log_file']).read_text())

    def test_explicit_stop_records_signal_and_disappeared_worker_is_interrupted(self):
        marker = self.root/'started'
        ident = self.start_local(f'from pathlib import Path; import time; Path({str(marker)!r}).touch(); time.sleep(30)')
        deadline = time.monotonic()+5
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertTrue(marker.exists())
        os.kill(self.row(ident)['worker_pid'], signal.SIGTERM)
        self.assertEqual(self.wait_ready(ident)['result'], 'stopped')
        lost = self.register('local', log_file=str(self.root/'missing.log'), lock_file=str(self.root/'lost.lock'))
        self.assertEqual(c.collect(ci, self.root), 1)
        self.assertEqual(self.row(lost)['result'], 'interrupted')


if __name__ == '__main__':
    unittest.main()
