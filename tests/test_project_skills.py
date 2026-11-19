import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HOOK_DIR = ROOT / 'hooks/codex'
spec = importlib.util.spec_from_file_location('project_skills', HOOK_DIR / 'project_skills.py')
skills = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skills)


class ProjectSkillsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.registry = self.root / 'private/registry.json'
        self.a = self.make_skill('project-a', 'verify-a')
        self.b = self.make_skill('project-b', 'verify-b')
        self.registry.parent.mkdir()
        self.registry.write_text(json.dumps({'/git/a': [str(self.a)], '/git/b': [str(self.b)]}))

    def make_skill(self, project, name):
        file = self.root / project / name / 'SKILL.md'
        file.parent.mkdir(parents=True)
        file.write_text(f'---\nname: {name}\ndescription: Verify the current project.\n---\nPRIVATE BODY {project}\n')
        return file

    def test_worktrees_share_only_the_registered_project(self):
        with patch.object(skills, 'common_directory', return_value='/git/a'):
            first = skills.skill_index(self.root / 'checkout', self.registry)
            second = skills.skill_index(self.root / 'another-worktree', self.registry)
        self.assertEqual(first, second)
        self.assertEqual([entry['id'] for entry in first['skills']], ['verify-a'])
        self.assertNotIn('PRIVATE BODY', json.dumps(first))
        self.assertNotIn('verify-b', json.dumps(first))

    def test_other_project_is_not_read_or_used_as_fallback(self):
        self.a.write_bytes(b'\xff')
        with patch.object(skills, 'common_directory', return_value='/git/b'):
            index = skills.skill_index(self.root, self.registry)
            body = skills.read_skill(self.root, 'verify-b', self.registry)
            with self.assertRaises(ValueError):
                skills.read_skill(self.root, 'verify-a', self.registry)
            with self.assertRaises(ValueError):
                skills.read_skill(self.root, '../../project-a/verify-a', self.registry)
        self.assertEqual([entry['id'] for entry in index['skills']], ['verify-b'])
        self.assertIn('PRIVATE BODY project-b', body)

    def test_unregistered_repository_returns_no_skills(self):
        with patch.object(skills, 'common_directory', return_value='/git/unregistered'):
            index = skills.skill_index(self.root, self.registry)
            with self.assertRaises(ValueError):
                skills.read_skill(self.root, 'verify-a', self.registry)
        self.assertEqual(index['skills'], [])

    def test_missing_registry_has_no_writes_or_git_probe(self):
        absent = self.root / 'absent/registry.json'
        with patch.object(skills, 'common_directory', side_effect=AssertionError('unneeded Git probe')):
            self.assertEqual(skills.skill_index(self.root, absent)['skills'], [])
        self.assertFalse(absent.parent.exists())

    def test_non_repository_has_no_skills_or_registration(self):
        self.assertEqual(skills.skill_index(self.root, self.registry)['skills'], [])
        with self.assertRaises(ValueError):
            skills.register(self.root, [self.a], self.registry)

    def test_registration_preserves_other_projects(self):
        replacement = self.make_skill('project-a', 'another-a')
        with patch.object(skills, 'common_directory', return_value='/git/a'):
            skills.register(self.root, [replacement], self.registry)
        data = json.loads(self.registry.read_text())
        self.assertEqual(data['/git/a'], [str(replacement.resolve())])
        self.assertEqual(data['/git/b'], [str(self.b)])
        self.assertEqual(self.registry.stat().st_mode & 0o777, 0o600)

    def test_context_replaces_prior_index_after_checkout_switch(self):
        with patch.dict(os.environ, {'CODEX_PROJECT_SKILLS_REGISTRY': str(self.registry)}):
            with patch.object(skills, 'common_directory', return_value='/git/a'):
                first = skills.render_context(str(self.root))
            with patch.object(skills, 'common_directory', return_value='/git/unregistered'):
                second = skills.render_context(str(self.root))
        self.assertIn('verify-a', first)
        self.assertIn('"skills": []', second)
        self.assertNotIn('verify-a', second)

    def test_unavailable_index_does_not_reuse_other_project(self):
        self.registry.write_text('not-json')
        with patch.dict(os.environ, {'CODEX_PROJECT_SKILLS_REGISTRY': str(self.registry)}):
            context = skills.render_context(str(self.root))
        self.assertIn('unavailable', context)
        self.assertNotIn('verify-a', context)
        self.assertNotIn('verify-b', context)

    def test_real_runtime_hook_delivers_index_and_restores_it_after_compaction(self):
        common = skills.common_directory(ROOT)
        self.registry.write_text(json.dumps({common: [str(self.a)]}))
        contract = self.root / 'contract.md'
        contract.write_text('test contract')
        env = dict(os.environ, CODEX_RUNTIME_CONTRACT=str(contract),
                   CODEX_RUNTIME_CONTRACT_STATE_DIR=str(self.root / 'state'),
                   CODEX_SOURCE_LEDGER_DIR=str(self.root / 'ledger'),
                   CODEX_PROJECT_SKILLS_REGISTRY=str(self.registry))
        def run(event, **extra):
            payload = {'hook_event_name': event, 'session_id': 'project-skill-test', 'cwd': str(ROOT), **extra}
            return subprocess.run(['python3', str(HOOK_DIR / 'runtime-contract-context.py')],
                                  input=json.dumps(payload), text=True, capture_output=True, env=env, check=True)
        first = run('UserPromptSubmit', prompt='Investigate the existing project behavior')
        repeated = run('UserPromptSubmit', prompt='Continue')
        compact = run('SessionStart', source='compact')
        for result in [first, compact]:
            context = json.loads(result.stdout)['hookSpecificOutput']['additionalContext']
            self.assertIn('verify-a', context)
            self.assertNotIn('PRIVATE BODY', context)
            self.assertNotIn('verify-b', context)
        self.assertEqual(repeated.stdout, '')


if __name__ == '__main__':
    unittest.main()
