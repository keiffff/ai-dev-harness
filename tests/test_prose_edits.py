import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'codex/skills/codex-writing/scripts/apply_edits.py'
spec = importlib.util.spec_from_file_location('prose_edits', SCRIPT)
edits = importlib.util.module_from_spec(spec)
spec.loader.exec_module(edits)


class ProseEditTests(unittest.TestCase):
    def test_only_selected_spans_change_and_empty_plan_preserves_everything(self):
        draft = '見積は7件。\n観測は2件。\n確認は未実施。\n'
        correction = {'old': '確認は未実施。', 'source': 'notes', 'quote': '確認済み。', 'reason': 'State corrected.'}
        self.assertEqual(edits.apply_edits(draft, [correction], ['確認済み。'], {'notes': '確認済み。'}),
                         '見積は7件。\n観測は2件。\n確認済み。\n')
        self.assertEqual(edits.apply_edits(draft, [], [], {}), draft)

    def test_invalid_or_ambiguous_plan_is_rejected_before_applying_any_edit(self):
        good = {'old': 'ab', 'source': 'notes', 'quote': 'source', 'reason': 'Supported.'}
        cases = [('ab ab', [good], ['x']), ('abcd', [good, {**good, 'old': 'bc'}], ['x', 'y']),
                 ('abcd', [good], []), ('abcd', [{**good, 'quote': 'invented'}], ['x']),
                 ('abcd', [{**good, 'old': ''}], ['x']), ('abcd', [{**good, 'old': 'missing'}], ['x'])]
        for draft, plan, replacements in cases:
            with self.subTest(draft=draft, plan=plan):
                with self.assertRaises(ValueError):
                    edits.apply_edits(draft, plan, replacements, {'notes': 'source'})

    def test_multiple_edits_keep_original_offsets(self):
        draft = 'first; keep; last'
        plan = [{'old': old, 'source': 'notes', 'quote': 'source', 'reason': 'Requested.'} for old in ('first', 'last')]
        self.assertEqual(edits.apply_edits(draft, plan, ['a longer first', 'end'], {'notes': 'source'}),
                         'a longer first; keep; end')


if __name__ == '__main__':
    unittest.main()
