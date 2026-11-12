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
    def test_missing_launcher_payload_is_resolved_before_any_model_request(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            broken, installed = root/'broken', root/'installed'
            broken.write_text('#!/bin/sh\necho "spawn missing executable ENOENT" >&2\nexit 1\n')
            installed.write_text('#!/bin/sh\necho "codex-cli fixture"\n')
            for path in (broken, installed):
                path.chmod(0o700)
            workflow.producer_cli.cache_clear()
            with patch.object(workflow, 'APP_CODEX_CLI', installed):
                self.assertEqual(workflow.producer_cli(broken), installed)
            workflow.producer_cli.cache_clear()

    def test_launcher_permission_or_authentication_failure_does_not_switch_installations(self):
        with tempfile.TemporaryDirectory() as directory:
            broken = Path(directory)/'blocked'
            broken.write_text('#!/bin/sh\necho "Permission denied" >&2\nexit 1\n')
            broken.chmod(0o700)
            workflow.producer_cli.cache_clear()
            with self.assertRaises(RuntimeError):
                workflow.producer_cli(broken)
            workflow.producer_cli.cache_clear()

    def selection(self, operation):
        return {'operation': operation, 'request_quote': 'request', 'reason': 'Current operation.',
                'draft_source': '', 'draft_quote': '', 'evidence': [], 'corrections': [],
                'replacements': [], 'medium': 'other', 'outline': []}

    def test_evidence_source_is_a_packet_key_not_a_description(self):
        for schema in (workflow.EVIDENCE, workflow.CORRECTION):
            self.assertEqual(schema['properties']['source']['enum'],
                             ['current_request', 'source_material'])

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

    def test_same_edit_span_keeps_all_evidence_but_is_replaced_only_once(self):
        sources = {'current_request': 'Explain why.', 'source_material': 'Keep the existing link.'}
        first = {'old': 'Status.', 'source': 'current_request', 'quote': 'Explain why.', 'reason': 'Add the reason.'}
        second = {'old': 'Status.', 'source': 'source_material', 'quote': 'Keep the existing link.', 'reason': 'Preserve the link.'}
        merged = workflow.coalesce_corrections('Before. Status. After.', [first, second], sources)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]['requirements'], [first, second])
        self.assertEqual(workflow.apply_edits('Before. Status. After.', merged, ['Reason and link.'], sources),
                         'Before. Reason and link. After.')

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

    def test_independent_review_uses_prompt_file_and_stops_without_producer_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wrapper = root/'reviewer'
            wrapper.write_text('#!' + sys.executable + '\nimport sys,pathlib,json\n'
                'assert sys.argv[1] == "--prompt-file"\n'
                'assert "candidate" in pathlib.Path(sys.argv[2]).read_text()\n'
                'print(json.dumps({"edits":[],"retained_qualifications":[],"delivery_notes":""}))\n')
            wrapper.chmod(0o700)
            with patch.dict('os.environ', CLAUDE_STRATEGIC_REVIEW_WRAPPER=str(wrapper)):
                result = workflow.review('{"candidate":"Draft"}', workflow.DRAFT_CHECK_SCHEMA,
                                         root/'pass', workflow.DRAFT_CHECK)
                self.assertEqual(result['edits'], [])
                wrapper.write_text('#!' + sys.executable + '\nraise SystemExit(1)\n')
                with self.assertRaises(RuntimeError):
                    workflow.review('{"candidate":"Draft"}', workflow.DRAFT_CHECK_SCHEMA,
                                    root/'fail', workflow.DRAFT_CHECK)
                self.assertFalse((root/'fail/answer.json').exists())

    def test_publication_file_contains_markdown_not_the_chat_copy_fence(self):
        selection = self.selection('compose')
        selection['medium'] = 'pr_body'
        body = '## Result\n\n[Evidence](https://example.com/change)\n'
        for supplied in (body, '````markdown\n' + body.rstrip() + '\n````'):
            with self.subTest(supplied=supplied):
                actual = workflow.generate(selection, 'request', {}, lambda *args: {
                    'content': supplied, 'delivery_notes': ''})
                self.assertEqual(actual, body.rstrip())

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
                'if "--version" in sys.argv: print("codex-cli fixture"); raise SystemExit(0)\n'
                'schema=json.loads(pathlib.Path(sys.argv[sys.argv.index("--output-schema")+1]).read_text())\n'
                f'value={intake!r} if "conversation_response" in schema["properties"] else ({selection!r} if "operation" in schema["properties"] else {{"replacements":["changed"]}})\n'
                'pathlib.Path(sys.argv[sys.argv.index("-o")+1]).write_text(json.dumps(value))\n'
                'print(json.dumps({"type":"turn.completed","usage":{"input_tokens":1}}))\n')
            stub.chmod(0o700)
            reviewer = root / 'review-stub'
            reviewer.write_text('#!' + sys.executable + '\nprint(\'{"edits": [], "retained_qualifications": [], "delivery_notes": ""}\')\n')
            reviewer.chmod(0o700)
            import os
            env = dict(os.environ, CLAUDE_STRATEGIC_REVIEW_WRAPPER=str(reviewer))
            result = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'compose_from_sources.py'),
                '--request-file', str(root / 'request.txt'), '--source-file', str(root / 'source.txt'),
                '--output', str(root / 'output.txt'), '--work-dir', str(root / 'work'),
                '--codex-bin', str(stub), '--model', 'fixture', '--reasoning', 'medium'], capture_output=True, text=True, env=env)
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
                'if "--version" in sys.argv: print("codex-cli fixture"); raise SystemExit(0)\n'
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
            with patch.object(workflow, 'review', return_value={'edits': [], 'retained_qualifications': []}):
                workflow.run(root / 'request.txt', root / 'source.txt', root / 'output.txt', root / 'work',
                             stub, 'fixture', 'medium')
            self.assertEqual((root / 'output.txt').read_text(), 'current draft.')

    def test_actual_draft_check_restores_missing_group_and_removes_unnecessary_qualification(self):
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
                if target.name == 'draft-check':
                    self.assertIn('evidence_blocks', packet)
                    self.assertEqual(packet['candidate_blocks'][0]['text'], 'First result. Unrelated limit.')
                    return {'edits': [{'block_id': 'candidate:0', 'replacement': 'First result. Second result.',
                        'evidence_ids': ['source_material:0'],
                        'reason': 'Restore requested result instead of an unrelated qualification.'}],
                        'retained_qualifications': []}
                self.assertEqual([p['point'] for p in packet['outline']], ['First result.'])
                self.assertNotIn('source_material', packet)
                return {'content': 'First result. Unrelated limit.', 'delivery_notes': ''}
            with patch.object(workflow, 'native', native), patch.object(workflow, 'review', native):
                workflow.run(root / 'request.txt', root / 'source.txt', root / 'output.txt', root / 'work',
                             root / 'unused', 'fixture', 'medium')
            self.assertEqual(calls, ['intake', 'selection', 'generation', 'draft-check'])
            self.assertEqual((root / 'output.txt').read_text(), 'First result. Second result.')



    def test_draft_check_preserves_unedited_text_and_rejects_invented_sources(self):
        draft = 'Mechanism.\nUnneeded limit.\nRequired action.'
        sources = {'current_request': 'Explain mechanism and action.', 'source_material': 'Mechanism verified.'}
        result = {'edits': [{'block_id': 'candidate:1', 'replacement': '',
                            'evidence_ids': ['current_request:0'], 'reason': 'No reader consequence.'}],
                  'retained_qualifications': []}
        self.assertEqual(workflow.check_draft(draft, sources, lambda *a: result), 'Mechanism.\n\nRequired action.')
        result['edits'][0]['evidence_ids'] = ['invented:0']
        with self.assertRaises(ValueError):
            workflow.check_draft(draft, sources, lambda *a: result)
        result = {'edits': [], 'retained_qualifications': [{'kind': 'input_scope',
            'block_id': 'candidate:0', 'consequence': '', 'evidence_ids': ['source_material:0']}]}
        with self.assertRaisesRegex(ValueError, 'consequence'):
            workflow.check_draft(draft, sources, lambda *a: result)

    def test_block_ids_select_duplicate_text_without_fuzzy_matching(self):
        draft = 'Same.\nKeep.\nSame.'
        sources = {'current_request': 'Change the last occurrence.', 'source_material': 'Changed.'}
        result = {'edits': [{'block_id': 'candidate:2', 'replacement': 'Changed.',
                            'evidence_ids': ['current_request:0'], 'reason': 'Requested last occurrence.'}],
                  'retained_qualifications': []}
        self.assertEqual(workflow.check_draft(draft, sources, lambda *a: result), 'Same.\nKeep.\nChanged.')
        result['edits'][0]['block_id'] = 'candidate:99'
        with self.assertRaises(ValueError):
            workflow.check_draft(draft, sources, lambda *a: result)

    def test_saved_draft_uses_one_check_and_does_not_regenerate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'request').write_text('Explain result.')
            (root/'sources').write_text('Result is verified.')
            (root/'draft').write_text('Result. Unneeded limit.')
            calls = []
            def native(prompt, schema, target, *args):
                calls.append(target.name)
                return {'edits': [{'block_id': 'candidate:0', 'replacement': 'Result.',
                    'evidence_ids': ['source_material:0'], 'reason': 'Unrelated limit.'}],
                    'delivery_notes': 'An unresolved secondary check.', 'retained_qualifications': []}
            with patch.object(workflow, 'native', native), patch.object(workflow, 'review', native):
                workflow.run(root/'request', root/'sources', root/'out', root/'work',
                             root/'unused', 'fixture', 'medium', root/'draft')
            self.assertEqual(calls, ['draft-check'])
            self.assertEqual((root/'out').read_text(), 'Result.')
            self.assertEqual((root/'draft').read_text(), 'Result. Unneeded limit.')
            self.assertEqual((root/'work/delivery-notes.md').read_text(), 'An unresolved secondary check.\n')
            self.assertNotIn('unresolved', (root/'out').read_text())

    def test_unknown_body_result_requires_a_current_user_request(self):
        sources = {'current_request': 'Report the findings.', 'source_material': 'The amount is unavailable.'}
        qualification = {'kind': 'requested_unknown', 'block_id': 'candidate:0',
            'consequence': 'Reports availability.', 'evidence_ids': ['source_material:0']}
        result = {'edits': [], 'retained_qualifications': [qualification]}
        with self.assertRaises(ValueError):
            workflow.check_draft('The amount is unavailable.', sources, lambda *args: result)
        sources['current_request'] = 'Report whether the amount is available.'
        qualification['evidence_ids'] = ['current_request:0']
        self.assertEqual(workflow.check_draft('The amount is unavailable.', sources, lambda *args: result),
                         'The amount is unavailable.')

    def test_slack_layout_preserves_body_and_requires_parent_for_details(self):
        slack_heading = workflow.format_slack('*Result*\nSame input.', lambda *args: {
            'mode': 'report', 'blocks': [{'kind': 'heading', 'text': 'Result'},
                {'kind': 'bullet', 'text': 'Same input.'}]})
        self.assertEqual(slack_heading, '`Result`\n\n- Same input.')
        emphasis = workflow.format_slack('A **marked** point.\nUse `x**2**y`.', lambda *args: {
            'mode': 'report', 'blocks': [{'kind': 'label', 'text': 'Result'},
                {'kind': 'bullet', 'text': 'A marked point.'}, {'kind': 'child', 'text': 'Use `x**2**y`.'}]})
        self.assertIn('`x**2**y`', emphasis)
        image_heading = workflow.format_slack('**Comparison**\nSame input.\n![view](/tmp/example.png)', lambda *args: {
            'mode': 'report', 'blocks': [{'kind': 'heading', 'text': 'Comparison'},
                {'kind': 'bullet', 'text': 'Same input.'},
                {'kind': 'paragraph', 'text': '![view](/tmp/example.png)'}]})
        self.assertIn('![view](/tmp/example.png)', image_heading)
        original = "確認結果\n待ち時間は5秒。\n再読み込みで復旧する。"
        blocks = [
            {'kind': 'heading', 'text': '確認結果'},
            {'kind': 'bullet', 'text': '待ち時間は5秒。'},
            {'kind': 'child', 'text': '再読み込みで復旧する。'},
        ]
        result = workflow.format_slack(original, lambda *args: {'mode': 'report', 'blocks': blocks})
        self.assertEqual(result, '`確認結果`\n\n- 待ち時間は5秒。\n  - 再読み込みで復旧する。')
        changed = [dict(block) for block in blocks]
        changed[1]['text'] = '待ち時間は3秒。'
        with self.assertRaisesRegex(ValueError, 'changed body'):
            workflow.format_slack(original, lambda *args: {'mode': 'report', 'blocks': changed})
        with self.assertRaisesRegex(ValueError, 'needs section headings'):
            workflow.format_slack('詳細。続き。', lambda *args: {
                'mode': 'report', 'blocks': [{'kind': 'heading', 'text': '詳細。'}, {'kind': 'child', 'text': '続き。'}]})
        with self.assertRaisesRegex(ValueError, 'no parent'):
            workflow.format_slack('確認結果。詳細。要点。', lambda *args: {
                'mode': 'report', 'blocks': [
                    {'kind': 'heading', 'text': '確認結果。'},
                    {'kind': 'child', 'text': '詳細。'},
                    {'kind': 'bullet', 'text': '要点。'}]})
        with self.assertRaisesRegex(ValueError, 'must stay plain'):
            workflow.format_slack('確認します。', lambda *args: {
                'mode': 'reply', 'blocks': [{'kind': 'bullet', 'text': '確認します。'}]})
        separated = workflow.format_slack('要確認\n接続確認、表示確認', lambda *args: {
            'mode': 'report', 'blocks': [
                {'kind': 'heading', 'text': '要確認'},
                {'kind': 'bullet', 'text': '接続確認'},
                {'kind': 'bullet', 'text': '表示確認'}]})
        self.assertEqual(separated, '`要確認`\n\n- 接続確認\n- 表示確認')
        short = '共有ありがとうございます。確認します。'
        self.assertEqual(workflow.format_slack(short, lambda *args: {
            'mode': 'reply', 'blocks': [{'kind': 'paragraph', 'text': short}]}), short)

    def test_unchanged_slack_edit_still_uses_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = 'Slack文面を確認。'
            draft = '完了事項\n確認済み。'
            (root / 'request.txt').write_text(request)
            (root / 'source.txt').write_text(draft)
            calls = []
            def native(prompt, schema, target, instruction, *runtime):
                calls.append(target.name)
                if target.name == 'intake':
                    return {'operation': 'edit', 'medium': 'slack',
                            'request_quote': request, 'draft_quote': '', 'conversation_response': ''}
                if target.name == 'selection':
                    return {'operation': 'edit', 'request_quote': request, 'reason': 'Check.',
                            'draft_source': 'source_material', 'draft_quote': draft,
                            'corrections': [], 'outline': []}
                if target.name == 'draft-check':
                    self.assertEqual(json.loads(prompt)['editing_baseline'], draft)
                    return {'edits': [], 'retained_qualifications': []}
                self.assertEqual(target.name, 'layout')
                self.assertEqual(json.loads(prompt)['medium'], 'slack')
                return {'mode': 'report', 'blocks': [{'kind': 'heading', 'text': '完了事項'},
                                   {'kind': 'bullet', 'text': '確認済み。'}]}
            with patch.object(workflow, 'native', native), patch.object(workflow, 'review', native):
                workflow.run(root / 'request.txt', root / 'source.txt', root / 'output.txt',
                             root / 'work', root / 'unused', 'fixture', 'medium')
            self.assertEqual(calls, ['intake', 'selection', 'draft-check', 'layout'])
            self.assertEqual((root / 'output.txt').read_text(), '`完了事項`\n\n- 確認済み。')



    def test_continued_writing_inherits_medium_but_current_explicit_medium_wins(self):
        for intake_medium in ('other', 'pr_body'):
            with self.subTest(medium=intake_medium), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / 'request.txt').write_text('まとめて。')
                (root / 'source.txt').write_text('確認済み。')
                calls = []
                def native(prompt, schema, target, instruction, *runtime):
                    calls.append(target.name)
                    if target.name == 'intake':
                        return {'operation': 'compose', 'medium': intake_medium,
                                'request_quote': 'まとめて。', 'draft_quote': '', 'conversation_response': ''}
                    if target.name == 'selection':
                        if intake_medium == 'pr_body':
                            self.assertEqual(schema['properties']['medium']['enum'], ['pr_body'])
                        return {'operation': 'compose', 'medium': 'slack', 'request_quote': 'まとめて。',
                                'reason': 'Continued task.', 'corrections': [],
                                'outline': [{'point': '確認済み。', 'evidence': [
                                    {'source': 'source_material', 'quote': '確認済み。', 'role': 'Fact.'}]}]}
                    if target.name == 'draft-check':
                        return {'edits': [], 'retained_qualifications': []}
                    if target.name == 'generation':
                        return {'content': '確認済み。', 'delivery_notes': ''}
                    self.assertEqual(target.name, 'layout')
                    return {'mode': 'reply', 'blocks': [{'kind': 'paragraph', 'text': '確認済み。'}]}
                with patch.object(workflow, 'native', native), patch.object(workflow, 'review', native):
                    workflow.run(root / 'request.txt', root / 'source.txt', root / 'output.txt',
                                 root / 'work', root / 'unused', 'fixture', 'medium')
                self.assertEqual('layout' in calls, intake_medium == 'other')


if __name__ == '__main__':
    unittest.main()
