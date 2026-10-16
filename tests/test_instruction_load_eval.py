import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'evals/instruction-load/evaluate.py'
spec = importlib.util.spec_from_file_location('instruction_load_eval', SCRIPT)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class InstructionLoadAcceptanceTests(unittest.TestCase):
    def test_real_file_link_defect_is_reported_separately_from_artifact_success(self):
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory)
            (task / 'caller.py').write_text('pass\n')
            self.assertFalse(study.answer_links(task, '[原因](caller.py:4)')['pass'])
            self.assertTrue(study.answer_links(task, f'[原因]({task}/caller.py:4)')['pass'])
            self.assertTrue(study.answer_links(task, '[文書](https://example.com/page) [節](#section)')['pass'])
            self.assertTrue(study.answer_links(task, '[文書](unrelated.md)')['pass'])

    def test_real_artifacts_accept_and_known_faults_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            for case in study.CASES:
                with self.subTest(case=case):
                    task = Path(directory) / case
                    study.seed(case, task)
                    start = study.hashes(task)
                    original = {p.relative_to(task).as_posix(): p.read_text() for p in task.rglob('*') if p.is_file()}

                    def check(answer, expected):
                        before_check = study.hashes(task)
                        self.assertEqual(study.check(case, task, answer, start, original)['artifact_checks_pass'], expected)
                        self.assertEqual(study.hashes(task), before_check, 'The observer must not repair the actor output')

                    if case == 'continuation':
                        check('done', False)
                        p = task / 'report.py'
                        p.write_text(p.read_text().replace("summarize(args.input, 'UTC')", 'summarize(args.input, args.timezone)'))
                        (task / 'report.csv').write_text('day,units\n2026-01-04,2\n2026-01-05,8\n')
                        check('done', True)
                        p.write_text(p.read_text().replace('summarize(args.input, args.timezone)', "{'2026-01-04':2,'2026-01-05':8}"))
                        check('done', False)
                    elif case == 'label':
                        check('done', False)
                        p = task / 'view.py'
                        p.write_text(p.read_text().replace("'done': '終了'", "'done': '完了'"))
                        check('done', True)
                        p.write_text(p.read_text().replace("'running': '実行中'", "'running': '稼働中'"))
                        check('done', False)
                        p.unlink()
                        check('done', False)
                    elif case == 'serialization':
                        check('done', False)
                        p = task / 'encode.py'
                        p.write_text(p.read_text().replace("str(record['count'])", "record['count']"))
                        check('done', True)
                        p.write_text(p.read_text().replace("if 'note' in record:", "if record.get('note'):"))
                        check('done', False)
                    elif case == 'wording':
                        expected = original['draft.txt'].strip().replace('検索改善の確認会', '検索候補の確認会')
                        check(expected, True)
                        check(expected.replace('録画は残しません。', ''), False)
                    else:
                        check('read only', True)
                        (task / '__pycache__').mkdir()
                        cache = task / '__pycache__/hidden.pyc'
                        cache.write_bytes(b'unexpected')
                        check('read only', False)
                        cache.unlink()
                        (task / 'nested').mkdir()
                        (task / 'nested/change.txt').write_text('unexpected')
                        check('read only', False)

    def test_native_failure_empty_answer_and_unreviewed_explanation_never_pass(self):
        self.assertFalse(study.verdict('label', True, 1, 'done'))
        self.assertFalse(study.verdict('label', True, 0, ' \n'))
        self.assertFalse(study.verdict('label', False, 0, 'done'))
        for case in study.MANUAL:
            with self.subTest(case=case):
                self.assertIsNone(study.verdict(case, True, 0, 'not yet assessed'))
        self.assertTrue(study.verdict('label', True, 0, 'done'))

    def test_cli_does_not_turn_no_changes_or_failure_into_success(self):
        for case, native_exit, expect_review in [('label', 0, False), ('stop', 1, False), ('investigation', 0, True)]:
            with self.subTest(case=case, native_exit=native_exit), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                stub = root / 'codex-stub'
                stub.write_text('#!' + sys.executable + '\nimport pathlib,sys\n'
                    'pathlib.Path(sys.argv[sys.argv.index("-o")+1]).write_text("No changes")\n'
                    f'raise SystemExit({native_exit})\n')
                stub.chmod(0o700)
                run = subprocess.run([sys.executable, '-B', str(SCRIPT), '--output-dir', str(root / 'results'), '--label', 'plumbing', '--case', case, '--codex-bin', str(stub)], text=True, capture_output=True)
                self.assertEqual(run.returncode, 1, run.stderr)
                result = json.loads(next((root / 'results').glob('*/result.json')).read_text())
                self.assertIs(result['pass'], None if expect_review else False)
                self.assertEqual(result['process_exit'], native_exit)


if __name__ == '__main__':
    unittest.main()
