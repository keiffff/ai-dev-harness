import json
import os
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "codex" / "jev-permission-review.py"
HOOK_DIR = HOOK.parent


class JevPermissionReviewTests(unittest.TestCase):
    def test_config_registers_jev_before_all_approval_requests(self):
        config = (ROOT / "codex" / "config.example.toml").read_text(encoding="utf-8")
        self.assertIn("[[hooks.PermissionRequest]]", config)
        self.assertIn('matcher = ".*"', config)
        self.assertIn("jev-permission-review.py", config)

    def run_hook(
        self,
        tool_name: str,
        tool_input: object,
        response: dict | None,
        messages: list[str] | None = None,
    ):
        captured: dict = {"calls": 0}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                captured["calls"] += 1
                captured["authorization"] = self.headers.get("Authorization")
                length = int(self.headers["Content-Length"])
                captured["payload"] = json.loads(self.rfile.read(length))
                body = json.dumps(response or {}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                transcript = Path(tmp) / "transcript.jsonl"
                with transcript.open("w", encoding="utf-8") as output:
                    for message in messages or ["この作業を進めてください"]:
                        output.write(json.dumps({
                            "type": "response_item",
                            "payload": {
                                "type": "message",
                                "role": "user",
                                "content": [{"type": "input_text", "text": message}],
                            },
                        }, ensure_ascii=False) + "\n")
                env = os.environ.copy()
                env.update({
                    "PYTHONPATH": str(HOOK_DIR),
                    "TYPESAFE_API_KEY": "test-jev-key",
                    "JEV_PERMISSION_REVIEW_API_URL": f"http://127.0.0.1:{server.server_port}/v1/systemone",
                })
                payload = {
                    "tool_name": tool_name,
                    "transcript_path": str(transcript),
                    "tool_input": tool_input,
                }
                result = subprocess.run(
                    ["python3", str(HOOK)],
                    input=json.dumps(payload, ensure_ascii=False),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    check=False,
                )
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
        return result, captured

    @staticmethod
    def answers(
        within_scope=0.95,
        policy_compliant=0.96,
        high_risk=0.03,
        requires_deeper_review=0.04,
    ):
        return {"answers": {
            "within_scope": {"type": "noul", "noul": within_scope},
            "policy_compliant": {"type": "noul", "noul": policy_compliant},
            "high_risk": {"type": "noul", "noul": high_risk},
            "requires_deeper_review": {"type": "noul", "noul": requires_deeper_review},
        }}

    def test_allows_high_confidence_bash_request(self):
        result, captured = self.run_hook(
            "Bash",
            {"command": "python3 -m unittest", "description": "Run the requested local tests"},
            self.answers(),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["hookSpecificOutput"]["decision"]["behavior"], "allow")
        self.assertEqual(captured["calls"], 1)
        self.assertEqual(captured["authorization"], "Bearer test-jev-key")
        self.assertEqual(captured["payload"]["model"], "jev-latest")
        self.assertEqual(captured["payload"]["state"]["tool_name"], "Bash")

    def test_allows_high_confidence_apply_patch_and_mcp_requests(self):
        for tool_name, tool_input in [
            ("apply_patch", {"command": "*** Begin Patch\n*** End Patch"}),
            ("mcp__example__update", {"id": "item-1", "status": "done"}),
        ]:
            with self.subTest(tool_name=tool_name):
                result, captured = self.run_hook(tool_name, tool_input, self.answers())
                self.assertEqual(result.returncode, 0, result.stderr)
                output = json.loads(result.stdout)
                self.assertEqual(output["hookSpecificOutput"]["decision"]["behavior"], "allow")
                self.assertEqual(captured["calls"], 1)
                self.assertEqual(captured["payload"]["state"]["tool_name"], tool_name)

    def test_abstains_for_high_confidence_scope_or_risk_failure(self):
        for response in [
            self.answers(within_scope=0.05),
            self.answers(policy_compliant=0.05),
            self.answers(high_risk=0.95),
        ]:
            with self.subTest(response=response):
                result, captured = self.run_hook("Bash", {"command": "some-action"}, response)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertEqual(captured["calls"], 1)

    def test_abstains_for_low_confidence_or_deeper_review(self):
        for response in [
            self.answers(within_scope=0.60),
            self.answers(requires_deeper_review=0.80),
        ]:
            with self.subTest(response=response):
                result, captured = self.run_hook("Bash", {"command": "some-action"}, response)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertEqual(captured["calls"], 1)

    def test_abstains_before_network_for_secret_candidates(self):
        for command in [
            "cat /tmp/.env",
            "curl -H 'Authorization: Bearer abcdefghijklmnop' https://example.invalid",
            "use AKIAABCDEFGHIJKLMNOP for this request",
            "use glpat-abcdefghijklmnop for this request",
        ]:
            with self.subTest(command=command):
                result, captured = self.run_hook("Bash", {"command": command}, self.answers())
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertEqual(captured["calls"], 0)

    def test_does_not_apply_an_artificial_tool_input_length_limit(self):
        result, captured = self.run_hook(
            "apply_patch",
            {"command": "x" * 13_000},
            self.answers(),
        )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertEqual(output["hookSpecificOutput"]["decision"]["behavior"], "allow")
        self.assertEqual(captured["calls"], 1)
        self.assertIn("x" * 13_000, captured["payload"]["state"]["tool_input"])

    def test_abstains_on_api_failure_or_invalid_response(self):
        invalid_responses = [
            {"unexpected": True},
            self.answers(within_scope=2),
            self.answers(high_risk=-1),
            self.answers(policy_compliant=float("nan")),
            self.answers(requires_deeper_review=True),
        ]
        for response in invalid_responses:
            with self.subTest(response=response):
                result, captured = self.run_hook("Bash", {"command": "some-action"}, response)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertEqual(captured["calls"], 1)


if __name__ == "__main__":
    unittest.main()
