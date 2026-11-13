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
    def test_final_note_filter_can_only_remove_identified_original_lines(self):
        body = 'Verified mechanism.\nInternal status.\nRequested action.'
        updated, removed = workflow.remove_sender_notes(body, 'Explain the mechanism and action.', [],
            lambda *args: {'remove': [{'block_id': 'body:1', 'reason': 'Sender work record.'}]})
        self.assertEqual(updated, 'Verified mechanism.\n\nRequested action.')
        self.assertEqual(removed[0]['text'], 'Internal status.')
        for invalid in [
            [{'block_id': 'body:99', 'reason': 'Invented line.'}],
            [{'block_id': 'body:1', 'reason': 'Duplicate.'}]*2]:
            with self.assertRaises(ValueError):
                workflow.remove_sender_notes(body, 'Explain.', [], lambda *args: {'remove': invalid})
        retained, removed = workflow.remove_sender_notes(body, 'Explain.', [],
            lambda *args: {'remove': [{'block_id': 'body:2', 'reason': 'Misclassified action.'}]},
            protected_texts=['Requested action.'])
        self.assertEqual(retained, body)
        self.assertEqual(removed, [])

    def composition_inputs(self, root, pending=None):
        (root/'request').write_text('Explain the change to the reader.')
        (root/'sources').write_text('The existing handler selects the stored item.')
        (root/'handoff').write_text(json.dumps({'purpose': 'Explain the behavior.',
            'conclusion': 'The handler selects the stored item.',
            'required_points': ['Selection behavior'], 'pending_checks': pending or [],
            'body_limits': [], 'sender_notes': 'A useful sender note.'}))

    def test_pending_investigation_cannot_emit_a_body_or_call_the_writer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.composition_inputs(root, [{'question': 'Which handler is active?',
                'consequence': 'Determines the behavior.', 'next_read': 'Read deployed configuration.'}])
            with patch.object(workflow, 'review') as call:
                receipt = workflow.compose(root/'request', root/'sources', root/'handoff', root/'out', root/'work')
            call.assert_not_called()
            self.assertEqual(receipt['status'], 'needs_investigation')
            self.assertFalse((root/'out').exists())

    def test_composition_keeps_original_evidence_and_sender_notes_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.composition_inputs(root)
            def writer(prompt, schema, target, instruction):
                if 'remove' in schema['properties']: return {'remove': []}
                packet = json.loads(prompt)
                self.assertEqual(packet['current_request'], (root/'request').read_text())
                self.assertEqual(packet['source_material'], (root/'sources').read_text())
                self.assertNotIn('candidate_blocks', packet)
                self.assertNotIn('sender_notes', packet['handoff'])
                return {'status': 'ready', 'blocks': [{'kind': 'body', 'text': 'The handler selects the stored item.', 'limit_index': -1}],
                        'questions': [], 'delivery_notes': 'A sender note.'}
            with patch.object(workflow, 'review', side_effect=writer) as call:
                receipt = workflow.compose(root/'request', root/'sources', root/'handoff', root/'out', root/'work')
            self.assertEqual(call.call_count, 2)
            self.assertEqual(receipt['model_calls'], 2)
            self.assertEqual((root/'out').read_text(), 'The handler selects the stored item.')
            self.assertEqual((root/'work/delivery-notes.md').read_text(), 'A useful sender note.\nA sender note.\n')

    def test_uncertainty_with_the_same_action_is_not_a_body_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.composition_inputs(root)
            handoff = json.loads((root/'handoff').read_text())
            handoff['body_limits'] = [{'claim': 'The handler can select the wrong item.',
                'action_if_true': 'Fix the selection.', 'action_if_false': 'Fix the selection.'}]
            (root/'handoff').write_text(json.dumps(handoff))
            with patch.object(workflow, 'review') as call:
                with self.assertRaisesRegex(ValueError, 'different concrete actions'):
                    workflow.compose(root/'request', root/'sources', root/'handoff', root/'out', root/'work')
            call.assert_not_called()

    def test_unmatched_qualifications_cannot_enter_the_sendable_document(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.composition_inputs(root)
            result = {'status': 'ready', 'questions': [], 'delivery_notes': '', 'blocks': [
                {'kind': 'body', 'text': 'The handler selects the stored item.', 'limit_index': -1},
                {'kind': 'qualification', 'text': 'Unrelated historical proof is unavailable.', 'limit_index': -1},
                {'kind': 'sender_note', 'text': 'No code was edited during drafting.', 'limit_index': -1}]}
            with patch.object(workflow, 'review', side_effect=[result, {'remove': []}]):
                workflow.compose(root/'request', root/'sources', root/'handoff', root/'out', root/'work')
            self.assertEqual((root/'out').read_text(), 'The handler selects the stored item.')
            notes = (root/'work/delivery-notes.md').read_text()
            self.assertIn('historical proof', notes)
            self.assertIn('No code was edited', notes)
            result['blocks'][1]['limit_index'] = 0
            with patch.object(workflow, 'review', side_effect=[result, {'remove': []}]):
                with self.assertRaisesRegex(ValueError, 'existing body limit'):
                    workflow.compose(root/'request', root/'sources', root/'handoff', root/'out2', root/'invalid')

    def test_action_changing_limit_remains_with_its_answer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.composition_inputs(root)
            handoff = json.loads((root/'handoff').read_text())
            handoff['body_limits'] = [{'claim': 'The format can be read by the consumer.',
                'action_if_true': 'Use the existing consumer.', 'action_if_false': 'Update the consumer first.'}]
            (root/'handoff').write_text(json.dumps(handoff))
            result = {'status': 'ready', 'questions': [], 'delivery_notes': '', 'blocks': [
                {'kind': 'body', 'text': 'The producer writes the new format.', 'limit_index': -1},
                {'kind': 'qualification', 'text': 'Consumer compatibility determines the rollout order.', 'limit_index': 0}]}
            with patch.object(workflow, 'review', side_effect=[result, {'remove': []}]):
                workflow.compose(root/'request', root/'sources', root/'handoff', root/'out', root/'work')
            self.assertIn('determines the rollout order', (root/'out').read_text())

    def test_composition_rejects_a_previous_body_before_an_upstream_return(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.composition_inputs(root, [{'question': 'Which handler is active?'}])
            (root/'out').write_text('An earlier body.')
            with patch.object(workflow, 'review') as call:
                with self.assertRaisesRegex(ValueError, 'stale body'):
                    workflow.compose(root/'request', root/'sources', root/'handoff', root/'out', root/'work')
            call.assert_not_called()
            self.assertEqual((root/'out').read_text(), 'An earlier body.')

    def test_evidence_question_returns_upstream_without_a_partial_document(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.composition_inputs(root)
            result = {'status': 'needs_evidence', 'blocks': [], 'delivery_notes': '',
                      'questions': [{'question': 'Which result applies?', 'consequence': 'Sources contradict.'}]}
            with patch.object(workflow, 'review', side_effect=[result, {'remove': []}]):
                receipt = workflow.compose(root/'request', root/'sources', root/'handoff', root/'out', root/'work')
            self.assertEqual(receipt['status'], 'needs_evidence')
            self.assertFalse((root/'out').exists())
            self.assertTrue((root/'work/questions.json').exists())
            result['blocks'] = [{'kind': 'body', 'text': 'A partial document.', 'limit_index': -1}]
            with patch.object(workflow, 'review', side_effect=[result, {'remove': []}]):
                with self.assertRaisesRegex(ValueError, 'not both'):
                    workflow.compose(root/'request', root/'sources', root/'handoff', root/'out', root/'invalid')

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


    def test_saved_draft_keeps_literal_edits_and_final_note_filter(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'request').write_text('Explain result.')
            (root/'sources').write_text('Result is verified.')
            (root/'draft').write_text('Result. Unneeded limit.')
            calls = []
            def native(prompt, schema, target, *args):
                calls.append(target.name)
                if target.name == 'note-filter': return {'remove': []}
                return {'edits': [{'block_id': 'candidate:0', 'replacement': 'Result.',
                    'evidence_ids': ['source_material:0'], 'reason': 'Unrelated limit.'}],
                    'delivery_notes': 'An unresolved secondary check.', 'retained_qualifications': []}
            with patch.object(workflow, 'review', native):
                workflow.run(root/'request', root/'sources', root/'out', root/'work',
                             root/'unused', 'fixture', 'medium', root/'draft')
            self.assertEqual(calls, ['draft-check', 'note-filter'])
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


    def test_missing_main_draft_does_not_start_a_model(self):
        with patch.object(workflow, 'review') as reviewer:
            with self.assertRaisesRegex(ValueError, '--draft-file'):
                workflow.run(Path('request'), Path('sources'), Path('out'), Path('work'))
            reviewer.assert_not_called()

    def test_saved_edit_preserves_medium_notes_and_input_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'request').write_text('Report the result.')
            (root/'sources').write_text('Result verified.')
            (root/'draft').write_bytes(b'Result.\r\nKeep.\r\n')
            def reviewer(prompt, schema, target, instruction):
                if target.name == 'note-filter': return {'remove': []}
                self.assertEqual(json.loads(prompt)['medium'], 'slack')
                return {'edits': [], 'retained_qualifications': [], 'delivery_notes': 'Sender only.'}
            with patch.object(workflow, 'review', side_effect=reviewer) as call:
                receipt = workflow.run(root/'request', root/'sources', root/'out', root/'work',
                                       draft_file=root/'draft', medium='slack')
            self.assertEqual(call.call_count, 2)
            self.assertEqual(receipt['review_calls'], 2)
            self.assertEqual((root/'out').read_bytes(), (root/'draft').read_bytes())
            self.assertNotIn('Sender only', (root/'out').read_text())
            self.assertIn('Sender only', (root/'work/delivery-notes.md').read_text())
