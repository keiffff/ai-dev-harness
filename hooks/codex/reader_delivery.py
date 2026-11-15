"""Keep Claude artifacts owned by their writer within the task.

This checks custody, not prose, facts, completion or human authorization.
"""
import hashlib
import fcntl
import json
import os
from pathlib import Path
import re
import tempfile


def locations(session):
    key = hashlib.sha256(session.encode()).hexdigest()
    state = Path(os.environ.get('CODEX_RUNTIME_CONTRACT_STATE_DIR',
                                str(Path.home()/'.codex/hook-state/runtime-contract')))
    staged_root = Path(os.environ.get('CODEX_READER_DELIVERY_STAGE_DIR',
                                      str(Path(tempfile.gettempdir())/'codex-reader-deliveries')))
    return staged_root/key, state.parent/'reader-deliveries'/(key+'.json')


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix('.'+str(os.getpid())+'.tmp')
    fd = os.open(temporary, os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, ensure_ascii=False)
    os.replace(temporary, path)


def stage(session, source_ref, output, body, supersedes=None):
    if not session or not source_ref:
        return
    pending, _ = locations(session)
    pending = pending/(hashlib.sha256(str(output.resolve()).encode()).hexdigest()+'.json')
    save(pending, {'source_ref': source_ref, 'path': str(output.resolve()),
                   'sha256': hashlib.sha256(body.encode()).hexdigest(), 'body': body,
                   'supersedes': str(supersedes.resolve()) if supersedes else None})


def read(path):
    try:
        result = json.loads(path.read_text())
        if not isinstance(result, dict):
            raise ValueError('Writer custody record must be an object')
        return result
    except FileNotFoundError:
        return {}


def consume(session, source_ref):
    pending, durable = locations(session)
    if not pending.is_dir() or not any(pending.glob('*.json')):
        return
    durable.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = os.open(durable.with_suffix('.lock'), os.O_RDWR|os.O_CREAT, 0o600)
    with os.fdopen(lock, 'r+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        records = read(durable)
        consumed = []
        for file in sorted(pending.glob('*.json'), key=lambda p: p.stat().st_mtime_ns):
            item = read(file)
            if item.get('source_ref') == source_ref:
                if hashlib.sha256(item['body'].encode()).hexdigest() != item['sha256']:
                    raise ValueError('Writer delivery snapshot does not match its digest')
                if item.get('supersedes'):
                    records.pop(item['supersedes'], None)
                snapshot = durable.with_suffix('')/(item['sha256']+'.md')
                snapshot.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                fd = os.open(snapshot, os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o600)
                with os.fdopen(fd, 'w') as body:
                    body.write(item['body'])
                records[item['path']] = {key: item[key] for key in ('source_ref', 'sha256')}
                records[item['path']]['snapshot'] = str(snapshot)
            consumed.append(file)
        save(durable, records)
        for file in consumed:
            file.unlink(missing_ok=True)


def direct_edit_reason(session, source_ref, payload):
    if payload.get('tool_name') not in ('apply_patch', 'Edit', 'Write'):
        return None
    inputs = payload.get('tool_input', {})
    if not isinstance(inputs, dict):
        return None
    command = inputs.get('command', '')
    paths = re.findall(r'^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$', command, re.M) if isinstance(command, str) else []
    if isinstance(inputs.get('file_path'), str):
        paths.append(inputs['file_path'])
    cwd = payload.get('cwd')
    if not isinstance(cwd, str) or not Path(cwd).is_absolute():
        return None
    _, durable = locations(session)
    records = read(durable)
    for path in paths:
        target = Path(path).expanduser()
        target = (target if target.is_absolute() else Path(cwd)/target).resolve()
        record = records.get(str(target))
        if record:
            return ('This file is owned by the Claude writer: '+str(target)+'. '
                    'Read and deliver its saved text unchanged. A new user-requested revision goes '
                    'to claude-writing with the original request, draft and source data. '
                    'Do not create agent-authored editorial or factual correction requests, '
                    'and do not bypass writer ownership through another editing tool.')
    return None
