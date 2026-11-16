import importlib.util
import json
import os
from pathlib import Path
import runpy
import sqlite3
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'hooks/codex/source_ledger.py'


class SkillSourceTransportTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        spec=importlib.util.spec_from_file_location('transport_ledger',SOURCE)
        self.ledger=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.ledger)
        self.request='訂正後の説明を使って、読み手向けにまとめてください。\n'
        self.prior='最初の説明を訂正します。観測された状態は後者でした。'
        history=self.root/'history.sqlite'
        with sqlite3.connect(history) as db:
            db.execute('CREATE TABLE thread_items(thread_id TEXT,created_at_ms INTEGER,item_type TEXT,item_json TEXT)')
            rows=[('userMessage',{'content':[{'type':'text','text':'二つの状態を調べてください。'}]}),
                  ('agentMessage',{'phase':'final_answer','text':self.prior}),
                  ('userMessage',{'content':[{'type':'text','text':self.request}]}),
                  ('agentMessage',{'phase':'final_answer','text':'AFTER_CUTOFF'})]
            db.executemany('INSERT INTO thread_items VALUES (?,?,?,?)',
                [('task',i,kind,json.dumps(item,ensure_ascii=False)) for i,(kind,item) in enumerate(rows)])
        self.addCleanup(patch.stopall)
        patch.dict(os.environ,CODEX_THREAD_ID='task',CODEX_SOURCE_LEDGER_DIR=str(self.root/'ledger'),
                   CODEX_THREAD_HISTORY_DB=str(history),CODEX_SOURCE_LEDGER_SCRIPT=str(SOURCE),
                   CODEX_READER_DELIVERY_STAGE_DIR=str(self.root/'delivery')).start()
        for message in ['二つの状態を調べてください。',self.request]:
            self.ledger.append_prompt('task',message)
        self.source=self.root/'source.txt'
        self.source.write_bytes(b'original observation\r\n')

    def check_context(self,packet):
        self.assertEqual(packet['current_request'],self.request)
        self.assertEqual(packet['saved_conversation']['turns'][-1]['text'],self.prior)
        self.assertNotIn('AFTER_CUTOFF',json.dumps(packet))

    def test_html_and_gemini_take_originals_without_a_caller_written_packet(self):
        html=runpy.run_path(str(ROOT/'wrappers/bin/claude-html-report.example'))
        packet=json.loads(html['build_packet'](None,[str(self.source)]))
        self.assertEqual(packet['request']['content'],self.request)
        self.assertEqual(packet['saved_conversation']['turns'][-1]['text'],self.prior)
        self.assertEqual(packet['evidence'][0]['content'].encode(),self.source.read_bytes())
        gemini=runpy.run_path(str(ROOT/'wrappers/bin/gemini-japanese-polish.example'))
        packet=json.loads(gemini['composition_sources'](SimpleNamespace(request_file=None,source_file=[str(self.source)])))
        self.check_context(packet)
        self.assertEqual(packet['source_material'][0]['content'].encode(),self.source.read_bytes())

    def test_review_uses_the_saved_request_when_bundle_omits_a_transcribed_file(self):
        spec=importlib.util.spec_from_file_location('review_transport',ROOT/'codex/skills/codex-code-review/scripts/review_record.py')
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result=module.original_inputs('')
        self.check_context(result)
        self.assertEqual(module.original_inputs('Outside-app original.')['current_request'],'Outside-app original.')

    def test_normal_html_cli_needs_no_request_transcription(self):
        capture=self.root/'html-input.txt'
        fake=self.root/'claude'
        artifact=self.root/'report.html'
        body='<!doctype html><html><body><p data-fact="F1" data-weight="load-bearing">説明</p><!-- REPORT-META facts: F1: U1 structure: one information_weighting: main: F1 inferences: [] --></body></html>'
        fake.write_text(f'#!{sys.executable}\nimport sys\nfrom pathlib import Path\n'
            'if "--help" in sys.argv: print("--safe-mode"); raise SystemExit(0)\n'
            f'Path({str(capture)!r}).write_text(sys.stdin.read())\nprint({body!r})\n')
        fake.chmod(0o755)
        result=subprocess.run([sys.executable,str(ROOT/'wrappers/bin/claude-html-report.example'),
            '--evidence-file',str(self.source),'--output-file',str(artifact)],capture_output=True,text=True,
            env={**os.environ,'CLAUDE_HTML_REPORT_CLI':str(fake),'CLAUDE_CODE_OAUTH_TOKEN':'synthetic-token'})
        self.assertEqual(result.returncode,0,result.stderr)
        packet=json.loads(capture.read_text().split('--- PACKET ---\n',1)[1])
        self.assertEqual(packet['request']['content'],self.request)
        self.assertEqual(packet['saved_conversation']['turns'][-1]['text'],self.prior)
        self.assertEqual(artifact.read_text(),body+'\n')

    def test_normal_gemini_cli_prints_the_body_in_one_call_without_a_packet_file(self):
        capture=self.root/'gemini-input.json'
        fake=self.root/'agy'
        body='読み手への説明です。\n'
        response={'event':'result','result':{'status':'SUCCESS','structured_output':{
            'revised_text':body,'changes':[],'warnings':[]}}}
        fake.write_text(f'#!{sys.executable}\nimport sys,json\nfrom pathlib import Path\n'
            f'p=Path({str(capture)!r})\nrows=json.loads(p.read_text()) if p.exists() else []\n'
            'rows.append(sys.stdin.read())\np.write_text(json.dumps(rows))\n'
            f'print({json.dumps(response,ensure_ascii=False)!r})\n')
        fake.chmod(0o755)
        result=subprocess.run([sys.executable,str(ROOT/'wrappers/bin/gemini-japanese-polish.example'),
            '--source-file',str(self.source),'--medium','slack','--print-body'],capture_output=True,text=True,
            env={**os.environ,'GEMINI_API_KEY':'synthetic-key','GEMINI_JAPANESE_POLISH_ANTIGRAVITY_CLI':str(fake),
                 'TMPDIR':str(self.root)})
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout,body)
        calls=json.loads(capture.read_text())
        self.assertEqual(len(calls),1)
        self.assertIn(self.prior,calls[0])


if __name__=='__main__':
    unittest.main()
