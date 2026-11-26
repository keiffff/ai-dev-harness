import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'codex/ci'))
from publication import select_item_checks


class PublicationTests(unittest.TestCase):
    def test_wrapper_controls_merge_for_selected_paths(self):
        wrapper = ROOT / 'wrappers/bin/gh-user-approved.example'
        head = 'a' * 40
        repo = 'example/widgets'
        url = f'https://github.com/{repo}/pull/1'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / 'publication-sources.json'
            config.write_text(json.dumps({repo: [
                {'paths': ['worker/*'], 'workflow': 'ci.yml',
                 'job': 'runtime', 'step': 'Compatibility', 'base': 'main'},
            ]}))
            gh = root / 'gh'
            gh.write_text('''#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
head = "a" * 40
if args[:2] == ["pr", "view"]:
    print(json.dumps(dict(url="https://github.com/example/widgets/pull/1",
                          baseRefOid="b" * 40, headRefOid=head, baseRefName="main")))
elif args[:2] == ["pr", "merge"]:
    print(json.dumps(args))
elif "workflows/" in args[-1]:
    print(json.dumps({"workflow_runs": [dict(head_sha=head, id=3, run_attempt=2)]}))
elif "runs/3/attempts/2/jobs" in args[-1]:
    status = os.environ["FIXTURE_STEP"]
    print(json.dumps([{"jobs": [dict(name="runtime",
          head_sha="c" * 40 if status == "wrong_sha" else head, conclusion="success",
          steps=[dict(name="Compatibility", conclusion=status)])]}]))
else:
    raise SystemExit(10)
''')
            gh.chmod(0o700)
            git = root / 'git'
            git.write_text('''#!/usr/bin/env python3
import os, sys
assert sys.argv[3:7] == ["diff", "--name-only", "-z", "--no-renames"]
sys.stdout.write(os.environ["FIXTURE_PATH"] + chr(0))
''')
            git.chmod(0o700)
            env = dict(os.environ, PATH=f'{root}:{os.environ["PATH"]}',
                       CODEX_CI_EVENTS_HOME=str(root), GH_READONLY_WRAPPER=str(gh),
                       CODEX_CI_EVENTS_SCRIPT=str(ROOT / 'codex/ci/ci_events.py'))

            def invoke(path, status, *args):
                return subprocess.run(
                    [str(wrapper), '--confirm-user-requested', 'pr', 'merge', *args],
                    capture_output=True, text=True,
                    env=dict(env, FIXTURE_PATH=path, FIXTURE_STEP=status),
                )

            result = invoke('worker/task.py', 'success', '--repo', repo, '1', '-b', '--disable-auto')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), [
                'pr', 'merge', '--match-head-commit', head, '--repo', repo, url, '-b', '--disable-auto',
            ])
            for status in ('skipped', 'failure', 'wrong_sha'):
                with self.subTest(status=status):
                    result = invoke('worker/task.py', status, '1', '--squash')
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(result.stdout, '')
            result = invoke('README.md', 'skipped', '1', '--squash')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), ['pr', 'merge', '1', '--squash'])
            result = invoke('worker/task.py', 'skipped', '1', '--disable-auto')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), ['pr', 'merge', '1', '--disable-auto'])

    def test_batch_keeps_required_checks_and_excludes_unregistered_requests(self):
        trace = []
        checks, excluded = select_item_checks(
            {'required': lambda item: trace.append(('required', item))},
            {'extra': lambda item: trace.append(('extra', item))},
            ['unknown', 'extra', 'extra', 'required'],
        )
        for item in (1, 2):
            for check in checks:
                check(item)
        self.assertEqual(excluded, ('unknown',))
        self.assertEqual(trace, [('required', 1), ('extra', 1), ('required', 2), ('extra', 2)])
