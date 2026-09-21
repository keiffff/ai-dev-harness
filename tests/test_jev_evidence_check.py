import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "wrappers" / "bin" / "jev-evidence-check.example"
FAKE_EVALUATOR = """#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
Path(os.environ["JEV_TEST_CAPTURE"]).write_text(sys.stdin.read(), encoding="utf-8")
print(os.environ["JEV_TEST_RESPONSE"])
"""


class JevEvidenceCheckTests(unittest.TestCase):
    def test_delegates_jev_execution_to_jev_kit(self):
        source = WRAPPER.read_text(encoding="utf-8")
        self.assertIn("jev-kit-evidence-check", source)
        self.assertNotIn("urllib.request", source)

    def run_check(self, response, evidence="HTTP 429 stopped the request.", claim="The provider returned a quota response."):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence_file = root / "evidence.txt"
            claim_file = root / "claim.txt"
            evaluator = root / "fake-evaluator"
            capture_file = root / "capture.json"
            evidence_file.write_text(evidence, encoding="utf-8")
            claim_file.write_text(claim, encoding="utf-8")
            evaluator.write_text(FAKE_EVALUATOR, encoding="utf-8")
            evaluator.chmod(0o755)
            env = os.environ.copy()
            env.update({
                "TYPESAFE_API_KEY": "test-key",
                "JEV_KIT_EVIDENCE_CLI": str(evaluator),
                "JEV_TEST_CAPTURE": str(capture_file),
                "JEV_TEST_RESPONSE": json.dumps(response),
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
            captured = {
                "calls": int(capture_file.exists()),
                "payload": json.loads(capture_file.read_text(encoding="utf-8")) if capture_file.exists() else None,
            }
        return result, captured

    @staticmethod
    def response(score):
        return {"schemaVersion": 1, "status": "evaluated", "scores": {"claim_supported": score}}

    def test_supports_directly_observed_claim(self):
        result, captured = self.run_check(self.response(0.91))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"claim_supported": 0.91, "decision": "supported"})
        payload = captured["payload"]
        self.assertEqual(payload["evidence"], "HTTP 429 stopped the request.")
        self.assertEqual(payload["claim"], "The provider returned a quota response.")
        instructions = payload["contract"]["axes"][0]["instructions"]
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
        result, _ = self.run_check({"schemaVersion": 1, "status": "unavailable", "errorKind": "api"})
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
        self.assertEqual(captured["payload"]["evidence"], evidence)

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
