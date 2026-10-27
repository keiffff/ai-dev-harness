"""Replay private, pre-cut native histories and compare evidence-bound assessments.

Case files, history seeds, rubrics and results stay outside the shared repository.
This extends instruction-load's native trace observation, not the agent runtime.
"""
import argparse
import hashlib
import json
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


def artifact_receipt(run):
    paths = [run / 'answer.txt']
    paths += sorted((run / 'project').rglob('*'))
    return {p.relative_to(run).as_posix(): digest(p) for p in paths
            if p.is_file() and '.agents' not in p.relative_to(run).parts}


def run_case(case_file, skills_root, output_dir, codex_bin, label):
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
        shutil.copytree(source, project, dirs_exist_ok=True)
    initial = hashes(project)
    (run / 'input.txt').write_text(request)
    manifest = {'case': case['id'], 'label': label,
                'request_sha256': hashlib.sha256(request.encode()).hexdigest(),
                'scope_sha256': hashlib.sha256(scope.encode()).hexdigest(),
                'seed_sha256': digest(seed), 'session_id': case['session_id'],
                'rubric_sha256': digest(rubric), 'initial_files': {
                    k: v for k, v in initial.items() if not k.startswith('.agents/')},
                'skill_files': skill_files, 'model': case['model'],
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
               '--json', '-o', str(run / 'answer.txt'), 'fork', case['session_id'], '-']
    print('START ' + str(run), flush=True)
    began = time.perf_counter()
    with (run / 'trace.jsonl').open('x') as out, (run / 'stderr.txt').open('x') as err:
        actor = subprocess.run(command, input=request, text=True, cwd=project, stdout=out, stderr=err)
    answer = (run / 'answer.txt').read_text() if (run / 'answer.txt').is_file() else ''
    result = {'process_exit': actor.returncode, 'seconds': time.perf_counter() - began,
              'execution_status': 'native_error' if actor.returncode else 'completed' if answer.strip() else 'answer_missing',
              'answer_present': bool(answer.strip()), 'pass': None,
              'assessment_required': True, 'artifacts': artifact_receipt(run),
              **trace_metrics(run / 'trace.jsonl')}
    result['skill_snapshot_unchanged'] = skill_receipt(project / '.agents/skills') == skill_files
    result['pass'] = False if actor.returncode or not answer.strip() else None
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
            files = read_json(paths[condition] / 'manifest.json')['skill_files']
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
    diff = subs.add_parser('compare')
    for name in ('before', 'after', 'before-assessment', 'after-assessment', 'rubric-file', 'output'):
        diff.add_argument('--' + name, required=True, type=Path)
    all_cases = subs.add_parser('suite')
    for name in ('case-list', 'plan-file', 'output'):
        all_cases.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    if args.operation == 'run':
        folder = run_case(args.case_file, args.skills_root, args.output_dir, args.codex_bin, args.label)
        result = read_json(folder / 'result.json')
        return 0 if result['process_exit'] == 0 and result['answer_present'] else 1
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
