import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "wrappers/bin/claude-html-report.example"


class HtmlReportEvidenceTests(unittest.TestCase):
    def test_credential_launcher_uses_current_home_and_preserves_override(self):
        wrapper = runpy.run_path(str(WRAPPER))
        home = Path("/synthetic/user home")
        for override in (None, "/synthetic/custom/credential-launcher"):
            environment = {} if override is None else {"KEYCHAIN_ENV_EXEC": override}
            with self.subTest(override=override), patch.dict(os.environ, environment, clear=True), \
                 patch.object(Path, "home", return_value=home), \
                 patch("os.execv", side_effect=RuntimeError("captured launch")) as launch:
                with self.assertRaisesRegex(RuntimeError, "captured launch"):
                    wrapper["load_oauth_token"]()
                expected = override or str(home / ".local" / "bin" / "keychain-env-exec")
                self.assertEqual(launch.call_args.args[0], expected)
                self.assertEqual(launch.call_args.args[1][:4],
                                 [expected, "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN", "--"])

    def test_original_request_and_complete_sources_reach_cli_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = root / "request.txt"
            reference = root / "reference.html"
            styles = root / "reference.css"
            request_bytes = "この資料を参考に説明してください。\r\n勝手に構成を決めないで。\r\n".encode()
            html_bytes = '<!doctype html>\r\n<html lang="ja"><style>h1{font-size:38px}</style><body>原資料 </source></body></html>\r\n'.encode()
            css_bytes = b":root { --ink: #112233; }\r\n.side { height: 100vh; }\r\n"
            request.write_bytes(request_bytes)
            reference.write_bytes(html_bytes)
            styles.write_bytes(css_bytes)
            capture = root / "stdin.txt"
            fake = root / "claude"
            fake.write_text(
                f"#!{sys.executable}\n"
                "import os, sys\n"
                "from pathlib import Path\n"
                "if '--help' in sys.argv:\n"
                " print('--safe-mode'); raise SystemExit(0)\n"
                "Path(os.environ['CAPTURE_FILE']).write_bytes(sys.stdin.buffer.read())\n"
                "print('<!doctype html><html><body data-fact=\"F1\" data-weight=\"load-bearing\">Example<!-- REPORT-META facts: F1: U1 structure: one information_weighting: main: F1 inferences: [] --></body></html>')\n"
            )
            fake.chmod(0o755)
            output = root / "result.html"
            result = subprocess.run(
                [sys.executable, str(WRAPPER), "--request-file", str(request),
                 "--evidence-file", str(reference), "--evidence-file", str(styles),
                 "--output-file", str(output)],
                env={**os.environ, "CLAUDE_HTML_REPORT_CLI": str(fake),
                     "CLAUDE_CODE_OAUTH_TOKEN": "test-token", "CAPTURE_FILE": str(capture)},
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.is_file())
            payload = json.loads(capture.read_text().split("--- PACKET ---\n", 1)[1])
            self.assertEqual(set(payload), {"request", "evidence"})
            for record, original in zip(
                [payload["request"], *payload["evidence"]],
                [request_bytes, html_bytes, css_bytes],
                strict=True,
            ):
                self.assertEqual(record["content"].encode(), original)
                self.assertEqual(record["sha256"], hashlib.sha256(original).hexdigest())
                self.assertEqual(set(record), {"id", "path", "sha256", "content"})
            self.assertEqual([r["id"] for r in payload["evidence"]], ["E1", "E2"])

    def test_unreadable_evidence_fails_before_model_call_or_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = root / "request.txt"
            request.write_text("Make an HTML report.")
            binary = root / "image.png"
            binary.write_bytes(b"\x89PNG\xff")
            for evidence, message in [
                (root / "missing.html", "existing regular file"),
                (binary, "UTF-8"),
            ]:
                result = subprocess.run(
                    [sys.executable, str(WRAPPER), "--request-file", str(request),
                     "--evidence-file", str(evidence), "--output-file", str(root / "result.html")],
                    env={**os.environ, "CLAUDE_HTML_REPORT_CLI": "/nonexistent/claude"},
                    text=True, capture_output=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertNotIn("not executable", result.stderr)
                self.assertFalse((root / "result.html").exists())

    def test_request_only_and_existing_flag_spelling_remain_supported(self):
        wrapper = runpy.run_path(str(WRAPPER))
        args = wrapper["parse_args"](["--prompt-file", "request.txt", "--output-file", "new.html"])
        self.assertEqual(args.prompt_file, "request.txt")
        self.assertEqual(args.evidence_file, [])
        with tempfile.TemporaryDirectory() as directory:
            request = Path(directory) / "request.txt"
            request.write_text("Write a report from this request alone.")
            packet = json.loads(wrapper["build_packet"](request, []))
            self.assertEqual(packet["request"]["content"], request.read_text())
            self.assertEqual(packet["evidence"], [])


if __name__ == "__main__":
    unittest.main()
