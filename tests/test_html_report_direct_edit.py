import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "wrappers/bin/claude-html-report.example"
HTML = '<!doctype html><html><style>body{color:#123456}</style><body><p data-fact="F1" data-weight="load-bearing">10件</p><!-- REPORT-META facts: F1: E1 structure: one information_weighting: main: F1 inferences: [] --></body></html>'


class DirectEditTests(unittest.TestCase):
    def run_edit(self, mode="edit"):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        artifact = root / "report.html"
        artifact.write_text(HTML)
        sibling = root / "untouched.html"
        sibling.write_text("unchanged")
        request = root / "request.txt"
        request.write_bytes("件数を原資料に合わせてください。\r\n".encode())
        evidence = root / "source.txt"
        evidence.write_bytes(b"count=12\r\n")
        fake = root / "claude"
        fake.write_text(f'''#!{sys.executable}
import json, os, sys
from pathlib import Path
if '--help' in sys.argv:
    print('--safe-mode'); raise SystemExit(0)
contract,raw_packet=sys.stdin.read().split('--- PACKET ---\\n',1)
packet=json.loads(raw_packet)
artifact=Path(packet['artifact']['path'])
Path(os.environ['CAPTURE']).write_text(json.dumps({{'argv':sys.argv[1:],'cwd':os.getcwd(),'cwd_files':os.listdir('.'),'packet':packet,'contract':contract}}))
mode=os.environ['FAKE_MODE']
if mode!='stdout_only':
    artifact.write_text('broken' if mode=='invalid' else artifact.read_text().replace('10件','12件'))
print(json.dumps({{'type':'assistant','message':{{'content':[{{'type':'tool_use','name':'Edit','input':{{'file_path':str(artifact),'old_string':'10件','new_string':'12件'}}}}]}}}}))
print(json.dumps({{'type':'result','is_error':False,'result':'not an HTML response'}}))
raise SystemExit(1 if mode=='fail' else 0)
''')
        fake.chmod(0o755)
        capture = root / "capture.json"
        trace = root / "trace.json"
        result = subprocess.run(
            [sys.executable, str(WRAPPER), "--request-file", str(request),
             "--evidence-file", str(evidence), "--edit-file", str(artifact),
             "--trace-file", str(trace)],
            env={**os.environ, "CLAUDE_CODE_OAUTH_TOKEN": "synthetic-token",
                 "CLAUDE_HTML_REPORT_CLI": str(fake), "CAPTURE": str(capture),
                 "FAKE_MODE": mode}, text=True, capture_output=True,
        )
        return result, artifact, sibling, capture, trace

    def test_cli_edits_file_instead_of_stdout_replacement(self):
        result, artifact, sibling, capture, trace = self.run_edit()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(artifact.read_text(), HTML.replace("10件", "12件"))
        self.assertEqual(sibling.read_text(), "unchanged")
        data = json.loads(capture.read_text())
        argv = data["argv"]
        self.assertEqual(argv[argv.index("--tools") + 1], "Read,Edit")
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "dontAsk")
        self.assertIn(f"Edit(/{artifact.resolve()})", argv)
        self.assertIn(f"Read(/{artifact.resolve()})", argv)
        self.assertNotIn("--max-turns", argv)
        self.assertNotIn("--dangerously-skip-permissions", argv)
        self.assertEqual(data["cwd_files"], [])
        self.assertNotEqual(Path(data["cwd"]), artifact.parent)
        self.assertEqual(data["packet"]["request"]["content"], "件数を原資料に合わせてください。\r\n")
        self.assertEqual(data["packet"]["evidence"][0]["content"], "count=12\r\n")
        self.assertNotIn("content", data["packet"]["artifact"])
        self.assertIn("Do not normalize, expand or migrate existing metadata", data["contract"])
        self.assertNotIn("Return only one complete HTML document", data["contract"])
        self.assertNotIn("Immediately before </body>", data["contract"])
        audit = json.loads(trace.read_text())
        self.assertTrue(audit["changed"])
        self.assertEqual(audit["tool_calls"][0]["tool"], "Edit")
        self.assertNotIn("not an HTML response", artifact.read_text())

    def test_stdout_is_never_adopted_as_the_artifact(self):
        result, artifact, _, _, trace = self.run_edit("stdout_only")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(artifact.read_text(), HTML)
        self.assertFalse(json.loads(trace.read_text())["changed"])

    def test_invalid_edited_document_is_rejected_and_preserved(self):
        result, artifact, _, _, trace = self.run_edit("invalid")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(artifact.read_text(), "broken")
        self.assertIn("did not begin", result.stderr)
        self.assertEqual(json.loads(trace.read_text())["status"], "invalid")

    def test_failed_cli_does_not_rollback_or_regenerate(self):
        result, artifact, _, _, _ = self.run_edit("fail")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(artifact.read_text(), HTML.replace("10件", "12件"))
        self.assertIn("partially edited", result.stderr)


if __name__ == "__main__":
    unittest.main()
