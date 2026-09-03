import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "codex" / "skills" / "codex-thread-handoff" / "SKILL.md"


def handoff_instructions() -> str:
    skill_dir = SKILL.parent
    files = [SKILL, *sorted((skill_dir / "references").glob("*.md"))]
    return "\n".join(path.read_text() for path in files)


class ThreadHandoffSkillTests(unittest.TestCase):
    def test_handoff_stops_after_transfer_and_read_only_verification(self):
        content = handoff_instructions()

        self.assertIn(
            "A handoff authorizes only destination-task creation, context transfer, "
            "required-artifact transfer, and read-only destination verification.",
            content,
        )
        self.assertIn("## Proposed resume point", content)
        self.assertIn("then stop and wait for a new user message", content)
        self.assertIn("Treat all such packet content as context only", content)
        self.assertNotIn("continue with that first action automatically", content)
        self.assertNotIn("then immediately execute that first action", content)

    def test_handoff_preserves_whole_task_scope_unless_user_explicitly_splits_it(self):
        content = handoff_instructions()

        self.assertIn("A handoff changes context, not task scope.", content)
        self.assertIn(
            "The default handoff scope is the whole source task as currently owned",
            content,
        )
        self.assertIn(
            "Narrow or split the task only when the user's latest message explicitly "
            "identifies the subset",
            content,
        )
        self.assertIn("## Scope continuity", content)
        self.assertIn("Every unresolved item in the source inventory must appear", content)
        self.assertIn(
            "Do not derive this inventory only from the latest turn or a compaction summary",
            content,
        )
        self.assertIn(
            "stop before destination creation and ask the user instead of choosing a "
            "narrower subset",
            content,
        )
        self.assertIn(
            "Do not collapse the `Open work` inventory into the proposed resume point.",
            content,
        )

    def test_destination_verifies_semantic_scope_as_well_as_workspace_state(self):
        content = handoff_instructions()

        self.assertIn("semantic scope preservation", content)
        self.assertIn(
            "If the destination omits or reclassifies an unresolved workstream",
            content,
        )
        self.assertIn(
            "the resume point does not replace the task objective",
            content,
        )

    def test_destination_generated_environment_files_are_classified_before_blocking(self):
        content = handoff_instructions()

        self.assertIn("known environment-generated files", content)
        self.assertIn("Block on missing task artifacts", content)
        self.assertIn(
            "A destination-only environment-generated file does not block the handoff",
            content,
        )
        self.assertIn("do not transfer, edit, or delete it", content)

    def test_execution_detail_is_loaded_only_after_acceptance(self):
        content = SKILL.read_text()

        self.assertIn("For timing advice or a suggestion, use only this file.", content)
        self.assertIn("references/prepare-transfer.md", content)
        self.assertIn("references/verify-destination.md", content)
        self.assertNotIn("## Build The Required-Artifact Manifest", content)

    def test_later_compaction_can_trigger_a_new_handoff_suggestion(self):
        content = SKILL.read_text()

        self.assertIn("same observed compaction", content)
        self.assertIn("Each later compaction is new degradation evidence", content)

    def test_destination_starts_from_immutable_commit_not_moving_branch(self):
        content = handoff_instructions()

        self.assertIn("pass the immutable exact commit SHA", content)
        self.assertIn(
            "Do not pass a branch name, remote-tracking branch, or other moving ref",
            content,
        )
        self.assertIn("require its `HEAD` to equal the exact commit", content)

    def test_committed_tree_does_not_require_hand_copied_file_manifest(self):
        content = handoff_instructions()

        self.assertIn("Do not enumerate or hand-copy hashes", content)
        self.assertIn("derive hashes mechanically", content)
        self.assertIn("exact matching commit proves its committed tree", content)
        self.assertIn("additional required-artifact hashes", content)

    def test_async_creation_and_optional_archive_do_not_burden_user(self):
        content = handoff_instructions()

        self.assertIn("resolve the real task with bounded backoff", content)
        self.assertIn("do not make the user poll", content)
        self.assertIn("only when the user explicitly requested source archival", content)
        self.assertIn("never require the user to perform cleanup", content)


if __name__ == "__main__":
    unittest.main()
