#!/usr/bin/env python3
"""Refresh an existing search record from its maintained Markdown entry."""
import argparse
import json
import re
from pathlib import Path


def sync_record(index_path, entry_path, record_id):
    index_path, entry_path = Path(index_path), Path(entry_path)
    data = json.loads(index_path.read_text())
    records = [r for r in data['records'] if r['id'] == record_id]
    if len(records) != 1:
        raise ValueError('Expected one existing index record: ' + record_id)
    text = entry_path.read_text()
    headings = list(re.finditer(r'^## ' + re.escape(record_id) + r' (.+)$', text, re.M))
    if len(headings) != 1:
        raise ValueError('Expected one maintained Markdown entry: ' + record_id)
    start = headings[0].end()
    next_heading = re.search(r'^## ', text[start:], re.M)
    body = text[start:start + next_heading.start() if next_heading else len(text)].strip()
    state = re.search(r'\*\*確認状態：\*\*\s*([^\n]+)', body)
    if not state:
        raise ValueError('Maintained entry has no verification-state field')
    records[0]['body'] = body
    records[0]['state'] = state.group(1).rstrip('。')
    index_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', required=True, type=Path)
    parser.add_argument('--entry', required=True, type=Path)
    parser.add_argument('--id', required=True)
    args = parser.parse_args()
    sync_record(args.index, args.entry, args.id)
