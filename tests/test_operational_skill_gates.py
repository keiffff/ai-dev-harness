import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class OperationalSkillGateTests(unittest.TestCase):
    def test_codex_config_uses_gpt_6_1_sol_as_the_main_model(self):
        config = (ROOT / "codex" / "config.example.toml").read_text()

        self.assertIn('model = "gpt-6.1-sol"', config)
        self.assertIn('model_reasoning_effort = "medium"', config)

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

    def test_html_report_keeps_composition_and_fact_ownership_separate(self):
        report = (
            ROOT / "codex" / "skills" / "claude-html-report" / "SKILL.md"
        ).read_text()
        contract = (
            ROOT
            / "codex"
            / "skills"
            / "claude-html-report"
            / "references"
            / "report-contract.md"
        ).read_text()
        frontend = (
            ROOT / "codex" / "skills" / "codex-frontend-ui" / "SKILL.md"
        ).read_text()
        writing = (
            ROOT / "codex" / "skills" / "codex-writing" / "SKILL.md"
        ).read_text()

        self.assertIn("Claude owns the initial complete report composition", report)
        self.assertIn("every editorial revision", report)
        self.assertIn("Codex owns evidence collection", report)
        self.assertIn("data-fact", contract)
        self.assertIn("data-weight", contract)
        self.assertIn("Audience-facing information budget", contract)
        self.assertIn("source completeness", report)
        self.assertIn("first viewport", report)
        self.assertIn("Rejected claims", contract)
        self.assertIn("comprehension dependencies", report)
        self.assertIn("claude-html-report", frontend)
        self.assertIn("bounded exception", writing)
        self.assertIn("Do not request separate approval", report)
        self.assertIn("company-internal, confidential-design or personal information", report)
        self.assertIn("every task-required non-secret fact", contract)
        self.assertIn("Run the wrapper with normal sandbox permissions", report)
        self.assertIn("Do not request escalated permissions solely for Keychain access", report)

    def test_gemini_skill_has_standing_non_secret_authorization(self):
        skill = (
            ROOT
            / "codex"
            / "skills"
            / "gemini-japanese-polish"
            / "SKILL.md"
        ).read_text()

        self.assertIn("standing authorization", skill)
        self.assertIn("Do not request separate approval", skill)
        self.assertIn("company-internal repository names", skill)
        self.assertIn("PR or issue identifiers", skill)
        self.assertIn("other secret-bearing content", skill)

    def test_gemini_skill_keeps_composition_ownership_with_gemini(self):
        skill = (
            ROOT
            / "codex"
            / "skills"
            / "gemini-japanese-polish"
            / "SKILL.md"
        ).read_text()

        self.assertIn("do not write a finished Codex draft", skill)
        self.assertIn("Do not use a Codex-authored draft as `<reference-draft>`", skill)
        self.assertIn("A structural difference from a Codex-authored draft is not a defect", skill)
        self.assertIn("Do not restore Codex-authored sentences", skill)

    def test_reader_facing_artifacts_use_semantic_and_visual_review_separately(self):
        integrity = (
            ROOT / "codex" / "skills" / "codex-artifact-integrity" / "SKILL.md"
        ).read_text()
        report = (
            ROOT / "codex" / "skills" / "claude-html-report" / "SKILL.md"
        ).read_text()
        frontend = (
            ROOT / "codex" / "skills" / "codex-frontend-ui" / "SKILL.md"
        ).read_text()
        gemini = (
            ROOT / "codex" / "skills" / "gemini-japanese-polish" / "SKILL.md"
        ).read_text()

        self.assertIn("JEV_ARTIFACT_REVIEW_WRAPPER", integrity)
        self.assertIn("--route-checks", integrity)
        self.assertIn("required_checks", integrity)
        self.assertIn("cannot remove an inherited runtime check", integrity)
        self.assertIn("routing evidence, not proof", integrity)
        self.assertIn("unavailable", integrity)
        self.assertIn("does not establish pixel overlap", integrity)
        self.assertIn("codex-artifact-integrity", report)
        self.assertIn("codex-artifact-integrity", frontend)
        self.assertIn("codex-artifact-integrity", gemini)

    def test_artifact_integrity_verifies_without_granting_editing_authority(self):
        integrity = (
            ROOT / "codex" / "skills" / "codex-artifact-integrity" / "SKILL.md"
        ).read_text()

        self.assertIn("it grants no editing authority", integrity)
        self.assertIn("The producing skill determines who may make corrections", integrity)
        self.assertIn("Codex validates findings against the original user request", integrity)
        self.assertIn("do not automatically forward reviewer suggestions", integrity)
        self.assertIn("Reject unsupported findings with a reason", integrity)
        self.assertIn("does not require an edit or another model call", integrity)
        self.assertIn("return confirmed defects to Claude", integrity)
        self.assertIn("Codex does not patch the report", integrity)
        self.assertIn("repairs authorized by that skill", integrity)
        self.assertIn("do not override either production workflow", integrity)

    def test_static_visuals_require_rendered_grid_overlay_qa(self):
        frontend = (
            ROOT / "codex" / "skills" / "codex-frontend-ui" / "SKILL.md"
        ).read_text()
        report = (
            ROOT / "codex" / "skills" / "claude-html-report" / "SKILL.md"
        ).read_text()
        report_contract = (
            ROOT
            / "codex"
            / "skills"
            / "claude-html-report"
            / "references"
            / "report-contract.md"
        ).read_text()
        visualization = (
            ROOT
            / "codex"
            / "skills"
            / "codex-frontend-ui"
            / "references"
            / "review-visualization.md"
        ).read_text()

        self.assertIn("temporary QA copy", frontend)
        self.assertIn("visible component bounds", frontend)
        self.assertIn("intended content insets", frontend)
        self.assertIn("enlarged crops", frontend)
        self.assertIn("Never ship or adopt the QA overlay", frontend)
        self.assertIn("overlay component bounds", visualization)
        self.assertIn("repeated row or column tracks", visualization)
        self.assertIn("never publish or adopt the QA overlay", visualization)
        self.assertIn("Claude owns the final spacing and alignment corrections", report)
        self.assertIn("temporary QA copy or screenshot overlay", report)
        self.assertIn("Do not ask Claude to produce the QA overlay", report)
        self.assertIn("grid alignment", report_contract)
        self.assertIn("temporary rendered QA overlay", report_contract)
        self.assertIn("never published", report_contract)

    def test_html_report_keeps_all_editorial_revisions_in_claude(self):
        report = (
            ROOT / "codex" / "skills" / "claude-html-report" / "SKILL.md"
        ).read_text()
        contract = (
            ROOT
            / "codex"
            / "skills"
            / "claude-html-report"
            / "references"
            / "report-contract.md"
        ).read_text()

        self.assertIn("Codex must not draft the report for Claude", report)
        self.assertIn("even for a typo, factual literal or responsive fix", report)
        self.assertIn("All editorial revisions return to Claude", report)
        self.assertIn("does not authorize redesigning unaffected sections", report)
        self.assertIn("Claude-only editorial revision", contract)
        self.assertIn("Codex must not edit the production report", contract)
        self.assertIn("mechanically substitute validated asset placeholders", contract)
        self.assertIn("its changes are never merged into the report", contract)
        self.assertIn("do not reuse a rejected or superseded report", contract)
        self.assertIn("Do not supply a Codex-authored ranked takeaway", contract)
        self.assertNotIn("Bounded Codex edit", report)
        self.assertNotIn("Local Codex revision", contract)

    def test_expensive_advisors_require_explicit_invocation(self):
        for skill_name in (
            "claude-fable-strategic-review",
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

    def test_failure_diagnosis_separates_stopping_layer_from_cause(self):
        content = (
            ROOT / "codex" / "skills" / "codex-debugging-loop" / "SKILL.md"
        ).read_text()

        self.assertIn("immediate stopping layer", content)
        self.assertIn("Do not present that layer as a root cause", content)
        self.assertIn("plausible alternative", content)
        self.assertIn("smallest additional observation", content)
        self.assertIn("successful fallback does not verify", content)
        self.assertIn("JEV_EVIDENCE_CHECK_WRAPPER", content)
        self.assertIn("non-secret evidence and the proposed claim", content)
        self.assertIn("do not retry automatically", content)

    def test_operational_sequence_traces_implicit_triggers(self):
        content = (
            ROOT / "codex" / "skills" / "codex-context-engineering" / "SKILL.md"
        ).read_text()

        self.assertIn("implicit creation write", content)
        self.assertIn("before calling an operational procedure safe", content)

    def test_ambiguous_references_stop_before_broad_log_search(self):
        agents = (ROOT / "codex" / "AGENTS.md").read_text()
        context = (
            ROOT / "codex" / "skills" / "codex-context-engineering" / "SKILL.md"
        ).read_text()

        self.assertIn("広いログ調査へ進む前にANDON", agents)
        self.assertIn("one direct lookup", context)
        self.assertIn("before starting a broad log search", context)

    def test_concise_output_keeps_explicit_breakdowns(self):
        content = (ROOT / "codex" / "AGENTS.md").read_text()

        self.assertIn("明示された件数、内訳、対象、比較条件は省かない", content)

    def test_review_raises_andon_instead_of_inventing_recovery(self):
        review = (
            ROOT / "codex" / "skills" / "codex-code-review" / "SKILL.md"
        ).read_text()
        doubt = (
            ROOT / "codex" / "skills" / "codex-doubt-review" / "SKILL.md"
        ).read_text()

        self.assertIn("Uncertain Boundary ANDON", review)
        self.assertIn("do not invent an identifier, fallback, retry", review)
        self.assertIn("use one bounded `codex-doubt-review` cycle", review)
        self.assertIn("at most three", doubt)
        self.assertIn("recommend an ANDON", doubt)

    def test_review_output_remains_copyable_outside_inline_review_ui(self):
        agents = (ROOT / "codex" / "AGENTS.md").read_text()
        review = (
            ROOT / "codex" / "skills" / "codex-code-review" / "SKILL.md"
        ).read_text()

        self.assertIn("コピー用レビュー本文", agents)
        self.assertIn("インライン表示は補助", agents)
        self.assertIn("outer four-backtick `markdown` fence", review)
        self.assertIn("never replace or shorten the copyable review body", review)

    def test_failure_patterns_distinguish_indirect_observation(self):
        content = (ROOT / "docs" / "failure-patterns.md").read_text()

        self.assertIn("間接的な観測を確定事実として扱う", content)
        # Keep the behavioral contract without pinning punctuation or one
        # particular Japanese sentence. Read the actual section, not other
        # unrelated ANDON mentions elsewhere in the document.
        section = content.split("## 間接的な観測を確定事実として扱う\n", 1)[1].split("\n## ", 1)[0]
        self.assertRegex(section, r"推測.*補完実装.*(?:進めず|進まず).*ANDON")

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
