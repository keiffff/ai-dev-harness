"""Replay private, pre-cut native histories and compare evidence-bound assessments.

Case files, history seeds, rubrics and results stay outside the shared repository.
This extends instruction-load's native trace observation, not the agent runtime.
"""
import argparse
import hashlib
import json
import os
import shlex
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from evaluate import hashes, trace_metrics


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def skill_receipt(root):
    return {p.name: hashes(p) for p in sorted(root.iterdir()) if p.is_dir()} if root.exists() else {}


def frozen_history(seed):
    """Use only the audited seed, never resolve its id to a newer live thread."""
    messages = []
    for line in seed.read_text().splitlines()[1:]:
        item = json.loads(line)
        payload = item.get('payload', {})
        if item.get('type') != 'response_item' or payload.get('type') != 'message':
            continue
        if payload.get('role') not in ('user', 'assistant'):
            continue
        content = payload.get('content', [])
        text = '\n'.join(part['text'] for part in content
                         if isinstance(part, dict) and isinstance(part.get('text'), str))
        if text:
            messages.append({'role': payload['role'], 'text': text})
    return messages


def artifact_receipt(run):
    paths = [run / 'answer.txt']
    paths += sorted((run / 'project').rglob('*'))
    return {p.relative_to(run).as_posix(): digest(p) for p in paths
            if p.is_file() and '.agents' not in p.relative_to(run).parts}


def run_case(case_file, skills_root, output_dir, codex_bin, label, harness_root=None, vetted_hooks=False,
             claude_cli=None):
    case = read_json(case_file)
    base = case_file.resolve().parent
    request = (base / case['request_file']).read_text()
    scope = (base / case['scope_file']).read_text()
    seed = base / case['seed_file']
    first = json.loads(seed.read_text().splitlines()[0])
    if (first.get('type') != 'session_meta'
            or first.get('payload', {}).get('id') != case['session_id']
            or first['payload'].get('history_base')
            or first['payload'].get('forked_from_id')):
        raise ValueError('Use a self-contained cutoff seed matching the session id')
    history = frozen_history(seed)
    # A fresh native task receives the frozen conversation as quoted data.
    # `exec fork <id>` would read the live history, not this cutoff seed.
    actor_input = (('Prior conversation (frozen at the requested cutoff):\n'
                    + json.dumps(history, ensure_ascii=False)
                    + '\n\nCurrent request:\n') if history else '') + request
    # Rubric hash is provenance only. Never load its content into the actor.
    rubric = base / case['rubric_file']
    output_dir.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix='trial-', dir=output_dir.resolve()))
    project = run / 'project'
    project.mkdir()
    skill_files = {}
    disabled = []
    for skill in sorted(skills_root.iterdir()):
        if not (skill / 'SKILL.md').is_file():
            continue
        shutil.copytree(skill, project / '.agents/skills' / skill.name)
        skill_files[skill.name] = hashes(skill)
        for root in (Path.home() / '.codex/skills', Path.home() / '.agents/skills'):
            path = root / skill.name / 'SKILL.md'
            if path.exists():
                disabled.append('{path=' + json.dumps(str(path)) + ',enabled=false}')
    if not skill_files:
        raise ValueError('No skill snapshot found')
    if case.get('files_dir'):
        source = base / case['files_dir']
        if (source / '.agents').exists():
            raise ValueError('Initial files must not replace the skill snapshot')
        shutil.copytree(source, project, dirs_exist_ok=True, symlinks=True)
    initial = hashes(project)
    harness_files = {}
    hook_config = []
    env = os.environ.copy()
    if claude_cli:
        claude_cli = claude_cli.resolve()
        if not claude_cli.is_file() or not os.access(claude_cli, os.X_OK):
            raise ValueError('The supplied Claude CLI must be an existing executable')
        env['CLAUDE_STRATEGIC_CLI'] = str(claude_cli)
    if harness_root:
        harness_root = harness_root.resolve()
        for relative in ('codex/AGENTS.md', 'hooks/codex/runtime-contract-context.py',
                         'hooks/codex/hook_utils.py', 'hooks/codex/runtime-contract.md',
                         'wrappers/bin/claude-strategic-review.example',
                         'hooks/codex/source_ledger.py', 'hooks/codex/reader_delivery.py',
                         'hooks/codex/additions_report.py'):
            file = harness_root / relative
            if file.is_file():
                harness_files[relative] = digest(file)
        if not vetted_hooks:
            raise ValueError('Harness hooks must be explicitly vetted before automation can execute them')
        agents = project / 'AGENTS.md'
        original = agents.read_text() if agents.exists() else ''
        agents.write_text((harness_root / 'codex/AGENTS.md').read_text() + '\n' + original)
        command = '/usr/bin/python3 ' + shlex.quote(str(harness_root / 'hooks/codex/runtime-contract-context.py'))
        if case.get('submitted_prompts_file'):
            prompts_path = base / case['submitted_prompts_file']
            prompts = read_json(prompts_path)
            original_text = '\n'.join([r['text'] for r in history] + [request])
            if (not isinstance(prompts, list) or not prompts
                    or any(not isinstance(p, str) or not p.strip() or p.strip() not in original_text for p in prompts)
                    or not request.strip().endswith(prompts[-1].strip())):
                raise ValueError('Historical prompt events must occur verbatim in the audited input and end at its current request')
            fixture = run / 'prompt-events.json'
            fixture.write_text(json.dumps({'actor_input_sha256': hashlib.sha256(actor_input.encode()).hexdigest(),
                                           'submitted_prompts': prompts}, ensure_ascii=False))
            adapter = Path(__file__).with_name('replay_hook.py')
            command = ('/usr/bin/python3 ' + shlex.quote(str(adapter))
                       + ' --handler ' + shlex.quote(str(harness_root/'hooks/codex/runtime-contract-context.py'))
                       + ' --fixture ' + shlex.quote(str(fixture))
                       + ' --receipt ' + shlex.quote(str(run/'prompt-events-receipt.json')))
        events = ['SessionStart', 'UserPromptSubmit', 'SubagentStart', 'PreToolUse', 'PostToolUse']
        if case.get('checked_writer_display'):
            events.append('Stop')
        for event in events:
            hook_config += ['-c', f'hooks.{event}=[{{hooks=[{{type="command",command={json.dumps(command)}}}]}}]']
        env.update(CODEX_RUNTIME_CONTRACT_STATE_DIR=str(run / 'runtime-state'),
                   CODEX_READER_DELIVERY_STAGE_DIR=str(project / '.reader-delivery-staged'),
                   CODEX_RUNTIME_CONTRACT_HANDLER=str(harness_root / 'hooks/codex/runtime-contract-context.py'),
                   CODEX_RUNTIME_CONTRACT=str(harness_root / 'hooks/codex/runtime-contract.md'),
                   CODEX_SOURCE_LEDGER_DIR=str(run / 'source-ledger'),
                   CODEX_SOURCE_LEDGER_SCRIPT=str(harness_root / 'hooks/codex/source_ledger.py'),
                   CLAUDE_STRATEGIC_REVIEW_WRAPPER=str(harness_root / 'wrappers/bin/claude-strategic-review.example'))
    (run / 'input.txt').write_text(request)
    manifest = {'case': case['id'], 'label': label,
                'request_sha256': hashlib.sha256(request.encode()).hexdigest(),
                'scope_sha256': hashlib.sha256(scope.encode()).hexdigest(),
                'seed_sha256': digest(seed), 'session_id': case['session_id'],
                'history_delivery': 'frozen_messages_in_fresh_native_task',
                'history_messages': len(history),
                'actor_input_sha256': hashlib.sha256(actor_input.encode()).hexdigest(),
                'rubric_sha256': digest(rubric), 'initial_files': {
                    k: v for k, v in initial.items() if not k.startswith('.agents/')},
                'skill_files': skill_files, 'model': case['model'],
                'harness_files': harness_files,
                'submitted_prompts_sha256': digest(base/case['submitted_prompts_file']) if case.get('submitted_prompts_file') else None,
                'claude_cli': str(claude_cli) if claude_cli else None,
                'reasoning': case['reasoning'], 'rubric_sent_to_actor': False,
                'runner_sha256': digest(Path(__file__)),
                'harness_revision': subprocess.check_output(
                    ['git', 'rev-parse', 'HEAD'], cwd=Path(__file__).resolve().parents[2], text=True).strip()}
    (run / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    command = [str(codex_bin), 'exec', '-m', case['model'],
               '-c', 'model_reasoning_effort=' + json.dumps(case['reasoning']),
               '-c', 'skills.config=[' + ','.join(disabled) + ']',
               '-c', 'developer_instructions=' + json.dumps(scope),
               '--approve-for-me', '--skip-git-repo-check', '-C', str(project),
               '--json', '-o', str(run / 'answer.txt'), '-']
    if vetted_hooks:
        command.insert(1, '--dangerously-bypass-hook-trust')
    command[2:2] = hook_config
    print('START ' + str(run), flush=True)
    began = time.perf_counter()
    with (run / 'trace.jsonl').open('x') as out, (run / 'stderr.txt').open('x') as err:
        actor = subprocess.run(command, input=actor_input, text=True, cwd=project, stdout=out, stderr=err, env=env)
    answer = (run / 'answer.txt').read_text() if (run / 'answer.txt').is_file() else ''
    result = {'process_exit': actor.returncode, 'seconds': time.perf_counter() - began,
              'execution_status': 'native_error' if actor.returncode else 'completed' if answer.strip() else 'answer_missing',
              'answer_present': bool(answer.strip()), 'pass': None,
              'assessment_required': True, 'artifacts': artifact_receipt(run),
              **trace_metrics(run / 'trace.jsonl')}
    result['skill_snapshot_unchanged'] = skill_receipt(project / '.agents/skills') == skill_files
    result['pass'] = False if actor.returncode or not answer.strip() else None
    if case.get('submitted_prompts_file') and not (run/'prompt-events-receipt.json').is_file():
        result.update({'execution_status': 'source_fixture_not_applied', 'pass': False})
    (run / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print('END ' + str(run), flush=True)
    return run


def assessed(run, assessment_file, rubric):
    result = read_json(run / 'result.json')
    manifest = read_json(run / 'manifest.json')
    assessment = read_json(assessment_file)
    if result['artifacts'] != artifact_receipt(run):
        raise ValueError('Artifacts changed after execution')
    if assessment['artifacts'] != result['artifacts']:
        raise ValueError('Assessment does not match the actual artifacts')
    if assessment.get('rubric_sha256') != manifest['rubric_sha256']:
        raise ValueError('Assessment is not bound to this rubric')
    checks = assessment['checks']
    ids = [c['id'] for c in checks]
    expected = [c['id'] for c in rubric['checks']]
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise ValueError('Assessment must cover every rubric criterion exactly once')
    for check in checks:
        if check['verdict'] not in ('pass', 'fail', 'unknown') or not check.get('reason') or not check.get('evidence'):
            raise ValueError('Every assessment needs a verdict and evidence')
        for evidence in check['evidence']:
            path = Path(evidence['file'])
            if path.is_absolute() or '..' in path.parts or str(path) not in result['artifacts']:
                raise ValueError('Evidence must refer to a recorded artifact')
            quote = evidence.get('quote')
            if not quote or quote not in (run / path).read_text():
                raise ValueError('Evidence quote does not occur in the artifact')
    snapshot_unchanged = (result['skill_snapshot_unchanged']
                          and skill_receipt(run / 'project/.agents/skills') == manifest['skill_files'])
    if result['pass'] is False or not snapshot_unchanged or any(c['verdict'] == 'fail' for c in checks):
        passed = False
    elif any(c['verdict'] == 'unknown' for c in checks):
        passed = None
    else:
        passed = True
    return {'pass': passed, 'checks': checks, 'seconds': result['seconds'],
            'skill_snapshot_unchanged': snapshot_unchanged,
            'native_usage': result['native_usage'],
            'command_executions': result['command_executions'],
            'skill_read_commands': result['skill_read_commands'],
            'human_corrections': assessment.get('human_corrections'),
            'stages': assessment.get('stages', {}),
            'answer': (run / 'answer.txt').read_text() if (run / 'answer.txt').is_file() else '',
            'drafts': {name: (run / name).read_text() for name in result['artifacts']
                       if name.startswith('project/') and Path(name).suffix in ('.md', '.txt')},
            'artifacts': result['artifacts']}


def compare(before, after, before_assessment, after_assessment, rubric_file):
    left = read_json(before / 'manifest.json')
    right = read_json(after / 'manifest.json')
    for key in ('case', 'request_sha256', 'scope_sha256', 'seed_sha256',
                'rubric_sha256', 'initial_files', 'model', 'reasoning'):
        if left[key] != right[key]:
            raise ValueError('Incomparable conditions: ' + key)
    for key in ('history_delivery', 'actor_input_sha256', 'claude_cli', 'submitted_prompts_sha256'):
        if left.get(key) != right.get(key):
            raise ValueError('Incomparable conditions: ' + key)
    if left['rubric_sha256'] != digest(rubric_file):
        raise ValueError('Rubric changed after execution')
    rubric = read_json(rubric_file)
    return {'case': left['case'], 'before': assessed(before, before_assessment, rubric),
            'after': assessed(after, after_assessment, rubric),
            'skills_changed': left['skill_files'] != right['skill_files'],
            'comparison_limits': 'Single replay pair; no population success rate, causal production improvement or inferred monetary cost.'}


def suite(case_list, plan_file):
    """Require the declared cases and one snapshot per condition, including failures."""
    expected = read_json(case_list)['cases']
    plan = read_json(plan_file)['comparisons']
    if len(expected) != len(set(expected)) or not expected:
        raise ValueError('Declare a nonempty unique case list')
    actual = [p['case'] for p in plan]
    if len(actual) != len(set(actual)) or set(actual) != set(expected):
        raise ValueError('Suite must contain every declared case exactly once')
    reports = []
    snapshots = {}
    for entry in plan:
        paths = {key: (plan_file.resolve().parent / entry[key]).resolve() for key in (
            'before', 'after', 'before_assessment', 'after_assessment', 'rubric_file')}
        report = compare(**paths)
        if report['case'] != entry['case']:
            raise ValueError('Suite case does not match the execution')
        for condition in ('before', 'after'):
            manifest = read_json(paths[condition] / 'manifest.json')
            files = {'skills': manifest['skill_files'], 'harness': manifest.get('harness_files', {})}
            if condition in snapshots and snapshots[condition] != files:
                raise ValueError('Do not mix different snapshots within a condition')
            snapshots[condition] = files
        reports.append(report)
    regressions = [r['case'] for r in reports if r['before']['pass'] is True and r['after']['pass'] is not True]
    unresolved = [r['case'] for r in reports if r['after']['pass'] is not True]
    improvements = [r['case'] for r in reports if r['before']['pass'] is False and r['after']['pass'] is True]
    return {'case_list_sha256': digest(case_list), 'comparisons': reports,
            'regressions': regressions, 'unresolved': unresolved, 'improvements': improvements,
            'adoption': 'not_ready' if unresolved else 'no_regression_observed',
            'summed_execution_seconds': {side: sum(r[side]['seconds'] for r in reports) for side in ('before', 'after')},
            'limits': 'Assessment scope only; no automatic publication, stable success rate or production efficacy claim.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='operation', required=True)
    run = subs.add_parser('run')
    for name in ('case-file', 'skills-root', 'output-dir', 'codex-bin'):
        run.add_argument('--' + name, required=True, type=Path)
    run.add_argument('--label', required=True)
    run.add_argument('--harness-root', type=Path)
    run.add_argument('--claude-cli', type=Path,
                     help='Verified existing CLI, preserving its configured authentication and model')
    run.add_argument('--vetted-hooks', action='store_true',
                     help='Invocation-only hook trust for sources already reviewed by the caller; does not bypass sandbox or approvals')
    diff = subs.add_parser('compare')
    for name in ('before', 'after', 'before-assessment', 'after-assessment', 'rubric-file', 'output'):
        diff.add_argument('--' + name, required=True, type=Path)
    all_cases = subs.add_parser('suite')
    for name in ('case-list', 'plan-file', 'output'):
        all_cases.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    if args.operation == 'run':
        folder = run_case(args.case_file, args.skills_root, args.output_dir, args.codex_bin, args.label,
                          args.harness_root, args.vetted_hooks, args.claude_cli)
        result = read_json(folder / 'result.json')
        return 0 if result['execution_status'] == 'completed' else 1
    elif args.operation == 'compare':
        report = compare(args.before, args.after, args.before_assessment, args.after_assessment, args.rubric_file)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    else:
        report = suite(args.case_list, args.plan_file)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report['adoption'] == 'no_regression_observed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
