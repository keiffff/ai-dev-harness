"""Adapt a frozen-history container to the actual historical prompt events.

The actor still receives the identical frozen conversation. Its serialization is
not itself a historical user utterance, so it must not become current_request.
This adapter is evaluation-only and delegates to the unmodified runtime hook.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import os
import sqlite3


def dispatch(payload, fixture, handler, receipt):
    if (payload.get('hook_event_name') == 'UserPromptSubmit'
            and isinstance(payload.get('prompt'), str)
            and hashlib.sha256(payload['prompt'].encode()).hexdigest() == fixture['actor_input_sha256']):
        prompts = fixture['submitted_prompts']
        if not prompts or not all(isinstance(text, str) and text for text in prompts):
            raise ValueError('The historical prompt fixture must be nonempty verbatim strings')
        ledger = handler.with_name('source_ledger.py')
        if ledger.is_file():
            spec = importlib.util.spec_from_file_location('replay_source_ledger', ledger)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if not module.read_records(payload['session_id']):
                for prompt in prompts[:-1]:
                    module.append_prompt(payload['session_id'], prompt, origin='replayed-submitted-prompt')
        payload = {**payload, 'prompt': prompts[-1]}
        history = fixture.get('history_messages')
        history_path = os.environ.get('CODEX_THREAD_HISTORY_DB')
        if history is not None and history_path:
            # Reproduce the app's saved-dialogue input for existing producers.
            # Only the same frozen actor input is used, never later live turns.
            with sqlite3.connect(history_path) as db:
                db.execute('CREATE TABLE IF NOT EXISTS thread_items '
                           '(thread_id TEXT, created_at_ms INTEGER, item_type TEXT, item_json TEXT)')
                db.execute('DELETE FROM thread_items WHERE thread_id=?', (payload['session_id'],))
                for index, message in enumerate(history):
                    if message['role'] == 'user':
                        kind = 'userMessage'
                        item = {'type': kind, 'content': [{'type': 'text', 'text': message['text']}]}
                    elif message['role'] == 'assistant':
                        kind = 'agentMessage'
                        item = {'type': kind, 'phase': 'final_answer', 'text': message['text']}
                    else:
                        raise ValueError('Frozen dialogue must preserve user/assistant roles')
                    db.execute('INSERT INTO thread_items VALUES (?,?,?,?)',
                               (payload['session_id'], index+1, kind, json.dumps(item)))
        receipt.write_text(json.dumps({
            'actor_input_sha256': fixture['actor_input_sha256'],
            'submitted_prompts': len(prompts),
            'current_prompt_sha256': hashlib.sha256(prompts[-1].encode()).hexdigest(),
            'source': 'audited_historical_prompt_events',
        }))
    return subprocess.run([sys.executable, str(handler)], input=json.dumps(payload), text=True).returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--handler', type=Path, required=True)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    return dispatch(json.load(sys.stdin), json.loads(args.fixture.read_text()), args.handler, args.receipt)


if __name__ == '__main__':
    raise SystemExit(main())
