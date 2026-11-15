"""Preserve Claude ownership without language scoring or a Stop loop."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT/'hooks/codex/runtime-contract-context.py'


def module(name):
    spec = importlib.util.spec_from_file_location(name,HOOK.with_name(name+'.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class ReaderDeliveryTests(unittest.TestCase):
    def test_main_patch_is_refused_across_user_corrections_but_other_files_are_allowed(self):
        ledger,reader = module('source_ledger'),module('reader_delivery')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = dict(os.environ,CODEX_SOURCE_LEDGER_DIR=str(root/'source'),
                CODEX_READER_DELIVERY_STAGE_DIR=str(root/'staged'),CODEX_RUNTIME_CONTRACT_STATE_DIR=str(root/'state'))
            env.pop('CODEX_RUNTIME_CONTRACT_HANDLER',None)
            body = root/'body.md'
            body.write_text('Observed result.')
            with patch.dict(os.environ,env):
                ledger.append_prompt('task','Report the observation.')
                reader.stage('task',ledger.request_reference('task'),body,body.read_text())
            def event(kind,**fields):
                process = subprocess.run([sys.executable,str(HOOK)],input=json.dumps({
                    'hook_event_name':kind,'session_id':'task','cwd':directory,**fields}),
                    text=True,capture_output=True,env=env)
                self.assertEqual(process.returncode,0,process.stderr)
                return json.loads(process.stdout) if process.stdout else None
            self.assertIsNone(event('PostToolUse',tool_name='Bash'))
            proposed = {'command':'*** Begin Patch\n*** Update File: body.md\n@@\n-Observed result.\n+Extra prose.\n*** End Patch'}
            self.assertEqual(event('PreToolUse',tool_name='apply_patch',tool_input=proposed)
                             ['hookSpecificOutput']['permissionDecision'],'deny')
            event('UserPromptSubmit',prompt='Change the report label.')
            self.assertEqual(event('PreToolUse',tool_name='apply_patch',tool_input=proposed)
                             ['hookSpecificOutput']['permissionDecision'],'deny')
            self.assertEqual(body.read_text(),'Observed result.')
            self.assertIsNone(event('PreToolUse',tool_name='apply_patch',tool_input={
                'command':proposed['command'].replace('body.md','source.py')}))

    def test_multiple_outputs_and_claude_revision_keep_their_ownership(self):
        reader = module('reader_delivery')
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,
            CODEX_READER_DELIVERY_STAGE_DIR=directory+'/staged',CODEX_RUNTIME_CONTRACT_STATE_DIR=directory+'/state'):
            root = Path(directory)
            a,b,revised = root/'a.md',root/'b.md',root/'revised.md'
            reader.stage('task','source',a,'A')
            reader.stage('task','source',b,'B')
            reader.consume('task','source')
            reader.stage('task','new-source',revised,'A revised',a)
            reader.consume('task','new-source')
            def reason(path):
                return reader.direct_edit_reason('task','new-source',{'tool_name':'apply_patch','cwd':directory,
                    'tool_input':{'command':'*** Update File: '+str(path)}})
            self.assertIsNone(reason(a))
            self.assertIsNotNone(reason(revised))
            self.assertIsNotNone(reason(b))
            _,saved = reader.locations('task')
            self.assertEqual(saved.stat().st_mode & 0o777,0o600)

    def test_completion_for_older_request_is_not_adopted_as_current_work(self):
        reader = module('reader_delivery')
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,
            CODEX_READER_DELIVERY_STAGE_DIR=directory+'/staged',CODEX_RUNTIME_CONTRACT_STATE_DIR=directory+'/state'):
            reader.stage('task','old-source',Path(directory)/'old.md','Old result')
            reader.consume('task','new-source')
            _,saved = reader.locations('task')
            self.assertEqual(json.loads(saved.read_text()),{})


if __name__ == '__main__':
    unittest.main()
