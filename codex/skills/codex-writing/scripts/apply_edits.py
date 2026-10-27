"""Apply source-grounded literal edits without regenerating untouched prose."""
import argparse
import json
from pathlib import Path


def apply_edits(draft, corrections, replacements, sources):
    if len(corrections) != len(replacements):
        raise ValueError('Every selected correction needs exactly one replacement')
    spans = []
    for correction, replacement in zip(corrections, replacements):
        old = correction['old']
        quote = correction['quote']
        if (not old or draft.count(old) != 1 or not quote
                or quote not in sources.get(correction['source'], '')
                or not correction.get('reason') or not isinstance(replacement, str)):
            raise ValueError('Correction needs a unique draft span and an exact source quote')
        start = draft.index(old)
        spans.append((start, start + len(old), replacement))
    spans.sort()
    if any(left[1] > right[0] for left, right in zip(spans, spans[1:])):
        raise ValueError('Overlapping corrections are ambiguous')
    result = draft
    for start, end, replacement in reversed(spans):
        result = result[:start] + replacement + result[end:]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--draft', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True,
                        help='JSON with corrections, replacements and source strings')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.draft.resolve() == args.output.resolve():
        parser.error('Keep the original draft as evidence; use a separate output path')
    plan = json.loads(args.plan.read_text())
    with args.draft.open(encoding='utf-8', newline='') as handle:
        draft = handle.read()
    updated = apply_edits(draft, plan['corrections'], plan['replacements'], plan['sources'])
    with args.output.open('w', encoding='utf-8', newline='') as handle:
        handle.write(updated)


if __name__ == '__main__':
    main()
