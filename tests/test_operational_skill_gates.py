import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class OperationalSkillGateTests(unittest.TestCase):
    def test_skill_descriptions_keep_discovery_context_bounded(self):
        descriptions = []
        for skill in (ROOT / "codex" / "skills").glob("*/SKILL.md"):
            description = next(
                line.removeprefix("description: ")
                for line in skill.read_text().splitlines()
                if line.startswith("description: ")
            )
            descriptions.append(description)

        self.assertLessEqual(sum(map(len, descriptions)), 3000)
        self.assertLessEqual(max(map(len, descriptions)), 200)

    def test_expensive_advisors_require_explicit_invocation(self):
        for skill_name in (
            "claude-fable-strategic-review",
            "gpt-sol-strategic-review",
        ):
            metadata = (
                ROOT / "codex" / "skills" / skill_name / "agents" / "openai.yaml"
            ).read_text()
            self.assertIn("allow_implicit_invocation: false", metadata)

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
        self.assertIn("coarse spot checks cannot support", content)
        self.assertIn("A successful fallback does not verify the primary path", content)

    def test_operational_sequence_traces_implicit_triggers(self):
        content = (
            ROOT / "codex" / "skills" / "codex-context-engineering" / "SKILL.md"
        ).read_text()

        self.assertIn("implicit creation write", content)
        self.assertIn("before calling an operational procedure safe", content)

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

    def test_cdk_preflight_checks_cloudfront_alias_and_dns_state(self):
        content = (
            ROOT
            / "codex"
            / "skills"
            / "codex-cdk-design-review"
            / "references"
            / "cdk-review-checklist.md"
        ).read_text()

        self.assertIn("exact and wildcard DNS", content)
        self.assertIn("current alias ownership", content)
        self.assertIn("DNS order avoid a conflict", content)


if __name__ == "__main__":
    unittest.main()
