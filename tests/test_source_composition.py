import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'codex/skills/codex-writing/scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('source_composition', SCRIPTS / 'compose_from_sources.py')
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


class SourceCompositionTests(unittest.TestCase):
    def selection(self, operation):
        return {'operation': operation, 'request_quote': 'request', 'reason': 'Current operation.',
                'draft_source': '', 'draft_quote': '', 'evidence': [], 'corrections': [],
                'replacements': [], 'medium': 'other', 'outline': []}

    def test_source_and_draft_selection_cannot_invent_quotes(self):
        sources = {'current_request': 'request', 'source_material': 'source'}
        selection = self.selection('compose')
        workflow.validate_selection(selection, sources)
        for key in ('request', 'evidence', 'draft'):
            bad = self.selection('edit' if key == 'draft' else 'compose')
            if key == 'request':
                bad['request_quote'] = 'invented'
            elif key == 'evidence':
                bad['outline'] = [{'point': 'Result.', 'evidence': [{'source': 'source_material', 'quote': 'invented', 'role': 'Fact.'}]}]
            else:
                bad.update(draft_source='source_material', draft_quote='invented')
            with self.subTest(key=key), self.assertRaises(ValueError):
                workflow.validate_selection(bad, sources)

    def test_composition_receives_selected_evidence_not_old_conversation_or_draft(self):
        selection = self.selection('compose')
        selection['outline'] = [{'point': 'Result.', 'evidence': [{'source': 'source_material', 'quote': 'selected', 'role': 'Result.'}]}]
        calls = []
        def author(packet, schema, prompt):
            calls.append(packet)
            return {'content': 'result'}
        self.assertEqual(workflow.generate(selection, 'request', {'source_material': 'old narrative'}, author), 'result')
        self.assertEqual(calls, [{'current_request': 'request', 'operation': 'compose', 'outline': selection['outline'], 'medium': 'other'}])
        selection['operation'] = 'conversation'
        calls.clear()
        workflow.generate(selection, 'request', {'source_material': 'old narrative'}, author)
        self.assertEqual(calls, [{'current_request': 'request', 'operation': 'conversation', 'medium': 'other'}])

    def test_editor_cannot_rewrite_unselected_regions(self):
        selection = self.selection('edit')
        selection.update(draft_quote='first\r\nunchanged\r\nlast\r\n', draft_source='source_material',
            corrections=[{'old': 'last', 'source': 'current_request', 'quote': 'request', 'reason': 'Requested.'}],
            replacements=['changed'])
        sources = {'current_request': 'request', 'source_material': selection['draft_quote']}
        workflow.validate_selection(selection, sources)
        def author(packet, schema, prompt):
            self.assertNotIn('source_material', packet)
            self.assertEqual(schema['properties']['replacements']['maxItems'], 1)
            return {'replacements': ['changed']}
        self.assertEqual(workflow.generate(selection, 'request', sources, author), 'first\r\nunchanged\r\nchanged\r\n')
        selection['corrections'] = []
        selection['replacements'] = []
        self.assertEqual(workflow.generate(selection, 'request', sources, lambda *args: self.fail('No edit needs no author call')),
                         selection['draft_quote'])

    def test_diagnostic_is_retained_but_not_confused_with_a_tool_action(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'trace.jsonl'
            rows = [{'type': 'item.completed', 'item': {'type': 'error', 'message': 'Ignored legacy setting.'}},
                    {'type': 'turn.completed', 'usage': {'input_tokens': 3}}]
            path.write_text('\n'.join(json.dumps(r) for r in rows))
            observation = workflow.observe_trace(path)
            self.assertEqual(observation['unexpected_actions'], [])
            self.assertEqual(len(observation['diagnostics']), 1)
            rows += [{'type': 'item.completed', 'item': {'type': 'command_execution'}}, {'type': 'turn.failed'}]
            path.write_text('\n'.join(json.dumps(r) for r in rows))
            observation = workflow.observe_trace(path)
            self.assertEqual(observation['unexpected_actions'], ['command_execution'])
            self.assertTrue(observation['turn_failed'])

    def test_secret_input_stops_before_a_model_call(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'request.txt').write_text('Summarize.')
            (root / 'source.txt').write_text('Authorization: Bearer abcdefghijklmnop')
            with self.assertRaisesRegex(ValueError, 'nothing was sent'):
                workflow.run(root / 'request.txt', root / 'source.txt', root / 'output.txt', root / 'work',
                             root / 'must-not-start', 'example', 'medium')
            self.assertFalse((root / 'work').exists())

    def test_cli_applies_only_selected_edit_and_preserves_crlf_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'request.txt').write_text('Change the first word.')
            (root / 'source.txt').write_bytes(b'draft\r\nkeep\r\n')
            selection = {'operation': 'edit', 'request_quote': 'Change the first word.', 'reason': 'Requested.',
                'draft_source': 'source_material', 'draft_quote': 'draft\r\nkeep\r\n', 'evidence': [],
                'corrections': [{'old': 'draft', 'source': 'current_request',
                                 'quote': 'Change the first word.', 'reason': 'Requested.'}],
                'replacements': ['changed'], 'outline': []}
            intake = {'operation': 'edit', 'medium': 'other', 'request_quote': 'Change the first word.',
                      'draft_quote': '', 'conversation_response': ''}
            stub = root / 'native-stub'
            stub.write_text('#!' + sys.executable + '\nimport json,pathlib,sys\n'
                'schema=json.loads(pathlib.Path(sys.argv[sys.argv.index("--output-schema")+1]).read_text())\n'
                f'value={intake!r} if "conversation_response" in schema["properties"] else ({selection!r} if "operation" in schema["properties"] else {{"replacements":["changed"]}})\n'
                'pathlib.Path(sys.argv[sys.argv.index("-o")+1]).write_text(json.dumps(value))\n'
                'print(json.dumps({"type":"turn.completed","usage":{"input_tokens":1}}))\n')
            stub.chmod(0o700)
            result = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'compose_from_sources.py'),
                '--request-file', str(root / 'request.txt'), '--source-file', str(root / 'source.txt'),
                '--output', str(root / 'output.txt'), '--work-dir', str(root / 'work'),
                '--codex-bin', str(stub), '--model', 'fixture', '--reasoning', 'medium'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root / 'output.txt').read_bytes(), b'changed\r\nkeep\r\n')
            self.assertEqual((root / 'source.txt').read_bytes(), b'draft\r\nkeep\r\n')

    def test_current_draft_is_fixed_before_history_can_substitute_an_older_one(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'request.txt').write_text('Please check: current draft.')
            (root / 'source.txt').write_text('historical draft.')
            intake = {'operation': 'edit', 'medium': 'other', 'request_quote': 'Please check:',
                      'draft_quote': 'current draft.', 'conversation_response': ''}
            plan = {'operation': 'edit', 'request_quote': 'Please check:', 'reason': 'Check.',
                    'draft_source': 'source_material', 'draft_quote': 'historical draft.',
                    'evidence': [], 'corrections': [], 'replacements': [], 'outline': []}
            stub = root / 'native-stub'
            stub.write_text('#!' + sys.executable + '\nimport json,pathlib,sys\n'
                'schema=json.loads(pathlib.Path(sys.argv[sys.argv.index("--output-schema")+1]).read_text())\n'
                'packet=json.loads(sys.stdin.read())\n'
                'if "conversation_response" in schema["properties"]:\n'
                ' assert set(packet)=={"current_request"}\n'
                f' value={intake!r}\n'
                'else:\n'
                ' assert "draft_quote" not in schema["properties"]\n'
                f' value={plan!r}\n'
                'pathlib.Path(sys.argv[sys.argv.index("-o")+1]).write_text(json.dumps(value))\n')
            stub.chmod(0o700)
            workflow.run(root / 'request.txt', root / 'source.txt', root / 'output.txt', root / 'work',
                         stub, 'fixture', 'medium')
            self.assertEqual((root / 'output.txt').read_text(), 'current draft.')

    def test_missing_source_group_is_added_before_composition_not_after_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'request.txt').write_text('Summarize the investigation.')
            (root / 'source.txt').write_text('First result. Second result.')
            point = lambda quote: {'point': quote, 'evidence': [{'source': 'source_material', 'quote': quote, 'role': 'Result.'}]}
            calls = []
            def native(prompt, schema, target, instruction, *runtime):
                packet = json.loads(prompt)
                calls.append(target.name)
                if target.name == 'intake':
                    return {'operation': 'compose', 'medium': 'other', 'request_quote': 'Summarize', 'draft_quote': '', 'conversation_response': ''}
                if target.name == 'selection':
                    return {'operation': 'compose', 'request_quote': 'Summarize', 'reason': 'Requested.', 'outline': [point('First result.')], 'corrections': []}
                if target.name == 'coverage':
                    self.assertIn('source_material', packet)
                    self.assertNotIn('candidate', packet)
                    return {'missing_points': [point('Second result.')]}
                self.assertEqual([p['point'] for p in packet['outline']], ['First result.', 'Second result.'])
                self.assertNotIn('source_material', packet)
                return {'content': 'Both results.', 'delivery_notes': ''}
            with patch.object(workflow, 'native', native):
                workflow.run(root / 'request.txt', root / 'source.txt', root / 'output.txt', root / 'work',
                             root / 'unused', 'fixture', 'medium')
            self.assertEqual(calls, ['intake', 'selection', 'coverage', 'generation'])
            self.assertEqual((root / 'output.txt').read_text(), 'Both results.')


if __name__ == '__main__':
    unittest.main()
