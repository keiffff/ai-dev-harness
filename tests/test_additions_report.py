"""Exercise observation boundaries with synthetic files, without Git mutation."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('additions_report', ROOT / 'hooks/codex/additions_report.py')
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class AdditionsReportTests(unittest.TestCase):
    def test_staged_new_files_and_added_calls_are_observed_without_semantic_verdicts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'client.py').write_text('requests.get("https://example.invalid")\nif enabled:\n    timeout = 2\n')
            (root / 'test_client.py').write_text('assert True\n')
            (root / '.env.local').write_text('not exported')
            replies = {
                ('rev-parse', '--verify', 'HEAD^{commit}'): 'commit',
                ('ls-tree', '-r', '--name-only', '-z', 'HEAD'): 'client.py\0',
                ('diff', '--name-only', '-z', 'HEAD', '--'): 'client.py\0test_client.py\0.env.local\0',
                ('ls-files', '--others', '--exclude-standard', '-z'): '',
                ('show', 'HEAD:client.py'): 'requests.get("https://example.invalid")\n',
            }
            with patch.object(report, 'git', side_effect=lambda _, *args: replies[args]):
                result = report.observe(root)
            self.assertEqual(result['new_files'], ['test_client.py'])
            self.assertEqual(result['new_test_files'], ['test_client.py'])
            self.assertNotIn('.env.local', str(result))
            self.assertNotIn('external_call_pattern', str(result['added_patterns']))
            self.assertEqual(result['added_patterns'][0]['line'], 2)
            self.assertNotIn('unrequested', result)
            self.assertNotIn('not exported', str(result))

    def test_invalid_base_is_an_error_not_a_clean_observation(self):
        with patch.object(report, 'git', side_effect=ValueError('invalid base')):
            with self.assertRaisesRegex(ValueError, 'invalid base'):
                report.observe(Path('/unused'))


if __name__ == '__main__':
    unittest.main()
