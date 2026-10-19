"""Synthetic regression cases for report composition vs language review ownership."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GEMINI = ROOT / "wrappers/bin/gemini-japanese-polish.example"
CLAUDE = ROOT / "wrappers/bin/claude-html-report.example"
HTML = '<!doctype html><html><style>body{color:#123456}</style><body><p data-fact="F1" data-weight="load-bearing">結果を確認をします。</p><!-- REPORT-META facts: F1: U1 structure: one information_weighting: main: F1 inferences: [] --></body></html>\r\n'


class LanguageReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.artifact = self.root / "report.html"
        self.artifact.write_bytes(HTML.encode())
        self.request = self.root / "request.txt"
        self.request.write_text("比較資料をHTMLにしてください。日本語も校正してください。")
        self.review = self.root / "review.json"

    def run_gemini(self, output, mode="review"):
        fake = self.root / "agy"
        fake.write_text(f'''#!{sys.executable}
import json, os, sys
from pathlib import Path
capture=Path(os.environ['CAPTURE'])
calls=json.loads(capture.read_text()) if capture.exists() else []
calls.append({{'args':sys.argv,'input':sys.stdin.read()}})
capture.write_text(json.dumps(calls))
print(json.dumps({{'event':'result','result':{{'status':'SUCCESS','structured_output':{output!r}}}}},ensure_ascii=False))
''')
        fake.chmod(0o755)
        result = subprocess.run(
            [sys.executable, str(GEMINI), "--mode", mode, "--medium", "html",
             "--input-file", str(self.artifact), "--output-file", str(self.review)],
            env={**os.environ, "GEMINI_API_KEY": "synthetic-key",
                 "GEMINI_JAPANESE_POLISH_ANTIGRAVITY_CLI": str(fake),
                 "CAPTURE": str(self.root / "capture.json")},
            text=True, capture_output=True,
        )
        return result

    def valid_output(self):
        return {"findings": [{"quote": "結果を確認をします。", "issue": "助詞が重複している。"}]}

    def test_review_returns_only_findings_and_binds_exact_html_bytes(self):
        result = self.run_gemini(self.valid_output())
        self.assertEqual(result.returncode, 0, result.stderr)
        review = json.loads(self.review.read_text())
        self.assertEqual(review["kind"], "japanese-language-review")
        self.assertEqual(review["source_sha256"], hashlib.sha256(self.artifact.read_bytes()).hexdigest())
        self.assertEqual(review["findings"], self.valid_output()["findings"])
        self.assertNotIn("revised_text", review)
        capture = json.loads((self.root / "capture.json").read_text())[0]
        schema = json.loads(capture["args"][capture["args"].index("--json-schema") + 1])
        self.assertEqual(set(schema["properties"]), {"findings"})
        self.assertIn(HTML, json.loads(capture["input"])["message"]["content"])

    def test_rewrite_or_nonexistent_quote_is_rejected_without_output_or_retry(self):
        for output in ({"revised_text": "全面改稿", "changes": [], "warnings": []},
                       {"findings": [{"quote": "not in report", "issue": "説明不足"}]}):
            with self.subTest(output=output):
                result = self.run_gemini(output)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("unrecognized arguments", result.stderr)
                self.assertFalse(self.review.exists())
                self.assertEqual(self.artifact.read_bytes(), HTML.encode())
        self.assertEqual(len(json.loads((self.root / "capture.json").read_text())), 2)

    def test_empty_findings_is_valid(self):
        result = self.run_gemini({"findings": []})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.review.read_text())["findings"], [])

    def test_existing_composition_provenance_is_not_overwritten(self):
        provenance = Path(str(self.review) + ".provenance.json")
        provenance.write_text("existing provenance")
        result = self.run_gemini({"revised_text": HTML + "<!-- GEMINI_COMPLETE_HTML -->",
                                  "changes": [], "warnings": []}, mode="compose")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("provenance path", result.stderr)
        self.assertEqual(provenance.read_text(), "existing provenance")
        self.assertFalse((self.root / "capture.json").exists())
        self.assertFalse(self.review.exists())

    def test_prior_analysis_is_separate_and_not_banned_by_markdown_extension(self):
        analysis = self.root / "comparison.md"
        analysis.write_text("# 比較\n方式Xは月額10、方式Yは月額20。\n")
        wrapper = runpy.run_path(str(CLAUDE))
        packet = json.loads(wrapper["build_packet"](self.request, [], [str(analysis)]))
        self.assertEqual(packet["evidence"], [])
        self.assertEqual(packet["analysis"][0]["content"], analysis.read_text())
        self.assertEqual(packet["analysis"][0]["id"], "A1")

    def test_old_composition_as_evidence_route_fails_before_claude(self):
        result = self.run_gemini({"revised_text": HTML + "<!-- GEMINI_COMPLETE_HTML -->",
                                  "changes": [], "warnings": []}, mode="compose")
        self.assertEqual(result.returncode, 0, result.stderr)
        output = self.root / "new.html"
        result = subprocess.run(
            [sys.executable, str(CLAUDE), "--request-file", str(self.request),
             "--evidence-file", str(self.review), "--output-file", str(output)],
            env={**os.environ, "CLAUDE_HTML_REPORT_CLI": "/nonexistent/claude"},
            text=True, capture_output=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("composition", result.stderr)
        self.assertNotIn("not executable", result.stderr)
        self.assertFalse(output.exists())

    def test_review_cannot_be_misrouted_as_primary_evidence(self):
        self.assertEqual(self.run_gemini(self.valid_output()).returncode, 0)
        wrapper = runpy.run_path(str(CLAUDE))
        with self.assertRaises(SystemExit):
            wrapper["build_packet"](self.request, [str(self.review)])

    def test_review_is_attached_only_to_matching_revision(self):
        self.assertEqual(self.run_gemini(self.valid_output()).returncode, 0)
        wrapper = runpy.run_path(str(CLAUDE))
        record = wrapper["language_review_record"](str(self.review), self.artifact.read_bytes())
        self.assertEqual(record["content"]["findings"], self.valid_output()["findings"])
        with self.assertRaises(SystemExit):
            wrapper["language_review_record"](str(self.review), b"changed HTML")

    def test_malformed_or_unanchored_review_is_rejected_by_recipient(self):
        self.assertEqual(self.run_gemini(self.valid_output()).returncode, 0)
        wrapper = runpy.run_path(str(CLAUDE))
        data = json.loads(self.review.read_text())
        data["findings"][0]["quote"] = "missing"
        self.review.write_text(json.dumps(data))
        with self.assertRaises(SystemExit):
            wrapper["language_review_record"](str(self.review), self.artifact.read_bytes())

    def test_matching_review_reaches_claude_as_findings_not_evidence(self):
        self.assertEqual(self.run_gemini(self.valid_output()).returncode, 0)
        analysis = self.root / "comparison.md"
        analysis.write_text("以前の比較資料。構成案は検討中。")
        capture = self.root / "claude-input.json"
        fake = self.root / "claude"
        fake.write_text(f'''#!{sys.executable}
import json, os, sys
from pathlib import Path
if '--help' in sys.argv:
    print('--safe-mode'); raise SystemExit(0)
packet=json.loads(sys.stdin.read().split('--- PACKET ---\\n',1)[1])
Path(os.environ['CAPTURE']).write_text(json.dumps(packet))
artifact=Path(packet['artifact']['path'])
artifact.write_bytes(artifact.read_bytes().replace('結果を確認をします。'.encode(),'結果を確認します。'.encode()))
print(json.dumps({{'type':'result','is_error':False,'result':'言語上の誤りのみ修正。'}}))
''')
        fake.chmod(0o755)
        result = subprocess.run(
            [sys.executable, str(CLAUDE), "--request-file", str(self.request),
             "--language-review-file", str(self.review), "--analysis-file", str(analysis),
             "--edit-file", str(self.artifact)],
            env={**os.environ, "CLAUDE_CODE_OAUTH_TOKEN": "synthetic-token",
                 "CLAUDE_HTML_REPORT_CLI": str(fake), "CAPTURE": str(capture)},
            text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        packet = json.loads(capture.read_text())
        self.assertEqual(packet["evidence"], [])
        self.assertEqual(packet["analysis"][0]["content"], analysis.read_text())
        self.assertEqual(packet["language_review"]["content"]["findings"], self.valid_output()["findings"])
        self.assertEqual(self.artifact.read_bytes(), HTML.replace("結果を確認をします。", "結果を確認します。").encode())

    def test_review_for_new_generation_fails_before_claude(self):
        self.assertEqual(self.run_gemini(self.valid_output()).returncode, 0)
        result = subprocess.run(
            [sys.executable, str(CLAUDE), "--request-file", str(self.request),
             "--language-review-file", str(self.review), "--output-file", str(self.root / "new.html")],
            env={**os.environ, "CLAUDE_HTML_REPORT_CLI": "/nonexistent/claude"},
            text=True, capture_output=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("after Claude has composed", result.stderr)
        self.assertFalse((self.root / "new.html").exists())


if __name__ == "__main__":
    unittest.main()
