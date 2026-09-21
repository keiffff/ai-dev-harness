import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "wrappers" / "bin" / "jev-artifact-review.example"
FAKE_EVALUATOR = """#!/usr/bin/env python3
import os
import sys
from pathlib import Path
Path(os.environ["JEV_TEST_CAPTURE"]).write_text(sys.stdin.read(), encoding="utf-8")
print(os.environ["JEV_TEST_RESPONSE"])
"""


class JevArtifactReviewTests(unittest.TestCase):
    def test_delegates_jev_execution_to_jev_kit(self):
        source = WRAPPER.read_text(encoding="utf-8")
        self.assertIn("jev-kit-semantic-diff", source)
        self.assertNotIn("urllib.request", source)

    def run_review(
        self,
        response,
        requirements="Keep the theme.",
        candidate="Same theme.",
        baseline=None,
        route_checks=False,
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            requirements_file = root / "requirements.txt"
            candidate_file = root / "candidate.html"
            evaluator = root / "fake-evaluator"
            capture_file = root / "capture.json"
            requirements_file.write_text(requirements, encoding="utf-8")
            candidate_file.write_text(candidate, encoding="utf-8")
            evaluator.write_text(FAKE_EVALUATOR, encoding="utf-8")
            evaluator.chmod(0o755)
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
            if route_checks:
                command.append("--route-checks")
            env = os.environ.copy()
            env.update({
                "TYPESAFE_API_KEY": "test-key",
                "JEV_KIT_SEMANTIC_DIFF_CLI": str(evaluator),
                "JEV_TEST_CAPTURE": str(capture_file),
                "JEV_TEST_RESPONSE": json.dumps(response),
            })
            result = subprocess.run(
                command,
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
        return {"schemaVersion": 1, "status": "evaluated", "scores": {"material_violation": score}}

    @staticmethod
    def routed_response(material, meaning, layout, interaction, whole):
        return {"schemaVersion": 1, "status": "evaluated", "scores": {
            "material_violation": material,
            "meaning_changed": meaning,
            "layout_changed": layout,
            "interaction_changed": interaction,
            "whole_artifact_changed": whole,
        }}

    def test_passes_candidate_below_observed_violation_boundary(self):
        result, captured = self.run_review(
            self.response(0.22),
            requirements="Keep the theme and improve Japanese wording.",
            candidate="The wording changed and the theme remained intact.",
            baseline="Original wording with the same theme.",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"decision": "pass", "material_violation": 0.22})
        payload = captured["payload"]
        self.assertEqual(payload["before"], "Original wording with the same theme.")
        self.assertIn("candidate", payload["after"])
        self.assertIn("requirements", payload["after"])

    def test_routes_high_confidence_violation_to_review(self):
        result, captured = self.run_review(
            self.response(0.97),
            requirements="Polish Japanese only; keep the theme.",
            candidate="Changed the wording, colors and layout.",
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"decision": "review", "material_violation": 0.97})
        instructions = captured["payload"]["contract"]["dimensions"][0]["instructions"]
        self.assertIn("misleading parallel presentation", instructions)
        self.assertIn("excuse copy", instructions)

    def test_api_failure_is_visible_but_does_not_block_candidate(self):
        result, _ = self.run_review({"schemaVersion": 1, "status": "unavailable", "errorKind": "api"})
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"decision": "unavailable"})
        self.assertIn("Jev artifact review unavailable", result.stderr)

    def test_routes_local_copy_change_without_full_artifact_checks(self):
        result, captured = self.run_review(
            self.routed_response(0.05, 0.06, 0.08, 0.02, 0.03),
            requirements="Change one heading only.",
            baseline="<html><h1>Old heading</h1></html>",
            candidate="<html><h1>New heading</h1></html>",
            route_checks=True,
        )
        output = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output["decision"], "pass")
        self.assertFalse(any(output["required_checks"].values()))
        dimension_ids = [item["id"] for item in captured["payload"]["contract"]["dimensions"]]
        self.assertIn("interaction_changed", dimension_ids)

    def test_inherits_runtime_checks_and_jev_adds_visual_scope(self):
        baseline = """<!doctype html><html><iframe src='demo.html'></iframe><script>start()</script></html>"""
        candidate = """<!doctype html><html><iframe src='demo.html'></iframe><script>changed()</script></html>"""
        result, _ = self.run_review(
            self.routed_response(0.91, 0.40, 0.88, 0.96, 0.22),
            requirements="Preserve the embedded demo in file and HTTP use.",
            baseline=baseline,
            candidate=candidate,
            route_checks=True,
        )
        output = json.loads(result.stdout)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(output["inherited_runtime_features"], ["iframe", "script"])
        self.assertTrue(output["runtime_contract_changed"])
        self.assertTrue(output["required_checks"]["changed_region_visual"])
        self.assertTrue(output["required_checks"]["browser_smoke"])
        self.assertTrue(output["required_checks"]["interaction_journey"])
        self.assertFalse(output["required_checks"]["full_page_visual"])

    def test_unavailable_route_keeps_inherited_runtime_checks(self):
        result, _ = self.run_review(
            {"schemaVersion": 1, "status": "unavailable", "errorKind": "api"},
            baseline="<html><iframe src='demo.html'></iframe></html>",
            candidate="<html><iframe src='demo.html'></iframe></html>",
            route_checks=True,
        )
        output = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(output["decision"], "unavailable")
        self.assertTrue(output["required_checks"]["browser_smoke"])
        self.assertFalse(output["required_checks"]["interaction_journey"])

    def test_unavailable_route_detects_runtime_contract_change_without_jev(self):
        result, _ = self.run_review(
            {"schemaVersion": 1, "status": "unavailable", "errorKind": "api"},
            baseline="<html><iframe src='demo.html'></iframe><script>start()</script></html>",
            candidate="<html><iframe src='demo.html'></iframe></html>",
            route_checks=True,
        )
        output = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(output["decision"], "unavailable")
        self.assertTrue(output["runtime_contract_changed"])
        self.assertTrue(output["required_checks"]["interaction_journey"])

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
