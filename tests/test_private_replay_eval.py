"""Synthetic fixtures only; exercise comparison failures, never call a model."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'evals/instruction-load'))
spec = importlib.util.spec_from_file_location('private_replay', ROOT / 'evals/instruction-load/replay.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2))


class ReplayTests(unittest.TestCase):
    def seed_pair(self, root):
        root.mkdir(parents=True, exist_ok=True)
        rubric = {'checks': [{'id': 'content', 'description': 'Preserve the requested state.'}]}
        rubric_path = root / 'rubric.json'
        write(rubric_path, rubric)
        for label in ('a', 'b'):
            run = root / label
            (run / 'project').mkdir(parents=True)
            (run / 'project/.agents/skills/sample').mkdir(parents=True)
            (run / 'project/.agents/skills/sample/SKILL.md').write_text(label)
            (run / 'answer.txt').write_text('The task is pending.')
            (run / 'project/draft.txt').write_text('The task is pending.')
            write(run / 'manifest.json', {**dict.fromkeys(
                ('case', 'request_sha256', 'scope_sha256', 'seed_sha256', 'model', 'reasoning'), 'same'),
                'rubric_sha256': replay.digest(rubric_path), 'initial_files': {},
                'skill_files': replay.skill_receipt(run / 'project/.agents/skills')})
            receipt = replay.artifact_receipt(run)
            write(run / 'result.json', {'pass': None, 'artifacts': receipt,
                'skill_snapshot_unchanged': True, 'seconds': 1, 'native_usage': [],
                'command_executions': 0, 'skill_read_commands': []})
            write(run / 'assessment.json', {'artifacts': receipt,
                'rubric_sha256': replay.digest(rubric_path),
                'checks': [{'id': 'content', 'verdict': 'pass', 'reason': 'Pending state preserved.',
                            'evidence': [{'file': 'project/draft.txt', 'quote': 'pending'}]}]})
        return rubric_path

    def compare(self, root, rubric):
        return replay.compare(root / 'a', root / 'b', root / 'a/assessment.json', root / 'b/assessment.json', rubric)

    def mutate(self, path, change):
        data = replay.read_json(path)
        change(data)
        write(path, data)

    def test_complete_pair_retains_actual_text_and_unknown_correction_count(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rubric = self.seed_pair(root)
            report = self.compare(root, rubric)
            self.assertTrue(report['before']['pass'])
            self.assertEqual(report['after']['drafts']['project/draft.txt'], 'The task is pending.')
            self.assertIsNone(report['after']['human_corrections'])

    def test_incomparable_input_model_scope_seed_or_rubric_is_rejected(self):
        for field in ('request_sha256', 'scope_sha256', 'seed_sha256', 'model', 'reasoning', 'initial_files', 'rubric_sha256'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                rubric = self.seed_pair(root)
                self.mutate(root / 'b/manifest.json', lambda d: d.update({field: 'different'}))
                with self.assertRaisesRegex(ValueError, 'Incomparable'):
                    self.compare(root, rubric)

    def test_tampering_output_assessment_or_rubric_cannot_pass(self):
        for fault in ('answer', 'draft', 'receipt', 'rubric', 'criterion', 'quote', 'empty-evidence', 'rubric-binding'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                rubric = self.seed_pair(root)
                assessment = root / 'b/assessment.json'
                if fault == 'answer':
                    (root / 'b/answer.txt').write_text('Changed')
                elif fault == 'draft':
                    (root / 'b/project/draft.txt').unlink()
                elif fault == 'rubric':
                    rubric.write_text('{}')
                elif fault == 'receipt':
                    self.mutate(assessment, lambda d: d.update(artifacts={}))
                elif fault == 'criterion':
                    self.mutate(assessment, lambda d: d.update(checks=[]))
                elif fault == 'quote':
                    self.mutate(assessment, lambda d: d['checks'][0]['evidence'][0].update(quote='not in artifact'))
                elif fault == 'rubric-binding':
                    self.mutate(assessment, lambda d: d.update(rubric_sha256='different'))
                else:
                    self.mutate(assessment, lambda d: d['checks'][0].update(evidence=[]))
                with self.assertRaises(ValueError):
                    self.compare(root, rubric)

    def test_failure_unknown_and_snapshot_mutation_are_not_promoted(self):
        for fault, expected in [('failed-process', False), ('unknown', None), ('content', False), ('snapshot', False), ('late-snapshot-edit', False)]:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                rubric = self.seed_pair(root)
                if fault == 'failed-process':
                    self.mutate(root / 'b/result.json', lambda d: d.update({'pass': False}))
                elif fault == 'snapshot':
                    self.mutate(root / 'b/result.json', lambda d: d.update(skill_snapshot_unchanged=False))
                elif fault == 'late-snapshot-edit':
                    (root / 'b/project/.agents/skills/sample/SKILL.md').write_text('changed after execution')
                else:
                    self.mutate(root / 'b/assessment.json', lambda d: d['checks'][0].update(verdict='unknown' if fault == 'unknown' else 'fail'))
                self.assertIs(self.compare(root, rubric)['after']['pass'], expected)

    def test_native_setup_failure_is_not_an_assessment_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'request.txt').write_text('Explain the current state.')
            (root / 'scope.txt').write_text('Read only.')
            (root / 'seed.jsonl').write_text(json.dumps({'type': 'session_meta', 'payload': {'id': 'sample'}}))
            (root / 'rubric.json').write_text('{}')
            (root / 'skills/sample').mkdir(parents=True)
            (root / 'skills/sample/SKILL.md').write_text('sample')
            stub = root / 'codex-stub'
            stub.write_text('#!' + sys.executable + '\nraise SystemExit(7)\n')
            stub.chmod(0o700)
            write(root / 'case.json', {'id': 'sample', 'request_file': 'request.txt',
                'scope_file': 'scope.txt', 'seed_file': 'seed.jsonl', 'rubric_file': 'rubric.json',
                'session_id': 'sample', 'model': 'sample', 'reasoning': 'sample'})
            run = replay.run_case(root / 'case.json', root / 'skills', root / 'results', stub, 'condition-hidden')
            self.assertNotIn('condition-hidden', str(run))
            result = replay.read_json(run / 'result.json')
            self.assertEqual(result['process_exit'], 7)
            self.assertEqual(result['execution_status'], 'native_error')
            self.assertFalse(result['pass'])
            self.assertEqual(result['native_usage'], [])

    def seed_suite(self, root):
        plan = []
        for name in ('one', 'two'):
            folder = root / name
            rubric = self.seed_pair(folder)
            for side in ('a', 'b'):
                self.mutate(folder / side / 'manifest.json', lambda d: d.update(case=name))
            plan.append({'case': name, 'before': str(folder / 'a'), 'after': str(folder / 'b'),
                         'before_assessment': str(folder / 'a/assessment.json'),
                         'after_assessment': str(folder / 'b/assessment.json'), 'rubric_file': str(rubric)})
        write(root / 'cases.json', {'cases': ['one', 'two']})
        write(root / 'plan.json', {'comparisons': plan})

    def test_suite_retains_regression_and_cannot_omit_a_declared_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.seed_suite(root)
            self.mutate(root / 'two/b/assessment.json', lambda d: d['checks'][0].update(verdict='fail'))
            result = replay.suite(root / 'cases.json', root / 'plan.json')
            self.assertEqual(result['regressions'], ['two'])
            self.assertEqual(result['adoption'], 'not_ready')
            self.mutate(root / 'plan.json', lambda d: d['comparisons'].pop())
            with self.assertRaisesRegex(ValueError, 'every declared'):
                replay.suite(root / 'cases.json', root / 'plan.json')

    def test_suite_rejects_mixing_successes_from_different_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.seed_suite(root)
            self.mutate(root / 'two/b/manifest.json', lambda d: d.update(skill_files={'sample': 'another candidate'}))
            with self.assertRaisesRegex(ValueError, 'different snapshots'):
                replay.suite(root / 'cases.json', root / 'plan.json')

    def test_actor_gets_request_and_scope_but_not_label_or_rubric(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'request.txt').write_text('Explain the current state.')
            (root / 'scope.txt').write_text('Read only.')
            (root / 'seed.jsonl').write_text(json.dumps({'type': 'session_meta', 'payload': {'id': 'sample'}}))
            (root / 'rubric.json').write_text('{"criterion":"HIDDEN-CRITERION"}')
            (root / 'skills/sample').mkdir(parents=True)
            (root / 'skills/sample/SKILL.md').write_text('sample')
            stub = root / 'codex-stub'
            stub.write_text('#!' + sys.executable + '\nimport json,pathlib,sys\n'
                'pathlib.Path("invocation.json").write_text(json.dumps({"args":sys.argv,"input":sys.stdin.read()}))\n'
                'pathlib.Path(sys.argv[sys.argv.index("-o")+1]).write_text("Pending.")\n')
            stub.chmod(0o700)
            write(root / 'case.json', {'id': 'sample', 'request_file': 'request.txt',
                'scope_file': 'scope.txt', 'seed_file': 'seed.jsonl', 'rubric_file': 'rubric.json',
                'session_id': 'sample', 'model': 'sample', 'reasoning': 'sample'})
            run = replay.run_case(root / 'case.json', root / 'skills', root / 'results', stub, 'HIDDEN-LABEL')
            invocation = (run / 'project/invocation.json').read_text()
            self.assertNotIn('HIDDEN-LABEL', invocation)
            self.assertNotIn('HIDDEN-CRITERION', invocation)
            self.assertNotIn(str(root / 'rubric.json'), invocation)
            self.assertEqual(json.loads(invocation)['input'], 'Explain the current state.')
            self.assertIsNone(replay.read_json(run / 'result.json')['pass'])


if __name__ == '__main__':
    unittest.main()
