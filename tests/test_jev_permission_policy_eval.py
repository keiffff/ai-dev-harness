import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = ROOT / "evals" / "permission-review"
RUNNER = EVAL_ROOT / "evaluate.mjs"


class JevPermissionPolicyEvaluationTests(unittest.TestCase):
    def test_runner_uses_jev_kit_policy_comparison(self):
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("evaluateAgentReviewFixtures", source)
        self.assertIn("compareDecisionPolicies", source)
        self.assertIn('id: "current"', source)
        self.assertNotIn("selectedCandidate", source)

    def test_calibration_and_holdout_are_separate_labeled_sets(self):
        calibration = json.loads((EVAL_ROOT / "calibration.json").read_text(encoding="utf-8"))
        holdout = json.loads((EVAL_ROOT / "holdout.json").read_text(encoding="utf-8"))
        calibration_ids = {fixture["id"] for fixture in calibration}
        holdout_ids = {fixture["id"] for fixture in holdout}
        self.assertEqual(len(calibration_ids), len(calibration))
        self.assertEqual(len(holdout_ids), len(holdout))
        self.assertTrue(calibration_ids.isdisjoint(holdout_ids))
        self.assertEqual({fixture["expected"] for fixture in calibration}, {"allow", "defer"})
        self.assertEqual({fixture["expected"] for fixture in holdout}, {"allow", "defer"})

    def test_help_does_not_require_provider_or_api_key(self):
        completed = subprocess.run(
            ["node", str(RUNNER), "--help"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("--candidate", completed.stdout)
        self.assertIn("JEV_KIT_ROOT", completed.stdout)


if __name__ == "__main__":
    unittest.main()
