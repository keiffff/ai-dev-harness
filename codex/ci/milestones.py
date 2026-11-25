"""Collect notification-only PR milestones from the existing GitHub connection."""

import json
import re
from urllib.parse import quote


SHA = re.compile(r'[0-9a-f]{40}')


def schema(db):
    db.executescript('''
        CREATE TABLE IF NOT EXISTS deployment_watches (
            repo TEXT, number INTEGER, sha TEXT NOT NULL, merged_at TEXT NOT NULL,
            PRIMARY KEY(repo,number));
        CREATE TABLE IF NOT EXISTS deployment_jobs (
            repo TEXT, job INTEGER, sha TEXT, completed_at TEXT NOT NULL,
            PRIMARY KEY(repo,job));
    ''')


def sources(root):
    try:
        with (root/'deployment-sources.json').open() as stream:
            return json.load(stream)
    except FileNotFoundError:
        return {}


def merge_ready(pr):
    return (pr.get('state') == 'OPEN' and pr.get('isDraft') is False
            and pr.get('mergeable') == 'MERGEABLE' and pr.get('mergeStateStatus') == 'CLEAN')


def save_notice(db, repo, number, sha, kind, **data):
    return db.execute(
        'INSERT OR IGNORE INTO deliveries(event_key,repo,number,sha,payload) VALUES (?,?,?,?,?)',
        (f'{kind}:{sha}', repo, number, sha, json.dumps(dict(kind=kind, **data))),
    ).rowcount


def observe_pr(db, binding, pr, config):
    repo, number = binding['repo'], binding['number']
    sha = pr.get('headRefOid', '')
    if merge_ready(pr) and SHA.fullmatch(sha):
        return save_notice(db, repo, number, sha, 'merge_ready')
    cfg = config.get(repo.lower())
    if cfg and pr['state'] == 'MERGED' and pr.get('baseRefName') == cfg['branch']:
        merged = (pr.get('mergeCommit') or {}).get('oid', '')
        if SHA.fullmatch(merged) and pr.get('mergedAt'):
            db.execute(
                'INSERT OR IGNORE INTO deployment_watches VALUES (?,?,?,?)',
                (repo, number, merged, pr['mergedAt']),
            )
    return 0


def deployment_evidence(ci, db, repo, cfg, since):
    workflow = quote(cfg['workflow'], safe='')
    runs = ci.gh('api', f'repos/{repo}/actions/workflows/{workflow}/runs?per_page=100')['workflow_runs']
    for run in runs:
        if run['updated_at'] < since:
            continue
        attempt = run.get('run_attempt', 1)
        jobs = ci.gh('api', f'repos/{repo}/actions/runs/{run["id"]}/attempts/{attempt}/jobs')['jobs']
        for job in jobs:
            if (job['name'] != cfg['job'] or job.get('conclusion') != 'success'
                    or job['completed_at'] < since):
                continue
            record = db.execute('SELECT sha FROM deployment_jobs WHERE repo=? AND job=?',
                                (repo, job['id'])).fetchone()
            if record is None:
                log = ci.gh_output('api', f'repos/{repo}/actions/jobs/{job["id"]}/logs')
                matches = set(re.findall(cfg['sha_pattern'], log))
                sha = next(iter(matches)) if len(matches) == 1 else None
                if not isinstance(sha, str) or not SHA.fullmatch(sha):
                    sha = None
                db.execute('INSERT INTO deployment_jobs VALUES (?,?,?,?)',
                           (repo, job['id'], sha, job['completed_at']))
            else:
                sha = record['sha']
            if sha:
                yield job['completed_at'], sha, f'https://github.com/{repo}/actions/runs/{run["id"]}/job/{job["id"]}'


def collect_deployments(ci, root, config):
    accepted = 0
    with ci.database(root) as db:
        repos = db.execute(
            'SELECT repo,MIN(merged_at) AS since FROM deployment_watches GROUP BY repo'
        ).fetchall()
        for group in repos:
            repo = group['repo']
            cfg = config.get(repo.lower())
            if not cfg:
                continue
            watches = db.execute('SELECT * FROM deployment_watches WHERE repo=?', (repo,)).fetchall()
            results = sorted(deployment_evidence(ci, db, repo, cfg, group['since']))
            ancestry = {}
            for watch in watches:
                for completed, deployed, url in results:
                    if completed < watch['merged_at']:
                        continue
                    merge = watch['sha']
                    pair = merge, deployed
                    if pair not in ancestry:
                        ancestry[pair] = (merge == deployed or ci.gh_output(
                            'api', f'repos/{repo}/compare/{merge}...{deployed}', '--jq', '.status'
                        ).strip() in ('ahead', 'identical'))
                    if not ancestry[pair]:
                        continue
                    accepted += save_notice(db, repo, watch['number'], merge, 'deployment_complete',
                                            deployed=deployed, url=url, completed_at=completed,
                                            environment=cfg.get('environment', cfg['branch']))
                    db.execute('DELETE FROM deployment_watches WHERE repo=? AND number=?',
                               (repo, watch['number']))
                    break
    return accepted


def message(item):
    if item['kind'] == 'merge_ready':
        return 'PRがマージ可能になりました。'
    if item['kind'] == 'deployment_complete':
        return f'{item["environment"]}へのデプロイが完了し、このPRの変更が含まれました。'
    return 'CIが失敗しました。'


def notice(row, item):
    return ('This is a notification only for the PR bound to this chat. '
            'Relay the message and links in Japanese, then end the turn. '
            'Do not run tools, edit files, merge, deploy, or update the PR.\n'
            + json.dumps({'message': message(item), 'pr_url': f'https://github.com/{row["repo"]}/pull/{row["number"]}',
                          'sha': row['sha'], **item}, ensure_ascii=False))
