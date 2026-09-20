import json
import os
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "wrappers" / "bin" / "jev-evidence-check.example"


class JevEvidenceCheckTests(unittest.TestCase):
    def run_check(self, response, evidence="HTTP 429 stopped the request.", claim="The provider returned a quota response."):
        captured = {"calls": 0}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                captured["calls"] += 1
                captured["authorization"] = self.headers.get("Authorization")
                length = int(self.headers["Content-Length"])
                captured["payload"] = json.loads(self.rfile.read(length))
                body = json.dumps(response).encode()
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
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                evidence_file = root / "evidence.txt"
                claim_file = root / "claim.txt"
                evidence_file.write_text(evidence, encoding="utf-8")
                claim_file.write_text(claim, encoding="utf-8")
                env = os.environ.copy()
                env.update({
                    "TYPESAFE_API_KEY": "test-key",
                    "JEV_EVIDENCE_CHECK_API_URL": f"http://127.0.0.1:{server.server_port}/v1/systemone",
                })
                result = subprocess.run(
                    [
                        "python3",
                        str(WRAPPER),
                        "--evidence-file",
                        str(evidence_file),
                        "--claim-file",
                        str(claim_file),
                    ],
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
    def response(score):
        return {"answers": {"claim_supported": {"type": "noul", "noul": score}}}

    def test_supports_directly_observed_claim(self):
        result, captured = self.run_check(self.response(0.91))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"claim_supported": 0.91, "decision": "supported"})
        self.assertEqual(captured["authorization"], "Bearer test-key")
        state = captured["payload"]["state"]
        self.assertEqual(state["observed_evidence"], "HTTP 429 stopped the request.")
        self.assertEqual(state["proposed_claim"], "The provider returned a quota response.")
        instructions = captured["payload"]["questions"]["claim_supported"]["instructions"]
        self.assertIn("Mere consistency is insufficient", instructions)
        self.assertIn("prescribed remedy", instructions)

    def test_routes_unsupported_claim_to_review(self):
        result, _ = self.run_check(
            self.response(0.08),
            claim="The paid plan must be upgraded.",
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"claim_supported": 0.08, "decision": "unsupported"})

    def test_uses_observed_support_boundary(self):
        result, _ = self.run_check(self.response(0.70))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["decision"], "supported")

    def test_api_failure_is_visible_without_becoming_a_blocker(self):
        result, _ = self.run_check({"unexpected": True})
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"decision": "unavailable"})
        self.assertIn("Jev evidence check unavailable", result.stderr)

    def test_secret_candidate_stops_before_network(self):
        result, captured = self.run_check(
            self.response(0.99),
            evidence="Authorization: Bearer abcdefghijklmnop",
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(captured["calls"], 0)
        self.assertIn("nothing was sent", result.stderr)

    def test_does_not_truncate_evidence(self):
        evidence = "observation " * 2000
        result, captured = self.run_check(self.response(0.93), evidence=evidence)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(captured["payload"]["state"]["observed_evidence"], evidence)

    def test_missing_credential_launcher_is_non_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence_file = root / "evidence.txt"
            claim_file = root / "claim.txt"
            evidence_file.write_text("The command returned exit code 1.", encoding="utf-8")
            claim_file.write_text("The command failed.", encoding="utf-8")
            env = os.environ.copy()
            env.pop("TYPESAFE_API_KEY", None)
            env["KEYCHAIN_ENV_EXEC"] = str(root / "missing-launcher")
            result = subprocess.run(
                [
                    "python3",
                    str(WRAPPER),
                    "--evidence-file",
                    str(evidence_file),
                    "--claim-file",
                    str(claim_file),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=False,
            )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"decision": "unavailable"})


if __name__ == "__main__":
    unittest.main()
