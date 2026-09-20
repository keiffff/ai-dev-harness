import json
import os
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "wrappers" / "bin" / "jev-artifact-review.example"


class JevArtifactReviewTests(unittest.TestCase):
    def run_review(self, response, requirements="Keep the theme.", candidate="Same theme.", baseline=None):
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
                requirements_file = root / "requirements.txt"
                candidate_file = root / "candidate.html"
                requirements_file.write_text(requirements, encoding="utf-8")
                candidate_file.write_text(candidate, encoding="utf-8")
                command = [
                    "python3",
                    str(WRAPPER),
                    "--requirements-file",
                    str(requirements_file),
                    "--candidate-file",
                    str(candidate_file),
                ]
                if baseline is not None:
                    baseline_file = root / "baseline.html"
                    baseline_file.write_text(baseline, encoding="utf-8")
                    command.extend(["--baseline-file", str(baseline_file)])
                env = os.environ.copy()
                env.update({
                    "TYPESAFE_API_KEY": "test-key",
                    "JEV_ARTIFACT_REVIEW_API_URL": f"http://127.0.0.1:{server.server_port}/v1/systemone",
                })
                result = subprocess.run(
                    command,
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
        return {"answers": {"material_violation": {"type": "noul", "noul": score}}}

    def test_passes_candidate_below_observed_violation_boundary(self):
        result, captured = self.run_review(
            self.response(0.22),
            requirements="Keep the theme and improve Japanese wording.",
            candidate="The wording changed and the theme remained intact.",
            baseline="Original wording with the same theme.",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"decision": "pass", "material_violation": 0.22})
        self.assertEqual(captured["authorization"], "Bearer test-key")
        state = captured["payload"]["state"]
        self.assertEqual(state["baseline"], "Original wording with the same theme.")
        self.assertIn("candidate", state)
        self.assertIn("requirements", state)

    def test_routes_high_confidence_violation_to_review(self):
        result, captured = self.run_review(
            self.response(0.97),
            requirements="Polish Japanese only; keep the theme.",
            candidate="Changed the wording, colors and layout.",
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"decision": "review", "material_violation": 0.97})
        instructions = captured["payload"]["questions"]["material_violation"]["instructions"]
        self.assertIn("misleading parallel presentation", instructions)
        self.assertIn("excuse copy", instructions)

    def test_api_failure_is_visible_but_does_not_block_candidate(self):
        result, _ = self.run_review({"unexpected": True})
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"decision": "unavailable"})
        self.assertIn("Jev artifact review unavailable", result.stderr)

    def test_secret_candidate_stops_before_network(self):
        result, captured = self.run_review(
            self.response(0.01),
            candidate="Authorization: Bearer abcdefghijklmnop",
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(captured["calls"], 0)
        self.assertIn("nothing was sent", result.stderr)

    def test_missing_credential_launcher_is_non_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            requirements_file = root / "requirements.txt"
            candidate_file = root / "candidate.txt"
            requirements_file.write_text("Keep the theme.", encoding="utf-8")
            candidate_file.write_text("Same theme.", encoding="utf-8")
            env = os.environ.copy()
            env.pop("TYPESAFE_API_KEY", None)
            env["KEYCHAIN_ENV_EXEC"] = str(root / "missing-launcher")
            result = subprocess.run(
                [
                    "python3",
                    str(WRAPPER),
                    "--requirements-file",
                    str(requirements_file),
                    "--candidate-file",
                    str(candidate_file),
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
