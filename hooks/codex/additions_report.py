#!/usr/bin/env python3
"""Observe changed files and added code patterns. This does not decide necessity."""
import argparse
import difflib
import json
from pathlib import Path
import re
import subprocess


PATTERNS = {
    'external_call_pattern': r'\b(?:fetch\s*\(|requests\.(?:get|post|put|delete)\s*\(|httpx\.|subprocess\.(?:run|Popen)\s*\(|exec_command\s*\(|(?:Head|Copy|Get|Put)ObjectCommand\s*\()',
    'recovery_or_limit_pattern': r'\b(?:retry|retries|fallback|timeout)\b',
    'state_or_flag_pattern': r'\b(?:useState|featureFlag|feature_flag|flag|process\.env|os\.environ)\b',
    'option_pattern': r'(?:^|\s)--[a-z][a-z0-9-]*',
    'branch_pattern': r'^\s*(?:if\s*\(|if\s+|elif\s+|else\b|case\s+)',
}


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True)


def private_path(path):
    return any(p.startswith('.env') or p in ('.ssh', '.aws', '.config', 'credentials')
               or re.search(r'(?:private[_-]?key|id_rsa|id_ed25519)', p)
               for p in Path(path).parts)


def observe(root, base='HEAD'):
    # Resolve the reference first: an invalid base must not look like an empty file.
    git(root, 'rev-parse', '--verify', base + '^{commit}')
    existing = set(git(root, 'ls-tree', '-r', '--name-only', '-z', base).split('\0'))
    tracked = git(root, 'diff', '--name-only', '-z', base, '--').split('\0')
    new = git(root, 'ls-files', '--others', '--exclude-standard', '-z').split('\0')
    paths = sorted({p for p in tracked + new if p and not private_path(p)})
    additions = []
    for path in paths:
        file = root / path
        if file.is_symlink() or not file.is_file():
            continue
        try:
            current = file.read_text()
        except UnicodeError:
            continue
        previous = git(root, 'show', f'{base}:{path}') if path in existing else ''
        line = 0
        for change in difflib.unified_diff(previous.splitlines(), current.splitlines(), n=0):
            if change.startswith('@@'):
                line = int(re.search(r'\+(\d+)', change).group(1)) - 1
            elif change.startswith('+') and not change.startswith('+++'):
                line += 1
                for kind, pattern in PATTERNS.items():
                    if re.search(pattern, change[1:], re.I):
                        additions.append({'file': path, 'line': line, 'pattern': kind})
            elif not change.startswith(('-', '---', '+++')):
                line += 1
    return {
        'kind': 'change-observations', 'base': base, 'changed_files': paths,
        'new_files': [p for p in paths if p not in existing],
        'new_test_files': [p for p in paths if p not in existing and re.search(r'(?:^test_|\.test\.|\.spec\.)', Path(p).name)],
        'added_patterns': additions,
        'meaning': 'Pattern observations only; not proof of execution, request scope, harm or necessity.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--base', default='HEAD')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = json.dumps(observe(args.root.resolve(), args.base), ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(result + '\n')
    else:
        print(result)


if __name__ == '__main__':
    main()
