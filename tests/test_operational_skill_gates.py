import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class OperationalSkillGateTests(unittest.TestCase):
    def test_unreleased_compatibility_requires_evidence(self):
        content = (ROOT / "codex" / "AGENTS.md").read_text()

        self.assertIn("リリース済み契約、現行データ、またはユーザーの明示要求", content)
        self.assertIn("根拠がなければ追加しない", content)

    def test_debugging_checks_evidence_and_reproduction_surfaces(self):
        content = (
            ROOT / "codex" / "skills" / "codex-debugging-loop" / "SKILL.md"
        ).read_text()

        self.assertIn("Confirm the selected data source contains those observations", content)
        self.assertIn("Match the reproduction surface", content)
        self.assertIn("A successful fallback does not verify the primary path", content)

    def test_writing_revision_is_limited_to_the_requested_delta(self):
        content = (ROOT / "codex" / "skills" / "codex-writing" / "SKILL.md").read_text()

        self.assertIn("every change is required by the requested delta", content)
        self.assertIn("Do not trade an unwanted rewrite for over-compression", content)

    def test_cdk_preflight_distinguishes_provider_success_from_fallback(self):
        content = (
            ROOT
            / "codex"
            / "skills"
            / "codex-cdk-design-review"
            / "references"
            / "cdk-review-checklist.md"
        ).read_text()

        self.assertIn("Organizations SCPs", content)
        self.assertIn("an overall successful job is insufficient", content)


if __name__ == "__main__":
    unittest.main()
