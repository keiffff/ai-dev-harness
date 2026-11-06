import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "codex/skills/codex-code-review/scripts/review_record.py"
spec = importlib.util.spec_from_file_location("review_record", SCRIPT)
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class ReviewRecordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "source.txt").write_text("The size is measured in bytes. Native option supports bytes. Reviewer: acceptance remains unknown.")
        (self.root / "description.txt").write_text("The size display uses bytes. ORIGINAL_REQUIREMENT_SENTINEL")
        (self.root / "request.txt").write_text("Review the size display.")
        self.evidence_list = self.root / "evidence.json"
        self.save(self.evidence_list, {"request": "request.txt", "descriptions": [{"change": "upload", "file": "description.txt"}],
            "diffs": [], "sources": []})
        self.ref = [{"file": "source.txt", "quote": "The size is measured in bytes."}]
        self.plan = {"changes": [{"id": "upload", "purpose": "サイズ制限を正しく表示する",
            "mechanisms": [], "requirements": [{"text": "単位はバイト", "evidence": self.ref}],
            "unknowns": [], "lookups": [{"id": "native", "question": "標準機能で同じ要件を保てるか"}],
            "lookup_not_needed": ""}],
            "objections": [{"id": "acceptance", "change": "upload", "claim": "受理条件は未確認",
                "material": True, "evidence": [{"file": "source.txt", "quote": "acceptance remains unknown"}]}]}
        self.result = {"changes": [{"id": "upload", "lookup_results": [{"id": "native",
            "result": "標準の設定が同じ単位を扱う", "evidence": self.ref}],
            "options": [{"name": "標準の設定", "assessment": "独自の単位変換が不要", "evidence": self.ref}],
            "choice": "標準の設定", "reason": "同じ制限を表現できる", "findings": [], "verification": "設定内容のみ確認",
            "delivery": {"summary": "サイズ表示には標準の設定が適切。ただし受理条件は確認が必要。",
                "decisions": [{"text": "受理条件は未確認。実際の受理はまだ確認できないため、受理する条件を確認してください。",
                    "objections": ["acceptance"], "goal_checks": []}], "claude_summary": "受理条件の懸念を保留し確認事項とした。"}}],
            "dispositions": [{"id": "acceptance", "status": "unresolved", "reason": "実際の受理はまだ確認できない", "evidence": []}]}
        self.plan_file = self.root / "plan.json"
        self.receipt = self.root / "receipt.json"
        self.assessment = self.root / "assessment.json"
        self.save(self.plan_file, self.plan)
        review.prepare(self.plan_file, self.receipt)

    @staticmethod
    def save(path, value):
        path.write_text(json.dumps(value, ensure_ascii=False))

    def render(self):
        self.save(self.assessment, self.result)
        return review.render(self.receipt, self.assessment)

    def test_unresolved_material_claim_is_in_overall_result_and_output_is_stdout_body(self):
        output = self.render()
        self.assertIn("受理条件は未確認", output)
        self.assertIn("実際の受理はまだ確認できない", output)
        self.assertIn("修正が必要な点：0件", output)
        self.assertIn("判断・確認してほしい点：1件", output)
        self.assertTrue(output.startswith("### upload\n"))
        self.assertFalse(output.startswith("````"))
        self.assertFalse((self.root / "review.md").exists())

    def test_missing_lookup_result_is_not_completion(self):
        self.result["changes"][0]["lookup_results"] = []
        with self.assertRaisesRegex(ValueError, "planned lookup"):
            self.render()

    def test_missing_objection_cannot_disappear(self):
        self.result["dispositions"] = []
        with self.assertRaisesRegex(ValueError, "objection"):
            self.render()

    def test_resolution_needs_evidence(self):
        self.result["dispositions"][0]["status"] = "resolved"
        with self.assertRaisesRegex(ValueError, "Evidence is missing"):
            self.render()

    def test_counterevidence_can_resolve_without_forcing_a_change(self):
        self.result["dispositions"][0].update(status="resolved", reason="標準仕様を確認", evidence=self.ref)
        self.result["changes"][0]["delivery"].update(summary="サイズ表示には標準の設定が適切。", decisions=[],
            claude_summary="受理条件への懸念は標準仕様を確認して解消した。")
        output = self.render()
        self.assertIn("判断・確認してほしい点：ありません", output)
        self.assertIn("標準仕様を確認して解消", output)
        self.assertNotIn("Claudeからの異論", output)

    def test_wrong_quote_does_not_count_as_research(self):
        self.result["changes"][0]["lookup_results"][0]["evidence"] = [{"file": "source.txt", "quote": "Not in source"}]
        with self.assertRaisesRegex(ValueError, "absent"):
            self.render()

    def test_plan_and_source_cannot_be_replaced_before_delivery(self):
        self.plan["objections"] = []
        self.save(self.plan_file, self.plan)
        with self.assertRaisesRegex(ValueError, "plan changed"):
            self.render()

    def test_changed_source_is_detected(self):
        (self.root / "source.txt").write_text("Edited after planning")
        with self.assertRaisesRegex(ValueError, "source changed"):
            self.render()

    def test_priority_codes_cannot_substitute_for_reasoning(self):
        self.result["changes"][0]["delivery"]["summary"] = "P2なので直す"
        with self.assertRaisesRegex(ValueError, "priority codes"):
            self.render()

    def test_recommendation_is_one_of_the_compared_options(self):
        self.result["changes"][0]["choice"] = "別の未比較方式"
        with self.assertRaisesRegex(ValueError, "compared options"):
            self.render()

    def research(self, with_web=True):
        self.plan["changes"][0]["mechanisms"] = ["File API"]
        self.plan["implementation"] = "implementation and prior conclusion must not be sent"
        self.save(self.plan_file, self.plan)
        self.receipt = self.root / "research-receipt.json"
        review.prepare(self.plan_file, self.receipt)

        def native(command, **kwargs):
            answer = Path(command[command.index("-o") + 1])
            self.save(answer, {"changes": [{"id": "upload", "options": [{"name": "native size",
                "capability": "reads bytes", "source": "https://example.test/spec", "compatibility": "supported",
                "caveat": "check the consumer"}], "goal_checks": [{"id": "unit", "condition": "サイズを表示する",
                    "expected": "バイト単位の値になる", "requirement": "単位はバイト"}], "limits": "not a runtime test"}]})
            if with_web:
                kwargs["stdout"].write(json.dumps({"type": "item.completed", "item": {
                    "type": "web_search", "action": {"type": "open_page", "url": "https://example.test/spec"}}}) + "\n")
            kwargs["stdout"].write(json.dumps({"type": "turn.completed"}) + "\n")
            return SimpleNamespace(returncode=0)

        with patch.object(review.subprocess, "run", side_effect=native):
            return review.discover(self.receipt, self.root / "research", Path("/verified/codex"), "configured-model", "medium", self.evidence_list)

    def test_research_input_excludes_implementation_and_prior_conclusions(self):
        self.research()
        packet = (self.root / "research/input.json").read_text()
        self.assertIn("File API", packet)
        self.assertNotIn("implementation", packet)
        self.assertNotIn("Reviewer", packet)
        self.assertNotIn("source.txt", packet)
        self.assertIn("ORIGINAL_REQUIREMENT_SENTINEL", packet)

    def test_memory_only_research_does_not_count_as_discovery(self):
        with self.assertRaisesRegex(ValueError, "discovery did not complete"):
            self.research(with_web=False)

    def test_independently_found_candidate_cannot_be_silently_omitted(self):
        discovery = self.research()
        self.result["changes"][0]["discovery_assessment"] = []
        self.save(self.assessment, self.result)
        with self.assertRaisesRegex(ValueError, "every independently discovered"):
            review.render(self.receipt, self.assessment, discovery)

    def test_discovery_result_cannot_be_rewritten_for_delivery(self):
        discovery = self.research()
        result = review.read(discovery)
        result["changes"][0]["options"] = []
        self.save(discovery, result)
        self.save(self.assessment, self.result)
        with self.assertRaisesRegex(ValueError, "not bound"):
            review.render(self.receipt, self.assessment, discovery)

    def test_startup_permission_fault_identifies_the_same_producer_permission_flow(self):
        self.plan["changes"][0]["mechanisms"] = ["File API"]
        self.save(self.plan_file, self.plan)
        receipt = self.root / "startup-receipt.json"
        review.prepare(self.plan_file, receipt)

        def native(command, **kwargs):
            kwargs["stderr"].write("failed to initialize in-process app-server client: Operation not permitted")
            return SimpleNamespace(returncode=1)

        with patch.object(review.subprocess, "run", side_effect=native) as invoke:
            with self.assertRaisesRegex(ValueError, "same discover producer.*normal permission flow"):
                review.discover(receipt, self.root / "startup", Path("/verified/codex"), "configured-model", "medium", self.evidence_list)
            self.assertEqual(invoke.call_count, 1)
        self.assertEqual(review.read(self.root / "startup/execution.json")["process_exit"], 1)

    def bind_late_advice(self):
        report = self.root / "advisor.txt"
        report.write_text("The native option has a compatibility limit.")
        objections = self.root / "advisor-objections.json"
        self.save(objections, [{"id": "compatibility", "change": "upload", "claim": "互換条件が残る",
            "material": True, "evidence": [{"file": "advisor.txt", "quote": "has a compatibility limit"}]}])
        bound = self.root / "advice.json"
        review.bind_advice(self.receipt, report, objections, bound)
        return bound

    def test_late_advisor_cannot_invalidate_the_prepared_goal_or_lose_an_objection(self):
        bound = self.bind_late_advice()
        self.save(self.assessment, self.result)
        with self.assertRaisesRegex(ValueError, "Every planned change and objection"):
            review.render(self.receipt, self.assessment, advice_file=bound)
        self.result["dispositions"].append({"id": "compatibility", "status": "unresolved",
            "reason": "対応条件をまだ確認できない", "evidence": []})
        self.result["changes"][0]["delivery"]["decisions"].append({"text": "互換条件が残るため対応条件を確認してください。",
            "objections": ["compatibility"], "goal_checks": []})
        self.save(self.assessment, self.result)
        output = review.render(self.receipt, self.assessment, advice_file=bound)
        self.assertIn("互換条件が残る", output)
        self.assertEqual(review.digest(self.plan_file), review.read(self.receipt)["plan_sha256"])

    def test_changed_advisor_report_is_not_the_bound_review(self):
        bound = self.bind_late_advice()
        (self.root / "advisor.txt").write_text("Replaced after binding")
        self.save(self.assessment, self.result)
        with self.assertRaisesRegex(ValueError, "Advisor objections changed"):
            review.render(self.receipt, self.assessment, advice_file=bound)

    def test_advisor_input_uses_originals_without_main_decision_or_earlier_review(self):
        self.plan["choice"] = "MAIN_DECISION_SENTINEL"
        self.save(self.plan_file, self.plan)
        receipt = self.root / "input-receipt.json"
        review.prepare(self.plan_file, receipt)
        (self.root / "request.txt").write_text("Review the size display.")
        (self.root / "change.diff").write_text("diff --git a/display.py b/display.py\n")
        bundle = self.root / "evidence.json"
        self.save(bundle, {"request": "request.txt", "descriptions": [{"change": "upload", "file": "source.txt"}],
            "diffs": [{"change": "upload", "file": "change.diff"}], "sources": []})
        output = self.root / "advisor-input.txt"
        review.advisor_input(receipt, bundle, None, output)
        prompt = output.read_text()
        self.assertIn("Review the size display.", prompt)
        self.assertIn("diff --git", prompt)
        self.assertNotIn("MAIN_DECISION_SENTINEL", prompt)
        self.assertNotIn("受理条件は未確認", prompt)

    def test_source_derived_expected_outcome_cannot_be_skipped(self):
        discovery = self.research()
        self.result["changes"][0]["discovery_assessment"] = [{"name": "native size", "reason": "標準機能で足りる"}]
        self.result["changes"][0]["goal_check_assessment"] = []
        self.save(self.assessment, self.result)
        with self.assertRaisesRegex(ValueError, "every source-derived expected outcome"):
            review.render(self.receipt, self.assessment, discovery)

    def test_goal_mismatch_is_visible_even_if_the_recommendation_sounds_clean(self):
        discovery = self.research()
        self.result["changes"][0]["discovery_assessment"] = [{"name": "native size", "reason": "標準機能で足りる"}]
        self.result["changes"][0]["goal_check_assessment"] = [{"id": "unit", "status": "not_met",
            "actual": "別の単位を表示する", "reason": "要件と表示が一致しない", "evidence": self.ref}]
        self.result["changes"][0]["findings"] = [{"location": "display.py:12",
            "comment": "サイズ表示が別の単位を表示するため、バイト単位の値になるよう修正してください。",
            "evidence": self.ref, "goal_checks": ["unit"]}]
        self.save(self.assessment, self.result)
        output = review.render(self.receipt, self.assessment, discovery)
        self.assertIn("バイト単位の値になる", output)
        self.assertIn("別の単位を表示する", output)
        self.assertIn("修正が必要な点：1件", output)

    def test_clean_summary_cannot_hide_material_unresolved_claim(self):
        self.result["changes"][0]["delivery"].update(summary="問題ありません。", decisions=[])
        with self.assertRaisesRegex(ValueError, "material unresolved"):
            self.render()

    def test_goal_mismatch_cannot_disappear_in_reader_view(self):
        discovery = self.research()
        self.result["changes"][0]["discovery_assessment"] = [{"name": "native size", "reason": "標準機能"}]
        self.result["changes"][0]["goal_check_assessment"] = [{"id": "unit", "status": "not_met",
            "actual": "別の単位", "reason": "不一致", "evidence": self.ref}]
        self.save(self.assessment, self.result)
        with self.assertRaisesRegex(ValueError, "goal mismatch"):
            review.render(self.receipt, self.assessment, discovery)

    def test_coverage_cannot_reference_a_nonexistent_item(self):
        self.result["changes"][0]["delivery"]["decisions"][0]["objections"].append("invented")
        with self.assertRaisesRegex(ValueError, "unknown or differently scoped"):
            self.render()

    def test_internal_comparisons_are_validated_but_not_dumped(self):
        self.plan["changes"][0]["unknowns"] = ["INTERNAL_UNKNOWN"]
        self.save(self.plan_file, self.plan)
        self.receipt = self.root / "comparison-receipt.json"
        review.prepare(self.plan_file, self.receipt)
        self.result["changes"][0]["options"].append({"name": "INTERNAL_CANDIDATE",
            "assessment": "INTERNAL_COMPARISON", "evidence": self.ref})
        output = self.render()
        self.assertNotIn("INTERNAL_", output)
        self.result["changes"][0]["options"][1]["evidence"] = []
        with self.assertRaisesRegex(ValueError, "Evidence is missing"):
            self.render()


if __name__ == "__main__":
    unittest.main()
