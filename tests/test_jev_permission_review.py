import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "hooks" / "codex" / "jev-permission-review-policy.json"
LEGACY_HOOK = ROOT / "hooks" / "codex" / "jev-permission-review.py"


class JevPermissionReviewWiringTests(unittest.TestCase):
    def test_config_uses_jev_kit_cli_for_all_permission_requests(self):
        config = (ROOT / "codex" / "config.example.toml").read_text(encoding="utf-8")
        self.assertIn("[[hooks.PermissionRequest]]", config)
        self.assertIn('matcher = ".*"', config)
        self.assertIn("jev-agent-review --adapter codex-permission", config)
        self.assertIn("jev-permission-review-policy.json", config)
        self.assertIn("--status-file", config)
        self.assertNotIn("jev-permission-review.py", config)

    def test_policy_keeps_the_measured_thresholds_and_versioned_contract(self):
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        self.assertEqual(policy["schemaVersion"], 1)
        self.assertEqual(policy["policy"]["id"], "ai-dev-harness.permission-review")
        self.assertEqual(policy["policy"]["version"], "1")
        self.assertEqual(policy["policy"]["thresholds"], {
            "policyCompliant": 0.70,
            "instructionAligned": 0.70,
            "highRisk": 0.15,
        })
        self.assertEqual(policy["userMessageCount"], 4)

    def test_legacy_python_decision_implementation_is_removed(self):
        self.assertFalse(LEGACY_HOOK.exists())


if __name__ == "__main__":
    unittest.main()
