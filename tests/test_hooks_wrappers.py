import json
import os
import runpy
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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


def browser_hook(
    user_messages: list[str],
    code: str,
    prior_browser_runtime: bool = False,
    tool_name: str = "mcp__node_repl__js",
    prior_calls: list[tuple[str, str, str]] | None = None,
) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', encoding='utf-8') as transcript:
        if prior_browser_runtime:
            transcript.write(json.dumps({
                'type': 'event_msg',
                'payload': {
                    'type': 'item_completed',
                    'item': {
                        'type': 'McpToolCall',
                        'server': 'node_repl',
                        'tool': 'js',
                        'arguments': {'code': 'const agent = await setupBrowserRuntime();'},
                    },
                },
            }) + '\n')
        for server, tool, prior_code in prior_calls or []:
            transcript.write(json.dumps({
                'type': 'event_msg',
                'payload': {
                    'type': 'item_completed',
                    'item': {
                        'type': 'McpToolCall', 'server': server, 'tool': tool,
                        'arguments': {'code': prior_code},
                    },
                },
            }) + '\n')
        for message in user_messages:
            transcript.write(json.dumps({
                'type': 'response_item',
                'payload': {
                    'type': 'message',
                    'role': 'user',
                    'content': [{'type': 'input_text', 'text': message}],
                },
            }) + '\n')
        transcript.flush()
        return run_hook('browser-policy.py', payload=json.dumps({
            'transcript_path': transcript.name,
            'tool_name': tool_name,
            'tool_input': {'code': code},
        }))


class HookPolicyTests(unittest.TestCase):
    def assertBlocked(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(result.returncode, 2, result.stderr + result.stdout)

    def assertAllowed(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_hooks_reject_malformed_nonempty_payload_but_allow_empty_input(self):
        self.assertBlocked(run_hook('local-safety-policy.py', payload='{not json'))
        self.assertAllowed(run_hook('local-safety-policy.py', payload=''))

    def test_combined_shell_hook_preserves_each_policy_boundary(self):
        self.assertBlocked(run_hook('shell-policy.py', payload='{not json'))
        self.assertAllowed(run_hook('shell-policy.py', payload=''))
        self.assertBlocked(run_hook('shell-policy.py', 'git push origin main'))
        self.assertBlocked(run_hook('shell-policy.py', f'{AWS} s3 ls'))
        self.assertBlocked(run_hook('shell-policy.py', f'{GH} pr view 1'))
        self.assertBlocked(run_hook('shell-policy.py', f'{GCLOUD} projects list'))
        self.assertBlocked(run_hook('shell-policy.py', f'{RM} {RF} /tmp/example'))
        self.assertAllowed(run_hook('shell-policy.py', 'pnpm test'))

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

    def test_git_hook_blocks_raw_branch_switching(self):
        self.assertBlocked(run_hook('git-policy.py', 'git switch -c HBE-301_medication-statement-create-api'))
        self.assertBlocked(run_hook('git-policy.py', 'git checkout -b HBE-301_medication-statement-create-api'))
        self.assertBlocked(run_hook('git-policy.py', 'git -C /tmp/example switch -c HBE-301_medication-statement-create-api'))
        self.assertAllowed(run_hook(
            'git-policy.py',
            '/approved/git-user-approved switch --confirm-user-requested --create HBE-301_medication-statement-create-api',
        ))

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
        self.assertAllowed(run_hook('local-safety-policy.py', 'python3 -c "print(1)"'))

    def test_database_cli_allows_explicit_local_targets(self):
        commands = [
            "psql -h localhost -d testdb -c 'SELECT 1'",
            "mysql --host=127.0.0.1 testdb",
            "mongosh --host ::1 --eval 'db.runCommand({ping:1})'",
            "redis-cli -h 127.0.0.1 PING",
            "psql postgresql://localhost/testdb -c 'SELECT 1'",
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertAllowed(run_hook('shell-policy.py', command))

    def test_database_cli_rejects_remote_missing_and_overridden_targets(self):
        commands = [
            "psql -d testdb", "mysql --host remote.example testdb",
            "mongosh mongodb://remote.example/testdb", "redis-cli -h remote.example PING",
            "psql -h localhost postgresql://remote.example/testdb",
            "psql postgresql://localhost/testdb?host=remote.example",
            "psql -h localhost -d 'hostaddr=192.0.2.1 dbname=testdb'",
            "psql -h localhost --host=remote.example",
            "psql -h", "psql -h localhost.example",
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertBlocked(run_hook('shell-policy.py', command))

    def test_database_scripts_are_not_blocked_by_name_alone(self):
        for command in [
            'pnpm test:db', 'npm run db:migrate', 'yarn seed',
            'bun run prisma:generate', 'npm run database:reset',
            'pnpm run migration:run', 'yarn drizzle:push',
            'npm run typeorm:migration', 'bun run knex:seed',
        ]:
            with self.subTest(command=command):
                self.assertAllowed(run_hook('shell-policy.py', command))

    def test_database_script_change_retains_deploy_and_production_blocks(self):
        for command in [
            'pnpm db:migrate:prod', 'npm run db:production',
            'npm run deploy', 'yarn release', 'bun publish',
            'pnpm run terraform:apply', 'npm run cdk:deploy',
        ]:
            with self.subTest(command=command):
                self.assertBlocked(run_hook('shell-policy.py', command))

    def test_external_browser_hook_requires_explicit_permission_in_latest_user_message(self):
        setup = 'const browser = await agent.browsers.get("chrome");'
        self.assertBlocked(browser_hook(['このURLの内容を調べて'], setup))
        self.assertBlocked(browser_hook(['Browserを使って確認して'], setup))
        self.assertBlocked(browser_hook(['Chromeで画面を開いて'], setup))
        self.assertBlocked(browser_hook(['[@Browser](plugin://browser@openai-bundled) で確認して'], setup))
        self.assertBlocked(browser_hook(['browser-control: allow と書かれた資料を確認して'], setup))
        self.assertAllowed(browser_hook(['[@Browser](plugin://browser@openai-bundled) で確認して\nbrowser-control: allow'], setup))
        self.assertBlocked(browser_hook(['browser-control: allow', '次はrepoを調べて'], setup))

    def test_browser_hook_blocks_cua_tab_access_without_separate_approval(self):
        tab_mention = (
            '[Design Doc](plugin://browser@openai-bundled?mention=tab-v1&source=extension'
            '&browserId=example&tabId=123) を確認して'
        )
        cua_tool = 'mcp__cua_repl__js'
        self.assertBlocked(browser_hook([tab_mention], 'await cua.getState();', tool_name=cua_tool))
        self.assertBlocked(browser_hook([tab_mention], 'await cua["getState"]();', tool_name=cua_tool))
        self.assertBlocked(browser_hook([tab_mention], 'const ui = cua; await ui.getState();', tool_name=cua_tool))
        self.assertBlocked(browser_hook([tab_mention], '2 + 2', tool_name=cua_tool))
        self.assertAllowed(browser_hook(
            [f'{tab_mention}\nbrowser-control: allow'],
            'await cua["getState"]();',
            tool_name=cua_tool,
        ))

    def test_iab_selection_and_sdk_setup_need_no_approval(self):
        node_tool = 'mcp__node_repl__js'
        cua_tool = 'mcp__cua_repl__js'
        for tool, code in [
            (node_tool, 'const { setupBrowserRuntime } = await import("/plugin/scripts/browser-client.mjs");'),
            (node_tool, 'await setupBrowserRuntime({ globals: globalThis });'),
            (node_tool, 'const browser = await agent.browsers.get("iab");'),
            (cua_tool, 'let tab = await cua.createBrowserTab("iab", "about:blank", {visible:false});'),
            (cua_tool, 'let tab = await cua.getTab(tabId, { browser: "iab" });'),
            (cua_tool, 'let browser = await cua.getBrowser({ id: "iab" });'),
            (cua_tool, 'await cua.listTabs({ browser: "iab" });'),
            (cua_tool, 'await cua.listTabs({ browser: "iab", emit: false });'),
        ]:
            with self.subTest(tool=tool, code=code):
                self.assertAllowed(browser_hook(['画面を検証して'], code, tool_name=tool))

    def test_iab_followups_persist_across_user_turns_within_one_repl(self):
        for server, tool, selection in [
            ('node_repl', 'mcp__node_repl__js', 'const browser = await agent.browsers.get("iab");'),
            ('cua_repl', 'mcp__cua_repl__js', 'let tab = await cua.createBrowserTab("iab", "about:blank");'),
        ]:
            with self.subTest(server=server):
                self.assertAllowed(browser_hook(
                    ['画面を確認して', '続けて'], 'await tab.playwright.domSnapshot();',
                    tool_name=tool, prior_calls=[(server, 'js', selection)],
                ))

    def test_iab_state_does_not_authorize_other_repl_or_survive_reset(self):
        selection = 'let tab = await cua.createBrowserTab("iab", "about:blank");'
        cua_tool = 'mcp__cua_repl__js'
        self.assertBlocked(browser_hook(
            ['続けて'], 'await tab.playwright.domSnapshot();', tool_name=cua_tool,
            prior_calls=[('node_repl', 'js', 'await agent.browsers.get("iab");')],
        ))
        self.assertAllowed(browser_hook(['続けて'], '', tool_name='mcp__cua_repl__js_reset'))
        self.assertBlocked(browser_hook(
            ['続けて'], 'await tab.playwright.domSnapshot();', tool_name=cua_tool,
            prior_calls=[('cua_repl', 'js', selection), ('cua_repl', 'js_reset', '')],
        ))
        self.assertAllowed(browser_hook(
            ['続けて'], selection, tool_name=cua_tool,
            prior_calls=[('cua_repl', 'js', selection), ('cua_repl', 'js_reset', '')],
        ))

    def test_iab_does_not_allow_external_dynamic_or_inventory_access(self):
        for code in [
            'await cua.createBrowserTab("chrome", "about:blank");',
            'await cua.createBrowserTab(target, "about:blank");',
            'await cua.getTab(tabId);',
            'await cua.getTab(tabId, {browser: "edge"});',
            'await cua.getState();',
            'await cua.listTabs();',
            'await cua.listTabs({browser: "chrome"});',
            'await cua.getBrowser({id: "chrome"});',
            'await cua.getBrowser({url: "https://example.com"});',
            'const ui = cua; await ui.getState();',
            'await cua["getState"]();',
            'await agent.browsers.list();',
            'await agent.browsers.getDefault();',
            'await agent.browsers.getForUrl("https://example.com");',
            'await agent.browsers.get(target);',
            'const browsers = agent.browsers; await browsers.get("chrome");',
            'await agent.browsers.get("iab"); await agent.browsers.get("chrome");',
            'await cua.createBrowserTab("iab", "about:blank"); await cua.getState();',
        ]:
            with self.subTest(code=code):
                self.assertBlocked(browser_hook(
                    ['画面を確認して'], code, tool_name='mcp__cua_repl__js',
                    prior_calls=[('cua_repl', 'js', 'await cua.createBrowserTab("iab", "about:blank");')],
                ))

    def test_browser_hook_registration_covers_node_and_cua_repl(self):
        config = (ROOT / 'codex' / 'config.example.toml').read_text(encoding='utf-8')
        self.assertIn('matcher = "(?i).*(node|cua)[_-]?repl.*js.*"', config)

    def test_browser_hook_blocks_reused_browser_bindings_but_allows_other_node_code(self):
        self.assertBlocked(browser_hook(['repoを読んで'], 'await pageAlias.doSomething();', prior_browser_runtime=True))
        self.assertAllowed(browser_hook(['browser-control: allow'], 'await pageAlias.doSomething();', prior_browser_runtime=True))
        self.assertAllowed(browser_hook(['計算して'], '2 + 2'))

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

    def test_github_readonly_allows_rest_reads_and_blocks_api_mutations(self):
        script = ROOT / 'wrappers' / 'bin' / 'gh-readonly.example'
        run = lambda args: self.run_with_fake_bin(script, GH, args)

        comments = run(['api', 'repos/acme/example/pulls/12/comments', '--paginate'])
        self.assertEqual(comments.returncode, 0, comments.stderr)
        self.assertEqual(
            comments.stdout.splitlines(),
            ['api', 'repos/acme/example/pulls/12/comments', '--paginate', '--method', 'GET'],
        )
        self.assertEqual(run(['api', 'repos/acme/example', '--method', 'GET']).returncode, 0)
        self.assertEqual(run(['api', 'repos/acme/example', '-XHEAD']).returncode, 0)

        for args in (
            ['api', 'repos/acme/example/issues', '--method', 'POST'],
            ['api', 'repos/acme/example', '-XPATCH'],
            ['api', 'repos/acme/example', '-X', 'DELETE'],
            ['api', 'repos/acme/example/issues', '--field', 'title=test', '--'],
            ['api', 'repos/acme/example', '--header', 'X-HTTP-Method-Override: POST'],
            ['api', 'repos/acme/example', '--header=X-Method-Override: DELETE'],
        ):
            with self.subTest(args=args):
                self.assertNotEqual(run(args).returncode, 0)

        self.assertNotEqual(run(['pr', 'merge', '12']).returncode, 0)

    def test_github_readonly_keeps_global_options_before_rest_reads(self):
        script = ROOT / 'wrappers' / 'bin' / 'gh-readonly.example'
        result = self.run_with_fake_bin(
            script,
            GH,
            ['--repo', 'acme/example', 'api', 'repos/acme/example/pulls/12/reviews'],
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            [
                '--repo',
                'acme/example',
                'api',
                'repos/acme/example/pulls/12/reviews',
                '--method',
                'GET',
            ],
        )

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

    def test_git_wrapper_rejects_rebase_exec_forms(self):
        script = ROOT / 'wrappers' / 'bin' / 'git-user-approved.example'
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / 'git'
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
            fake.chmod(0o755)
            env = os.environ.copy()
            env['PATH'] = tmp + os.pathsep + env.get('PATH', '')

            def run(args: list[str]) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [str(script), *args],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    check=False,
                )

            for args in (
                ['rebase', '-x', 'touch /tmp/example', 'origin/main'],
                ['rebase', '-xtouch /tmp/example', 'origin/main'],
                ['rebase', '--exec', 'touch /tmp/example', 'origin/main'],
                ['rebase', '--exec=touch /tmp/example', 'origin/main'],
            ):
                self.assertNotEqual(run(args).returncode, 0, args)
            self.assertEqual(run(['rebase', 'origin/main']).returncode, 0)

    def test_git_wrapper_requires_explicit_merge_confirmation(self):
        script = ROOT / 'wrappers' / 'bin' / 'git-user-approved.example'
        run = lambda args: self.run_with_fake_bin(script, 'git', args)
        self.assertNotEqual(run(['merge', '--no-edit', 'origin/staging']).returncode, 0)
        result = run(['merge', '--confirm-user-requested', '--no-edit', 'origin/staging'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ['merge', '--no-edit', 'origin/staging'])
        self.assertNotEqual(run(['merge', '--confirm-user-requested', '--squash', 'origin/staging']).returncode, 0)
        self.assertNotEqual(run(['merge', '--confirm-user-requested', 'origin/staging', 'origin/main']).returncode, 0)
        self.assertEqual(run(['merge', '--abort']).returncode, 0)

    def test_git_wrapper_requires_explicit_switch_confirmation(self):
        script = ROOT / 'wrappers' / 'bin' / 'git-user-approved.example'
        run = lambda args: self.run_with_fake_bin(script, 'git', args)
        self.assertNotEqual(run(['switch', '--create', 'HBE-301_medication-statement-create-api']).returncode, 0)
        created = run([
            'switch',
            '--confirm-user-requested',
            '--create',
            'HBE-301_medication-statement-create-api',
        ])
        self.assertEqual(created.returncode, 0, created.stderr)
        self.assertEqual(
            created.stdout.splitlines(),
            ['switch', '--create', 'HBE-301_medication-statement-create-api'],
        )
        existing = run(['switch', '--confirm-user-requested', 'main'])
        self.assertEqual(existing.returncode, 0, existing.stderr)
        self.assertEqual(existing.stdout.splitlines(), ['switch', 'main'])
        self.assertNotEqual(run(['switch', '--confirm-user-requested', '--detach', 'main']).returncode, 0)
        self.assertNotEqual(run(['switch', '--confirm-user-requested', '--create', '-invalid']).returncode, 0)
        self.assertNotEqual(run([
            'switch',
            '--confirm-user-requested',
            '--create',
            'new-branch',
            'origin/main',
        ]).returncode, 0)

    def run_claude_wrapper(
        self,
        claude_script: str,
        timeout: str = '5',
        supports_safe_mode: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            fake_security = Path(tmp) / 'security'
            fake_security.write_text('#!/bin/sh\nprintf "test-token\\n"\n')
            fake_security.chmod(0o755)

            fake_claude = Path(tmp) / 'claude'
            safe_mode_help = '--safe-mode' if supports_safe_mode else '--permission-mode'
            fake_claude.write_text(
                '#!/bin/sh\n'
                'if [ "$1" = "--help" ]; then\n'
                f'  printf "%s\\n" "{safe_mode_help}"\n'
                '  exit 0\n'
                'fi\n'
                'if [ "$1" = "--version" ]; then\n'
                '  printf "test-claude 1.0\\n"\n'
                '  exit 0\n'
                'fi\n'
                + claude_script.removeprefix('#!/bin/sh\n')
            )
            fake_claude.chmod(0o755)

            prompt = Path(tmp) / 'prompt.md'
            prompt.write_text('Review this bounded plan.')
            env = os.environ.copy()
            env.update({
                'PATH': tmp + os.pathsep + env.get('PATH', ''),
                'CLAUDE_STRATEGIC_CLI': str(fake_claude),
                'CLAUDE_STRATEGIC_TIMEOUT_SECONDS': timeout,
            })
            return subprocess.run(
                [
                    str(ROOT / 'wrappers' / 'bin' / 'claude-strategic-review.example'),
                    '--prompt-file',
                    str(prompt),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=False,
            )

    def test_claude_strategic_review_disables_agentic_execution(self):
        result = self.run_claude_wrapper(
            '#!/bin/sh\n'
            'test -n "$CLAUDE_CODE_OAUTH_TOKEN" || exit 9\n'
            'printf "%s\\n" "$@"\n'
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        args = result.stdout.splitlines()
        self.assertIn('--safe-mode', args)
        self.assertIn('--no-session-persistence', args)
        self.assertEqual(args[args.index('--tools') + 1], '')
        self.assertEqual(args[args.index('--max-turns') + 1], '1')

    def test_claude_strategic_review_default_timeout_allows_deep_review(self):
        wrapper = ROOT / 'wrappers' / 'bin' / 'claude-strategic-review.example'
        namespace = runpy.run_path(str(wrapper))
        self.assertEqual(namespace['DEFAULT_TIMEOUT_SECONDS'], 600)

    def test_claude_strategic_review_rejects_cli_without_safe_mode(self):
        result = self.run_claude_wrapper(
            '#!/bin/sh\nexit 0\n',
            supports_safe_mode=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('does not support required --safe-mode', result.stderr)
        self.assertIn('test-claude 1.0', result.stderr)

    def test_claude_strategic_review_has_a_hard_timeout(self):
        result = self.run_claude_wrapper('#!/bin/sh\nsleep 2\n', timeout='1')
        self.assertEqual(result.returncode, 124)
        self.assertIn('timed out after 1 seconds', result.stderr)
        self.assertIn('process remained active but final stdout was not received', result.stderr)

    def run_claude_html_wrapper(
        self,
        claude_script: str,
        args: list[str] | None = None,
        supports_safe_mode: bool = True,
        timeout: str = '5',
    ) -> tuple[subprocess.CompletedProcess[str], Path, tempfile.TemporaryDirectory[str]]:
        tmp_context = tempfile.TemporaryDirectory()
        tmp = Path(tmp_context.name)
        fake_security = tmp / 'security'
        fake_security.write_text('#!/bin/sh\nprintf "test-token\\n"\n')
        fake_security.chmod(0o755)

        fake_claude = tmp / 'claude'
        safe_mode_help = '--safe-mode' if supports_safe_mode else '--permission-mode'
        fake_claude.write_text(
            '#!/bin/sh\n'
            'if [ "$1" = "--help" ]; then\n'
            f'  printf "%s\\n" "{safe_mode_help}"\n'
            '  exit 0\n'
            'fi\n'
            'if [ "$1" = "--version" ]; then\n'
            '  printf "test-claude 1.0\\n"\n'
            '  exit 0\n'
            'fi\n'
            + claude_script.removeprefix('#!/bin/sh\n')
        )
        fake_claude.chmod(0o755)

        prompt = tmp / 'packet.md'
        prompt.write_text('Reader: product owner.\\nFact F1: verified result.')
        output = tmp / 'candidate.html'
        args_file = tmp / 'claude-args.txt'
        env = os.environ.copy()
        env.update({
            'PATH': str(tmp) + os.pathsep + env.get('PATH', ''),
            'CLAUDE_HTML_REPORT_CLI': str(fake_claude),
            'CLAUDE_HTML_REPORT_TIMEOUT_SECONDS': timeout,
            'CLAUDE_HTML_ARGS_FILE': str(args_file),
        })
        command = [
            str(ROOT / 'wrappers' / 'bin' / 'claude-html-report.example'),
            '--prompt-file',
            str(prompt),
            '--output-file',
            str(output),
        ]
        if args:
            command.extend(args)
        result = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )
        return result, output, tmp_context

    def test_claude_html_report_disables_agentic_execution_and_writes_new_html(self):
        result, output, tmp_context = self.run_claude_html_wrapper(
            '#!/bin/sh\n'
            'printf "%s\\n" "$@" > "$CLAUDE_HTML_ARGS_FILE"\n'
            'printf "<!doctype html><html><body data-fact=\\"F1\\" data-weight=\\"load-bearing\\">ok<!-- REPORT-META structure: - one information_weighting: main: - F1 deferred: [] omitted: [] inferences: [] --></body></html>\\n"\n'
        )
        try:
            self.assertEqual(result.returncode, 0, result.stderr)
            args = (Path(tmp_context.name) / 'claude-args.txt').read_text().splitlines()
            self.assertIn('--safe-mode', args)
            self.assertIn('--no-session-persistence', args)
            self.assertIn('--disable-slash-commands', args)
            self.assertIn('--no-chrome', args)
            self.assertEqual(args[args.index('--tools') + 1], '')
            self.assertEqual(args[args.index('--max-turns') + 1], '1')
            self.assertEqual(args[args.index('--model') + 1], 'claude-opus-5')
            self.assertTrue(output.is_file())
            self.assertIn('data-fact="F1"', output.read_text())
            self.assertIn('data-weight="load-bearing"', output.read_text())
        finally:
            tmp_context.cleanup()

    def test_claude_html_report_prompt_contains_the_enforced_output_contract(self):
        wrapper = ROOT / 'wrappers' / 'bin' / 'claude-html-report.example'
        contract = runpy.run_path(str(wrapper))['fixed_contract']()

        self.assertIn('data-fact="F1 F4"', contract)
        self.assertIn('data-weight="load-bearing|supporting|context"', contract)
        self.assertIn('data-uncertainty="U2"', contract)
        self.assertIn('{{ASSET:A1}}', contract)
        self.assertIn('<!-- REPORT-META', contract)
        self.assertIn('information_weighting:', contract)
        self.assertIn('Do not make the reader reconstruct priority', contract)
        self.assertIn('never render REPORT-META as visible content', contract)

    def test_claude_html_report_uses_fable_only_when_selected(self):
        result, output, tmp_context = self.run_claude_html_wrapper(
            '#!/bin/sh\n'
            'printf "%s\\n" "$@" > "$CLAUDE_HTML_ARGS_FILE"\n'
            'printf "<!doctype html><html><body data-fact=\\"F1\\" data-weight=\\"load-bearing\\">ok<!-- REPORT-META structure: - one information_weighting: main: - F1 deferred: [] omitted: [] inferences: [] --></body></html>\\n"\n',
            args=['--model', 'fable'],
        )
        try:
            self.assertEqual(result.returncode, 0, result.stderr)
            args = (Path(tmp_context.name) / 'claude-args.txt').read_text().splitlines()
            self.assertEqual(args[args.index('--model') + 1], 'claude-fable-5-1')
            self.assertTrue(output.is_file())
        finally:
            tmp_context.cleanup()

    def test_claude_html_report_rejects_existing_output(self):
        result, output, tmp_context = self.run_claude_html_wrapper(
            '#!/bin/sh\nprintf "<!doctype html><html><body data-fact=\\"F1\\" data-weight=\\"load-bearing\\"><!-- REPORT-META structure: - one information_weighting: main: - F1 deferred: [] omitted: [] inferences: [] --></body></html>\\n"\n'
        )
        try:
            self.assertEqual(result.returncode, 0, result.stderr)
            second = subprocess.run(
                [
                    str(ROOT / 'wrappers' / 'bin' / 'claude-html-report.example'),
                    '--prompt-file',
                    str(Path(tmp_context.name) / 'packet.md'),
                    '--output-file',
                    str(output),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={
                    **os.environ,
                    'PATH': tmp_context.name + os.pathsep + os.environ.get('PATH', ''),
                    'CLAUDE_HTML_REPORT_CLI': str(Path(tmp_context.name) / 'claude'),
                },
                check=False,
            )
            self.assertNotEqual(second.returncode, 0)
            self.assertIn('must not already exist', second.stderr)
        finally:
            tmp_context.cleanup()

    def test_claude_html_report_rejects_invalid_html(self):
        result, output, tmp_context = self.run_claude_html_wrapper(
            '#!/bin/sh\nprintf "not html\\n"\n'
        )
        try:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('did not begin with <!doctype html>', result.stderr)
            self.assertFalse(output.exists())
        finally:
            tmp_context.cleanup()

    def test_claude_html_report_surfaces_redacted_stdout_and_stderr_on_cli_failure(self):
        result, output, tmp_context = self.run_claude_html_wrapper(
            '#!/bin/sh\n'
            'printf "Fable request failed for token %s\\n" "$CLAUDE_CODE_OAUTH_TOKEN"\n'
            'printf "provider detail: overloaded\\n" >&2\n'
            'exit 7\n'
        )
        try:
            self.assertEqual(result.returncode, 1)
            self.assertIn('Claude CLI stdout:', result.stderr)
            self.assertIn('Fable request failed for token [REDACTED]', result.stderr)
            self.assertIn('Claude CLI stderr:', result.stderr)
            self.assertIn('provider detail: overloaded', result.stderr)
            self.assertIn('failed with exit code 7', result.stderr)
            self.assertNotIn('test-token', result.stderr)
            self.assertFalse(output.exists())
        finally:
            tmp_context.cleanup()

    def test_claude_html_report_reports_empty_cli_failure_diagnostics(self):
        result, output, tmp_context = self.run_claude_html_wrapper(
            '#!/bin/sh\nexit 9\n'
        )
        try:
            self.assertEqual(result.returncode, 1)
            self.assertIn('produced no stdout or stderr diagnostics', result.stderr)
            self.assertIn('failed with exit code 9', result.stderr)
            self.assertFalse(output.exists())
        finally:
            tmp_context.cleanup()

    def test_claude_html_report_surfaces_diagnostics_on_timeout(self):
        result, output, tmp_context = self.run_claude_html_wrapper(
            '#!/bin/sh\n'
            'printf "provider request started\\n"\n'
            'sleep 2\n',
            timeout='1',
        )
        try:
            self.assertEqual(result.returncode, 124)
            self.assertIn('Claude CLI stdout:', result.stderr)
            self.assertIn('provider request started', result.stderr)
            self.assertIn('timed out after 1 seconds', result.stderr)
            self.assertFalse(output.exists())
        finally:
            tmp_context.cleanup()

    def test_claude_html_report_rejects_commentary_after_html(self):
        result, output, tmp_context = self.run_claude_html_wrapper(
            '#!/bin/sh\nprintf "<!doctype html><html><body data-fact=\\"F1\\" data-weight=\\"load-bearing\\"><!-- REPORT-META structure: - one information_weighting: main: - F1 deferred: [] omitted: [] inferences: [] --></body></html>\\nDone.\\n"\n'
        )
        try:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('was not a complete HTML document', result.stderr)
            self.assertFalse(output.exists())
        finally:
            tmp_context.cleanup()

    def test_claude_html_report_rejects_missing_report_metadata(self):
        result, output, tmp_context = self.run_claude_html_wrapper(
            '#!/bin/sh\nprintf "<!doctype html><html><body data-fact=\\"F1\\" data-weight=\\"load-bearing\\">ok</body></html>\\n"\n'
        )
        try:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('exactly one REPORT-META comment', result.stderr)
            self.assertFalse(output.exists())
        finally:
            tmp_context.cleanup()

    def test_claude_html_report_rejects_missing_display_weights(self):
        result, output, tmp_context = self.run_claude_html_wrapper(
            '#!/bin/sh\nprintf "<!doctype html><html><body data-fact=\\"F1\\">ok<!-- REPORT-META structure: - one information_weighting: main: - F1 deferred: [] omitted: [] inferences: [] --></body></html>\\n"\n'
        )
        try:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('did not attach any display weights', result.stderr)
            self.assertFalse(output.exists())
        finally:
            tmp_context.cleanup()

    def test_claude_html_report_rejects_missing_weighting_metadata(self):
        result, output, tmp_context = self.run_claude_html_wrapper(
            '#!/bin/sh\nprintf "<!doctype html><html><body data-fact=\\"F1\\" data-weight=\\"load-bearing\\">ok<!-- REPORT-META structure: - one inferences: [] --></body></html>\\n"\n'
        )
        try:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('incomplete REPORT-META comment', result.stderr)
            self.assertFalse(output.exists())
        finally:
            tmp_context.cleanup()

    def test_claude_html_report_rejects_cli_without_safe_mode(self):
        result, output, tmp_context = self.run_claude_html_wrapper(
            '#!/bin/sh\nexit 0\n',
            supports_safe_mode=False,
        )
        try:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('does not support required --safe-mode', result.stderr)
            self.assertFalse(output.exists())
        finally:
            tmp_context.cleanup()

    def run_gemini_polish_wrapper(
        self,
        response_payload: dict,
        source: str = 'API v2は`/api/v2/items`で使えます。詳細はhttps://example.com/docsを見てください。',
        http_status: int = 200,
        precreate_output: bool = False,
    ) -> tuple[subprocess.CompletedProcess[str], Path, dict, tempfile.TemporaryDirectory[str]]:
        captured: dict = {'calls': 0}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                captured['calls'] += 1
                length = int(self.headers['Content-Length'])
                captured['api_key'] = self.headers.get('x-goog-api-key')
                captured['payload'] = json.loads(self.rfile.read(length))
                body = json.dumps(response_payload, ensure_ascii=False).encode()
                self.send_response(http_status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        tmp_context = tempfile.TemporaryDirectory()
        tmp = Path(tmp_context.name)
        input_file = tmp / 'draft.md'
        input_file.write_text(source, encoding='utf-8')
        output_file = tmp / 'polished.md'
        if precreate_output:
            output_file.write_text('existing', encoding='utf-8')
        env = os.environ.copy()
        env.update({
            'GEMINI_API_KEY': 'test-gemini-key',
            'GEMINI_JAPANESE_POLISH_API_URL': f'http://127.0.0.1:{server.server_port}/interactions',
            'GEMINI_JAPANESE_POLISH_TIMEOUT_SECONDS': '5',
        })
        try:
            result = subprocess.run(
                [
                    str(ROOT / 'wrappers' / 'bin' / 'gemini-japanese-polish.example'),
                    '--input-file',
                    str(input_file),
                    '--output-file',
                    str(output_file),
                    '--medium',
                    'github',
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=False,
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
        return result, output_file, captured, tmp_context

    @staticmethod
    def gemini_response(revised_text: str) -> dict:
        return {
            'id': 'int_test',
            'status': 'completed',
            'model': 'gemini-3.8-flash',
            'usage': {
                'total_input_tokens': 120,
                'total_output_tokens': 40,
                'total_tokens': 160,
            },
            'steps': [{
                'type': 'model_output',
                'content': [{
                    'type': 'text',
                    'text': json.dumps({
                        'revised_text': revised_text,
                        'changes': ['語順を調整'],
                        'warnings': [],
                    }, ensure_ascii=False),
                }],
            }],
        }

    def test_gemini_polish_is_stateless_bounded_and_writes_verified_output(self):
        revised = 'API v2は`/api/v2/items`で利用できます。詳細はhttps://example.com/docsをご覧ください。'
        result, output, captured, tmp_context = self.run_gemini_polish_wrapper(
            self.gemini_response(revised)
        )
        try:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_text(encoding='utf-8'), revised + '\n')
            self.assertEqual(captured['calls'], 1)
            self.assertEqual(captured['api_key'], 'test-gemini-key')
            payload = captured['payload']
            self.assertEqual(payload['model'], 'gemini-3.8-flash')
            self.assertIs(payload['store'], False)
            self.assertEqual(payload['generation_config']['thinking_level'], 'low')
            self.assertNotIn('tools', payload)
            self.assertEqual(payload['response_format']['mime_type'], 'application/json')
            self.assertEqual(
                set(payload['response_format']['schema']['required']),
                {'revised_text', 'changes', 'warnings'},
            )
            self.assertIn('120', result.stderr)
            self.assertNotIn('test-gemini-key', result.stderr + result.stdout)
        finally:
            tmp_context.cleanup()

    def test_gemini_polish_rejects_changed_protected_spans(self):
        revised = 'API v3は`/api/v3/items`で利用できます。詳細はhttps://example.com/newをご覧ください。'
        result, output, captured, tmp_context = self.run_gemini_polish_wrapper(
            self.gemini_response(revised)
        )
        try:
            self.assertEqual(result.returncode, 1)
            self.assertIn('changed a protected', result.stderr)
            self.assertEqual(captured['calls'], 1)
            self.assertFalse(output.exists())
        finally:
            tmp_context.cleanup()

    def test_gemini_polish_rejects_invalid_structured_output(self):
        response = self.gemini_response('推敲済み')
        response['steps'][0]['content'][0]['text'] = '{not json'
        result, output, _, tmp_context = self.run_gemini_polish_wrapper(response)
        try:
            self.assertEqual(result.returncode, 1)
            self.assertIn('structured output was not valid JSON', result.stderr)
            self.assertFalse(output.exists())
        finally:
            tmp_context.cleanup()

    def test_gemini_polish_rejects_existing_output_before_api_call(self):
        result, output, captured, tmp_context = self.run_gemini_polish_wrapper(
            self.gemini_response('unused'),
            precreate_output=True,
        )
        try:
            self.assertEqual(result.returncode, 2)
            self.assertIn('must not already exist', result.stderr)
            self.assertEqual(captured['calls'], 0)
            self.assertEqual(output.read_text(encoding='utf-8'), 'existing')
        finally:
            tmp_context.cleanup()

    def test_gemini_polish_does_not_retry_and_redacts_http_failure(self):
        response = {'error': {'message': 'key test-gemini-key is rejected'}}
        result, output, captured, tmp_context = self.run_gemini_polish_wrapper(
            response,
            http_status=429,
        )
        try:
            self.assertEqual(result.returncode, 1)
            self.assertEqual(captured['calls'], 1)
            self.assertIn('HTTP 429', result.stderr)
            self.assertIn('[REDACTED]', result.stderr)
            self.assertNotIn('test-gemini-key', result.stderr)
            self.assertFalse(output.exists())
        finally:
            tmp_context.cleanup()

    def run_grok_wrapper(
        self,
        response_payload: dict,
        args: list[str] | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict]:
        captured: dict = {}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers['Content-Length'])
                captured['authorization'] = self.headers.get('Authorization')
                captured['payload'] = json.loads(self.rfile.read(length))
                body = json.dumps(response_payload).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                prompt = Path(tmp) / 'prompt.md'
                prompt.write_text('直近のAI agent運用の議論を調査して')
                env = os.environ.copy()
                env.update({
                    'XAI_API_KEY': 'test-key',
                    'XAI_API_URL': f'http://127.0.0.1:{server.server_port}/responses',
                })
                command = [
                    str(ROOT / 'wrappers' / 'bin' / 'grok-x-research.example'),
                    '--prompt-file',
                    str(prompt),
                    '--from-date',
                    '2026-07-22',
                    '--to-date',
                    '2026-07-29',
                    *(args or []),
                ]
                result = subprocess.run(
                    command,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    check=False,
                )
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

        return result, captured

    def test_grok_wrapper_uses_only_x_search_and_normalizes_citations_and_cost(self):
        response = {
            'status': 'completed',
            'output': [{
                'type': 'message',
                'content': [{
                    'type': 'output_text',
                    'text': '調査結果',
                    'annotations': [
                        {'type': 'url_citation', 'url': 'https://x.com/example/status/1', 'title': '1'},
                        {'type': 'url_citation', 'url': 'https://x.com/example/status/1', 'title': 'duplicate'},
                    ],
                }],
            }],
            'usage': {
                'input_tokens': 100,
                'output_tokens': 20,
                'total_tokens': 120,
                'num_server_side_tools_used': 2,
                'cost_in_usd_ticks': 580_000_000,
                'server_side_tool_usage_details': {
                    'x_search_calls': 2,
                    'web_search_calls': 0,
                },
            },
        }
        result, captured = self.run_grok_wrapper(response, ['--allow-handle', '@example'])

        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output['status'], 'completed')
        self.assertEqual(output['sources'], [{
            'url': 'https://x.com/example/status/1',
            'citation_type': 'url_citation',
            'title': '1',
        }])
        self.assertEqual(output['usage']['cost_usd'], 0.058)
        self.assertEqual(captured['authorization'], 'Bearer test-key')
        self.assertEqual(captured['payload']['tools'], [{
            'type': 'x_search',
            'from_date': '2026-07-22',
            'to_date': '2026-07-29',
            'allowed_x_handles': ['example'],
        }])
        self.assertNotIn('web_search', json.dumps(captured['payload']))

    def test_grok_wrapper_returns_partial_when_structured_citations_are_missing(self):
        response = {
            'status': 'completed',
            'output': [{
                'type': 'message',
                'content': [{'type': 'output_text', 'text': 'URLなし', 'annotations': []}],
            }],
            'usage': {
                'cost_in_usd_ticks': 0,
                'server_side_tool_usage_details': {'x_search_calls': 1},
            },
        }
        result, _ = self.run_grok_wrapper(response)

        self.assertEqual(result.returncode, 3, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output['status'], 'partial')
        self.assertIn('No structured citation annotations were returned.', output['warnings'])

    def test_grok_wrapper_rejects_overly_broad_date_range_before_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            prompt = Path(tmp) / 'prompt.md'
            prompt.write_text('調査して')
            env = os.environ.copy()
            env['XAI_API_KEY'] = 'test-key'
            result = subprocess.run(
                [
                    str(ROOT / 'wrappers' / 'bin' / 'grok-x-research.example'),
                    '--prompt-file',
                    str(prompt),
                    '--from-date',
                    '2026-01-01',
                    '--to-date',
                    '2026-07-29',
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=False,
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn('Date range must not exceed 31 calendar days.', result.stderr)


if __name__ == '__main__':
    unittest.main()
