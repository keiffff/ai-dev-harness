#!/usr/bin/env python3
"""Read a repository's private skill index without adding files to its checkout."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


DEFAULT_REGISTRY = Path.home() / '.local/share/agent-work-memory/knowledge/project-skills/registry.json'


def registry_path() -> Path:
    return Path(os.environ.get('CODEX_PROJECT_SKILLS_REGISTRY', str(DEFAULT_REGISTRY))).expanduser()


def common_directory(cwd: Path) -> str | None:
    result = subprocess.run(
        ['git', '-C', str(cwd), 'rev-parse', '--path-format=absolute', '--git-common-dir'],
        check=False, capture_output=True, text=True,
    )
    if result.returncode == 128 and 'not a git repository' in result.stderr.lower():
        return None
    result.check_returncode()
    path = Path(result.stdout.strip())
    if not path.is_absolute():
        raise ValueError('Git did not return an absolute common directory')
    return str(path.resolve())


def load_registry(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or any(
        not isinstance(key, str) or not isinstance(files, list)
        or any(not isinstance(file, str) or not Path(file).is_absolute() for file in files)
        for key, files in data.items()
    ):
        raise ValueError('Registry must map common Git directories to absolute SKILL.md paths')
    return data


def skill_entry(path: str) -> dict[str, str]:
    file = Path(path)
    if file.name != 'SKILL.md':
        raise ValueError('Registered skills must name a SKILL.md file')
    with file.open(encoding='utf-8') as stream:
        header = []
        if stream.readline().strip() == '---':
            for line in stream:
                if line.strip() == '---':
                    break
                header.append(line.rstrip('\n'))
    return {'id': file.parent.name, 'path': str(file), 'metadata': '\n'.join(header)}


def skill_index(cwd: Path, registry: Path | None = None) -> dict:
    data = load_registry(registry if registry is not None else registry_path())
    if not data:
        return {'repository': None, 'skills': []}
    repository = common_directory(cwd)
    if repository is None:
        return {'repository': None, 'skills': []}
    entries = [skill_entry(path) for path in data.get(repository, [])]
    if len({entry['id'] for entry in entries}) != len(entries):
        raise ValueError('Registered skill folder names must be distinct within a project')
    return {'repository': repository, 'skills': entries}


def read_skill(cwd: Path, skill_id: str, registry: Path | None = None) -> str:
    for entry in skill_index(cwd, registry)['skills']:
        if entry['id'] == skill_id:
            return Path(entry['path']).read_text(encoding='utf-8')
    raise ValueError('That skill is not registered for the current repository')


def register(cwd: Path, files: list[Path], registry: Path | None = None) -> dict:
    target = registry if registry is not None else registry_path()
    data = load_registry(target)
    repository = common_directory(cwd)
    if repository is None:
        raise ValueError('Registration requires a Git checkout')
    paths = [str(file.expanduser().resolve(strict=True)) for file in files]
    entries = [skill_entry(path) for path in paths]
    if len({entry['id'] for entry in entries}) != len(entries):
        raise ValueError('Registered skill folder names must be distinct within a project')
    data[repository] = paths
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    return {'repository': repository, 'skills': entries}


def render_context(cwd: str | None) -> str:
    if not cwd:
        return ''
    try:
        index = skill_index(Path(cwd))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'External project skill index unavailable: {error}', file=sys.stderr)
        return 'External project skills for this checkout are unavailable; earlier checkout indexes do not apply.'
    return (
        'External project skills for the current checkout (replaces any earlier checkout index). '
        'Read relevant listed SKILL.md files when choosing project procedures; other projects are not included:\n'
        + json.dumps(index, ensure_ascii=False)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['list', 'read', 'register'])
    parser.add_argument('--cwd', type=Path, default=Path.cwd())
    parser.add_argument('--registry', type=Path)
    parser.add_argument('--skill')
    parser.add_argument('--skill-file', type=Path, action='append')
    args = parser.parse_args()
    try:
        if args.action == 'read':
            if not args.skill:
                parser.error('read requires --skill')
            print(read_skill(args.cwd, args.skill, args.registry), end='')
        else:
            if args.action == 'register' and not args.skill_file:
                parser.error('register requires --skill-file (repeat for multiple skills)')
            result = register(args.cwd, args.skill_file, args.registry) if args.action == 'register' else skill_index(args.cwd, args.registry)
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
