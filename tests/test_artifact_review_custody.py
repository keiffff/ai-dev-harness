"""Check invocation, custody and evidence transfer; no prose self-scoring."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'wrappers/bin/jev-artifact-review.example'
HTML = ROOT / 'wrappers/bin/claude-html-report.example'


class ArtifactReviewCustodyTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.candidate = self.root / 'report.html'
        self.candidate.write_text('<html><audio controls></audio></html>')
        self.request = self.root / 'request.txt'
        self.request.write_text('Keep the existing playback controls.')
        self.requirements = self.root / 'sources.txt'
        self.requirements.write_text('Actual source evidence.')
        fake = self.root / 'evaluator'
        fake.write_text('#!' + sys.executable + '\nimport json,os\nfrom pathlib import Path\np=Path(os.environ["CALLS"])\np.write_text(p.read_text()+"1" if p.exists() else "1")\nprint(os.environ["RESPONSE"])\n')
        fake.chmod(0o755)
        self.calls = self.root / 'calls'
        self.env = {**os.environ, 'TYPESAFE_API_KEY': 'synthetic-key',
                    'JEV_KIT_SEMANTIC_DIFF_CLI': str(fake), 'CALLS': str(self.calls),
                    'RESPONSE': json.dumps({'status': 'evaluated', 'scores': {'material_violation': .1}})}

    def review(self):
        return subprocess.run([sys.executable, str(REVIEW), '--request-file', str(self.request),
            '--requirements-file', str(self.requirements), '--candidate-file', str(self.candidate)],
            env=self.env, capture_output=True, text=True)

    def test_prose_and_static_reports_make_no_model_call(self):
        for value in ['A short report.', '<html><h1>Report</h1><script>const metadata={}</script></html>']:
            self.candidate.write_text(value)
            result = self.review()
            self.assertEqual(json.loads(result.stdout)['decision'], 'skipped')
            self.assertFalse(self.calls.exists())
            self.assertEqual(self.candidate.read_text(), value)

    def test_unchanged_inputs_reuse_even_unavailable_results(self):
        for response in [{'status': 'evaluated', 'scores': {'material_violation': .1}},
                         {'status': 'unavailable', 'errorKind': 'api'}]:
            self.env['RESPONSE'] = json.dumps(response)
            self.requirements.write_text(json.dumps(response))
            before = self.candidate.read_bytes()
            first, second = self.review(), self.review()
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(self.candidate.read_bytes(), before)
        self.assertEqual(self.calls.read_text(), '11')
        self.request.write_text('New user-requested comparison.')
        self.review()
        self.assertEqual(self.calls.read_text(), '111')

    def test_empty_findings_cannot_start_editor_and_stale_receipt_is_rejected(self):
        original = self.candidate.read_bytes()
        receipt = self.root / 'review.json'
        receipt.write_text(json.dumps({'kind': 'artifact-integrity-review',
            'input_sha256': {'candidate': hashlib.sha256(original).hexdigest(),
                             'request': hashlib.sha256(self.request.read_bytes()).hexdigest(),
                             'requirements': hashlib.sha256(self.requirements.read_bytes()).hexdigest(),
                             'baseline': None},
            'input_sources': {'requirements': str(self.requirements), 'baseline': None},
            'concrete_review': {'status': 'completed', 'findings': []}}))
        command = [sys.executable, str(HTML), '--request-file', str(self.request),
                   '--edit-file', str(self.candidate), '--integrity-review-file', str(receipt)]
        env = {**self.env, 'CLAUDE_HTML_REPORT_CLI': str(self.root / 'must-not-start')}
        result = subprocess.run(command, env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)['changed'])
        self.assertEqual(self.candidate.read_bytes(), original)
        self.candidate.write_bytes(original + b' ')
        result = subprocess.run(command, env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('does not match', result.stderr)
        self.candidate.write_bytes(original)
        self.requirements.write_text('Changed source evidence')
        result = subprocess.run(command, env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('source changed', result.stderr)

    def test_html_registers_existing_custody_and_main_patch_is_denied(self):
        def load(name):
            spec = importlib.util.spec_from_file_location(name, ROOT / 'hooks/codex' / (name + '.py'))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        ledger, delivery = load('source_ledger'), load('reader_delivery')
        env = {'CODEX_THREAD_ID': 'fixture-task',
               'CODEX_SOURCE_LEDGER_DIR': str(self.root / 'ledger'),
               'CODEX_SOURCE_LEDGER_SCRIPT': str(ROOT / 'hooks/codex/source_ledger.py'),
               'CODEX_READER_DELIVERY_STAGE_DIR': str(self.root / 'staged'),
               'CODEX_RUNTIME_CONTRACT_STATE_DIR': str(self.root / 'state')}
        with patch.dict(os.environ, env):
            ledger.append_prompt('fixture-task', self.request.read_text())
            reference = ledger.request_reference('fixture-task')
            runpy.run_path(str(HTML))['stage_html_delivery'](self.candidate)
            delivery.consume('fixture-task', reference)
            reason = delivery.direct_edit_reason('fixture-task', reference, {
                'tool_name': 'apply_patch', 'cwd': str(self.root),
                'tool_input': {'command': '*** Update File: ' + str(self.candidate)}})
            self.assertIn('claude-html-report', reason)
            ledger.append_prompt('fixture-task', 'Change the heading.')
            self.assertIsNotNone(delivery.direct_edit_reason('fixture-task',
                ledger.request_reference('fixture-task'), {'tool_name': 'Edit', 'cwd': str(self.root),
                'tool_input': {'file_path': str(self.candidate)}}))

    def test_nonempty_unconfirmed_findings_cannot_start_editor(self):
        receipt = self.root / 'review.json'
        receipt.write_text(json.dumps({'kind': 'artifact-integrity-review',
            'input_sha256': {'candidate': hashlib.sha256(self.candidate.read_bytes()).hexdigest(),
                             'request': hashlib.sha256(self.request.read_bytes()).hexdigest(),
                             'requirements': hashlib.sha256(self.requirements.read_bytes()).hexdigest(),
                             'baseline': None},
            'input_sources': {'requirements': str(self.requirements), 'baseline': None},
            'concrete_review': {'status': 'completed', 'findings': [{
                'source': 'request', 'requirement': self.request.read_text(),
                'evidence': '<audio controls>', 'reason': 'Unadjudicated reviewer suspicion.'}]}}))
        command = [sys.executable, str(HTML), '--request-file', str(self.request),
                   '--edit-file', str(self.candidate), '--integrity-review-file', str(receipt)]
        before = self.candidate.read_bytes()
        result = subprocess.run(command, env={**self.env, 'CLAUDE_HTML_REPORT_CLI': '/missing/editor'},
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['reason'], 'no_confirmed_integrity_findings')
        self.assertEqual(self.candidate.read_bytes(), before)
        result = subprocess.run(command + ['--confirmed-finding-index', '1'], env=self.env,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('outside this receipt', result.stderr)

    def test_only_confirmed_findings_and_unpromoted_sources_reach_editor(self):
        self.candidate.write_text('<!doctype html><html><audio controls></audio></html>')
        receipt = self.root / 'review.json'
        finding = {'source': 'request', 'requirement': self.request.read_text(),
                   'evidence': '<audio controls>', 'reason': 'Observed playback defect.'}
        receipt.write_text(json.dumps({'kind': 'artifact-integrity-review',
            'input_sha256': {'candidate': hashlib.sha256(self.candidate.read_bytes()).hexdigest(),
                             'request': hashlib.sha256(self.request.read_bytes()).hexdigest(),
                             'requirements': hashlib.sha256(self.requirements.read_bytes()).hexdigest(),
                             'baseline': None},
            'input_sources': {'requirements': str(self.requirements), 'baseline': None},
            'concrete_review': {'status': 'completed', 'findings': [finding,
                {**finding, 'reason': 'Unselected preference: redesign the page.'}]}}))
        fake = self.root / 'claude'
        fake.write_text('#!' + sys.executable + '\nimport json,os,sys\nfrom pathlib import Path\n'
            'if "--help" in sys.argv:\n print("--safe-mode"); raise SystemExit(0)\n'
            'packet=json.loads(sys.stdin.read().split("--- PACKET ---\\n",1)[1])\n'
            'Path(os.environ["PACKET"]).write_text(json.dumps(packet))\n'
            'print(json.dumps({"type":"result","is_error":False,"result":"Unchanged"}))\n')
        fake.chmod(0o755)
        capture = self.root / 'packet.json'
        result = subprocess.run([sys.executable, str(HTML), '--request-file', str(self.request),
            '--edit-file', str(self.candidate), '--integrity-review-file', str(receipt),
            '--confirmed-finding-index', '0'], text=True, capture_output=True,
            env={**self.env, 'CLAUDE_HTML_REPORT_CLI': str(fake), 'CLAUDE_CODE_OAUTH_TOKEN': 'synthetic',
                 'PACKET': str(capture)})
        self.assertEqual(result.returncode, 0, result.stderr)
        packet = json.loads(capture.read_text())
        self.assertEqual(packet['integrity_review']['concrete_review']['findings'], [finding])
        self.assertEqual(packet['evidence'], [])
        self.assertEqual(packet['integrity_sources']['producer_notes']['content'], self.requirements.read_text())
        self.assertEqual(packet['request']['content'], self.request.read_text())


if __name__ == '__main__':
    unittest.main()
