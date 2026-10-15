import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('work_memory_index', ROOT / 'codex/skills/codex-learn-from-work/scripts/sync_record_index.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class WorkMemoryIndexTests(unittest.TestCase):
    def test_corrected_entry_replaces_stale_search_facts_without_altering_other_records(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            index = root / 'records.json'
            unchanged = {'id': 'B2', 'body': 'unrelated', 'state': 'pending', 'sources': [['source', 'item']], 'other': {'value': 3}}
            index.write_text(json.dumps({'records': [{'id': 'A1', 'body': 'old claim', 'state': 'unverified', 'sources': [['original', 'item']]}, unchanged], 'policy': 'preserve'}))
            entry = root / 'topic.md'
            entry.write_text('# Topic\n\n## A1 Timing verification\n\nThe live behavior was checked; device acceptance remains open.\n\n**確認状態：** 実測済み。\n\n## B2 Other entry\nDo not copy this section.\n')
            module.sync_record(index, entry, 'A1')
            data = json.loads(index.read_text())
            self.assertEqual(data['records'][0]['state'], '実測済み')
            self.assertIn('device acceptance remains open', data['records'][0]['body'])
            self.assertNotIn('old claim', data['records'][0]['body'])
            self.assertNotIn('Do not copy', data['records'][0]['body'])
            self.assertEqual(data['records'][0]['sources'], [['original', 'item']])
            self.assertEqual(data['records'][1], unchanged)
            self.assertEqual(data['policy'], 'preserve')

    def test_ambiguous_source_does_not_rewrite_index(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            index, entry = root / 'records.json', root / 'topic.md'
            original = json.dumps({'records': [{'id': 'A1', 'body': 'retain', 'state': 'unknown'}]})
            index.write_text(original)
            entry.write_text('## A1 First\n**確認状態：** one\n## A1 Second\n**確認状態：** two\n')
            with self.assertRaises(ValueError):
                module.sync_record(index, entry, 'A1')
            self.assertEqual(index.read_text(), original)


if __name__ == '__main__':
    unittest.main()
