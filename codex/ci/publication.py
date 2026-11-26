"""Run project-owned checks before a protected publication."""

from fnmatch import fnmatchcase
import json
import re
from urllib.parse import quote, urlencode, urlparse


SHA = re.compile(r'[0-9a-f]{40}')
PR_PATH = re.compile(r'/([\w.-]+/[\w.-]+)/pull/[1-9][0-9]*')


def select_item_checks(required, registered, requested):
    """Compile a batch's check IDs to project-owned callables before iterating."""
    selected = dict(required)
    excluded = []
    for name in dict.fromkeys(requested):
        if name in selected:
            continue
        if name in registered:
            selected[name] = registered[name]
        else:
            excluded.append(name)
    return tuple(selected.values()), tuple(excluded)


def merge_arguments(args):
    """Resolve the target and existing head pin without interpreting GitHub options."""
    values = {
        '--repo', '-R', '--match-head-commit', '--subject', '-t', '--body', '-b',
        '--body-file', '-F', '--author-email', '-A',
    }
    target = None
    repo = None
    head = None
    disable_auto = False
    position = 0
    tokens = iter(enumerate(args, 1))
    for index, arg in tokens:
        option, eq, value = arg.partition('=')
        if not eq and option[:2] in values and not option.startswith('--') and len(option) > 2:
            option, eq, value = option[:2], '=', arg[2:]
        if option in values:
            if not eq:
                _, value = next(tokens, (0, ''))
                if not value:
                    raise ValueError(f'{option} requires a value.')
            if option in {'--repo', '-R'}:
                repo = value
            if option == '--match-head-commit':
                head = value
        elif arg.startswith('-'):
            if arg == '--':
                tail = list(tokens)
                if len(tail) > 1 or (tail and target is not None):
                    raise ValueError('Specify one pull request to merge.')
                if tail:
                    position, target = tail[0]
                break
            if option == '--disable-auto':
                disable_auto = not eq or value == 'true'
        elif target is None:
            position, target = index, arg
        else:
            raise ValueError('Specify one pull request to merge.')
    return target, repo, head, position, disable_auto


def verify_step(gh, repo, head, rule):
    workflow, name, step = (rule[key] for key in ('workflow', 'job', 'step'))
    query = urlencode({'head_sha': head, 'event': 'pull_request', 'per_page': 1})
    runs = gh('api', f'repos/{repo}/actions/workflows/{quote(workflow, safe="")}/runs?{query}')
    run = next(iter(runs['workflow_runs']), None)
    if run and run['head_sha'] == head:
        endpoint = f'repos/{repo}/actions/runs/{run["id"]}/attempts/{run["run_attempt"]}/jobs?per_page=100'
        pages = gh('api', '--paginate', '--slurp', endpoint)
        jobs = [job for page in pages for job in page['jobs']
                if job['name'] == name and job['head_sha'] == head]
        if len(jobs) == 1:
            job = jobs[0]
            steps = [item for item in job['steps'] if item['name'] == step]
            if len(steps) == 1 and job['conclusion'] == steps[0]['conclusion'] == 'success':
                return
            observed = steps[0]['conclusion'] if len(steps) == 1 else 'missing'
            raise ValueError(f'Required CI step {name} / {step}: {observed or "pending"} '
                             f'(job: {job["conclusion"] or "pending"}) for {head}.')
    raise ValueError(f'No matching CI result for {name} / {step} on {head}.')


def verify_merge(gh, git, registry, args):
    target, explicit_repo, requested_head, position, disable_auto = merge_arguments(args)
    if disable_auto:
        return None
    lookup = [target] if target else []
    if explicit_repo:
        lookup.extend(('--repo', explicit_repo))
    pr = gh('pr', 'view', *lookup, '--json', 'url,baseRefOid,headRefOid,baseRefName')
    url = urlparse(pr['url'])
    match = PR_PATH.fullmatch(url.path)
    if url.scheme != 'https' or url.netloc != 'github.com' or not match:
        return None
    repo = match[1]
    rules = [rule for rule in registry.get(repo.lower(), [])
             if rule.get('base', pr['baseRefName']) == pr['baseRefName']]
    if not rules:
        return None
    base, head = pr['baseRefOid'], pr['headRefOid']
    if not all(isinstance(oid, str) and SHA.fullmatch(oid) for oid in (base, head)):
        raise ValueError('GitHub did not return exact pull request source and target SHAs.')
    paths = git('diff', '--name-only', '-z', '--no-renames', f'{base}...{head}', '--').split('\0')
    selected = [rule for rule in rules if any(fnmatchcase(path, pattern)
                for path in paths if path for pattern in rule['paths'])]
    if not selected:
        return None
    if requested_head and requested_head != head:
        raise ValueError('The requested merge SHA differs from the current pull request head.')
    for rule in selected:
        verify_step(gh, repo, head, rule)
    return position, pr['url'], head


def configured_merge(ci, root, args):
    with (root / 'publication-sources.json').open(encoding='utf-8') as source:
        registry = json.load(source)
    if registry and args not in (['--help'], ['-h']):
        return verify_merge(ci.gh, lambda *argv: ci.git('.', *argv, strip=False), registry, args)
    return None
