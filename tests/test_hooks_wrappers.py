import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK_DIR = ROOT / 'hooks' / 'codex'
AWS = 'aw' + 's'
GH = 'g' + 'h'
GCLOUD = 'g' + 'cloud'
GSUTIL = 'gs' + 'util'
BQ = 'b' + 'q'
CAT = 'ca' + 't'
ENV_FILE = '.env'
RM = 'r' + 'm'
RF = '-' + 'rf'


def run_hook(script_name: str, command: str | None = None, payload: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({
        'PYTHONPATH': str(HOOK_DIR),
        'AWS_READONLY_WRAPPER': '/approved/aws-readonly',
        'GH_READONLY_WRAPPER': '/approved/gh-readonly',
        'GCLOUD_READONLY_WRAPPER': '/approved/gcloud-readonly',
        'GIT_USER_APPROVED_WRAPPER': '/approved/git-user-approved',
    })
    if payload is None:
        payload = json.dumps({'tool_input': {'command': command or ''}})
    return subprocess.run(
        ['python3', str(HOOK_DIR / script_name)],
        input=payload,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )


class HookPolicyTests(unittest.TestCase):
    def assertBlocked(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(result.returncode, 2, result.stderr + result.stdout)

    def assertAllowed(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_hooks_reject_malformed_nonempty_payload_but_allow_empty_input(self):
        self.assertBlocked(run_hook('local-safety-policy.py', payload='{not json'))
        self.assertAllowed(run_hook('local-safety-policy.py', payload=''))

    def test_aws_hook_blocks_shell_bypasses_and_raw_cli_variants(self):
        self.assertBlocked(run_hook('aws-policy.py', f'command {AWS} sts get-caller-identity'))
        self.assertBlocked(run_hook('aws-policy.py', f'command sh -c "{AWS} s3 ls"'))
        self.assertBlocked(run_hook('aws-policy.py', f'exec sh -c "{AWS} s3 ls"'))
        self.assertBlocked(run_hook('aws-policy.py', f'env -i command sh -c "{AWS} s3 ls"'))
        self.assertBlocked(run_hook('aws-policy.py', f'command sudo {AWS} s3 ls'))
        self.assertBlocked(run_hook('aws-policy.py', f'sh -c "{AWS} s3 ls"'))
        self.assertBlocked(run_hook('aws-policy.py', 'echo $' + f'({AWS} s3 ls)'))
        self.assertBlocked(run_hook('aws-policy.py', f'env -i {AWS} s3 ls'))
        self.assertBlocked(run_hook('aws-policy.py', f'xargs {AWS}'))
        self.assertBlocked(run_hook('aws-policy.py', f'sudo --chdir /tmp {AWS} s3 ls'))
        self.assertBlocked(run_hook('aws-policy.py', f'/usr/bin/{AWS} s3 ls'))
        self.assertBlocked(run_hook('aws-policy.py', f'/approved/aws-readonly s3 ls ; {AWS} s3 ls'))
        self.assertBlocked(run_hook('aws-policy.py', f'printf ok\n{AWS} s3 ls'))
        self.assertBlocked(run_hook('aws-policy.py', f'({AWS} s3 ls)'))
        self.assertBlocked(run_hook('aws-policy.py', '{ ' + f'{AWS} s3 ls' + '; }'))
        self.assertAllowed(run_hook('aws-policy.py', '/approved/aws-readonly s3 ls'))

    def test_github_and_gcloud_hooks_block_wrappers_and_raw_cli_variants(self):
        self.assertBlocked(run_hook('gh-policy.py', f'sudo {GH} pr view 1'))
        self.assertBlocked(run_hook('gh-policy.py', f'/approved/gh-readonly pr view 1 && {GH} pr merge 1'))
        self.assertAllowed(run_hook('gh-policy.py', '/approved/gh-readonly pr view 1'))
        self.assertBlocked(run_hook('gcloud-policy.py', f'command {GCLOUD} projects list'))
        self.assertBlocked(run_hook('gcloud-policy.py', f'/approved/gcloud-readonly projects list | {BQ} ls'))
        self.assertBlocked(run_hook('gcloud-policy.py', f'{GSUTIL} ls gs://example'))
        self.assertAllowed(run_hook('gcloud-policy.py', '/approved/gcloud-readonly projects list'))

    def test_git_hook_blocks_raw_commit_push_and_shell_bypass(self):
        self.assertBlocked(run_hook('git-policy.py', 'command git push origin main'))
        self.assertBlocked(run_hook('git-policy.py', 'command sh -c "git push"'))
        self.assertBlocked(run_hook('git-policy.py', 'sh -c "git push"'))
        self.assertBlocked(run_hook('git-policy.py', '(git push)'))
        self.assertBlocked(run_hook('git-policy.py', '/approved/git-user-approved add README.md ; git push origin main'))
        self.assertAllowed(run_hook('git-policy.py', '/approved/git-user-approved push --confirm-user-requested origin HEAD:main'))

    def test_local_safety_blocks_shell_bypasses_and_destructive_forms(self):
        self.assertBlocked(run_hook('local-safety-policy.py', f'command {RM} {RF} /tmp/example'))
        self.assertBlocked(run_hook('local-safety-policy.py', f'printf x | xargs {RM} {RF}'))
        self.assertBlocked(run_hook('local-safety-policy.py', 'sudo git clean -fd'))
        self.assertBlocked(run_hook('local-safety-policy.py', f'command sh -c "{RM} {RF} /tmp/x"'))
        self.assertBlocked(run_hook('local-safety-policy.py', f'sh -c "{RM} {RF} /tmp/x"'))
        self.assertBlocked(run_hook('local-safety-policy.py', f'({RM} {RF} /tmp/x)'))
        self.assertBlocked(run_hook('local-safety-policy.py', 'echo $' + f'({CAT} {ENV_FILE})'))
        self.assertBlocked(run_hook('local-safety-policy.py', 'echo $API_TOKEN'))
        self.assertAllowed(run_hook('local-safety-policy.py', 'pnpm test'))


class WrapperTests(unittest.TestCase):
    def run_with_fake_bin(self, script: Path, fake_name: str, args: list[str]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / fake_name
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
            fake.chmod(0o755)
            env = os.environ.copy()
            env['PATH'] = tmp + os.pathsep + env.get('PATH', '')
            return subprocess.run([str(script), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, check=False)

    def test_aws_readonly_uses_metadata_allowlist_and_blocks_secret_or_data_reads(self):
        script = ROOT / 'wrappers' / 'bin' / 'aws-readonly.example'
        run = lambda args: self.run_with_fake_bin(script, AWS, args)
        self.assertEqual(run(['sts', 'get-caller-identity']).returncode, 0)
        self.assertEqual(run(['ec2', 'describe-vpcs']).returncode, 0)
        self.assertEqual(run(['lambda', 'get-function-configuration', '--function-name', 'fn']).returncode, 0)
        self.assertNotEqual(run(['secretsmanager', 'get-secret-value', '--secret-id', 'x']).returncode, 0)
        self.assertNotEqual(run(['ssm', 'get-parameter', '--with-decryption', '--name', 'x']).returncode, 0)
        self.assertNotEqual(run(['ecr', 'get-login-password']).returncode, 0)
        self.assertNotEqual(run(['logs', 'filter-log-events', '--log-group-name', 'x']).returncode, 0)
        self.assertNotEqual(run(['logs', 'start-query', '--log-group-name', 'x']).returncode, 0)
        self.assertNotEqual(run(['dynamodb', 'scan', '--table-name', 'x']).returncode, 0)
        self.assertNotEqual(run(['lambda', 'get-function', '--function-name', 'fn']).returncode, 0)

    def test_gcloud_readonly_uses_explicit_allowlist_and_blocks_write_like_forms(self):
        script = ROOT / 'wrappers' / 'bin' / 'gcloud-readonly.example'
        run = lambda args: self.run_with_fake_bin(script, GCLOUD, args)
        self.assertEqual(run(['projects', 'list']).returncode, 0)
        self.assertEqual(run(['projects', 'describe', 'example-project']).returncode, 0)
        self.assertEqual(run(['compute', 'instances', 'list']).returncode, 0)
        self.assertEqual(run(['storage', 'ls', 'gs://example']).returncode, 0)
        self.assertNotEqual(run(['storage', 'cp', 'list', 'gs://example/object']).returncode, 0)
        self.assertNotEqual(run(['auth', 'print-access-token']).returncode, 0)
        self.assertNotEqual(run(['secrets', 'versions', 'access', 'latest']).returncode, 0)

    def test_git_wrapper_rejects_unsafe_push_forms(self):
        script = ROOT / 'wrappers' / 'bin' / 'git-user-approved.example'
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / 'git'
            fake.write_text('#!/bin/sh\nexit 0\n')
            fake.chmod(0o755)
            env = os.environ.copy()
            env['PATH'] = tmp + os.pathsep + env.get('PATH', '')
            def run(args: list[str]) -> subprocess.CompletedProcess[str]:
                return subprocess.run([str(script), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, check=False)
            self.assertNotEqual(run(['push', '--confirm-user-requested', '--force', 'origin', 'HEAD:main']).returncode, 0)
            self.assertNotEqual(run(['push', '--confirm-user-requested', 'origin', ':main']).returncode, 0)
            self.assertEqual(run(['push', '--confirm-user-requested', '--force-with-lease=refs/heads/main:abc', 'origin', 'HEAD:main']).returncode, 0)


if __name__ == '__main__':
    unittest.main()
