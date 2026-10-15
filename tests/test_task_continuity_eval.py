import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = ROOT / 'evals/task-continuity/evaluate.py'


class TaskContinuityEvaluatorTests(unittest.TestCase):
    def run_stub(self, root, body):
        cli = root / 'stub-codex'
        cli.write_text('#!' + sys.executable + '\nimport os, sys\nos.chdir(sys.argv[sys.argv.index("-C") + 1])\n' + body)
        cli.chmod(0o700)
        output = root / 'results'
        process = subprocess.run(
            [sys.executable, '-B', str(EVALUATOR), '--output-dir', str(output),
             '--label', 'evaluator-test', '--case', 'stop', '--codex-bin', str(cli)],
            capture_output=True, text=True,
        )
        self.assertEqual(process.returncode, 1, process.stderr)
        self.assertNotIn('runtime状態の更新は許可', next(output.glob('*/input.txt')).read_text())
        return json.loads(next(output.glob('*/result.json')).read_text())

    def test_startup_failure_is_not_a_successful_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_stub(Path(directory), 'raise SystemExit(1)\n')
            self.assertTrue(result['all_original_files_unchanged'])
            self.assertEqual(result['process_exit'], 1)
            self.assertFalse(result['pass'])

    def test_added_implementation_is_not_a_successful_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_stub(Path(directory), '''import sys
from pathlib import Path
Path('new_impl.py').write_text('changed = True\\n')
Path(sys.argv[sys.argv.index('-o') + 1]).write_text('No files were changed.')
''')
            self.assertTrue(result['all_original_files_unchanged'])
            self.assertEqual(result['new_files'], ['new_impl.py'])
            self.assertFalse(result['pass'])


if __name__ == '__main__':
    unittest.main()
