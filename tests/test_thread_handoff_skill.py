import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "codex" / "skills" / "codex-thread-handoff" / "SKILL.md"


def handoff_instructions() -> str:
    skill_dir = SKILL.parent
    files = [SKILL, *sorted((skill_dir / "references").glob("*.md"))]
    return "\n".join(path.read_text() for path in files)


class ThreadHandoffSkillTests(unittest.TestCase):
    def test_handoff_resumes_only_when_latest_request_explicitly_asks(self):
        content = handoff_instructions()

        self.assertIn(
            "A plain handoff authorizes only destination-task creation, context transfer, "
            "required-artifact transfer, and read-only destination verification.",
            content,
        )
        self.assertIn("## Proposed resume point", content)
        self.assertIn("Post-verification mode", content)
        self.assertIn("A plain handoff stops after verification", content)
        self.assertIn(
            "An explicit handoff-and-resume request authorizes the destination to continue",
            content,
        )
        self.assertIn(
            "For `RESUME`, continue the proposed resume point in the same turn",
            content,
        )
        self.assertIn("For `STOP`", content)
        self.assertIn("does not authorize browser use, credentials, external services", content)

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
            "Use the latest verified handoff packet or compaction summary as the baseline",
            content,
        )
        self.assertIn("Read older history only when the baseline is missing", content)
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
            "The resume point does not replace the task objective",
            content,
        )

    def test_checkout_local_environment_files_do_not_block_or_create_noise(self):
        content = handoff_instructions()

        self.assertIn("known environment-generated files", content)
        self.assertIn("Block on missing task artifacts", content)
        self.assertIn(
            "A source-only or destination-only environment-generated file does not block the handoff",
            content,
        )
        self.assertIn("do not put it in expected task changes", content)
        self.assertIn("Excluded environment state may differ by checkout", content)
        self.assertIn(
            "Do not mention a present, absent, or changed excluded environment file",
            content,
        )
        self.assertIn(
            "Do not enumerate passing checks such as `HEAD`, remote branch equality, "
            "default branch, absent OpenSpec changes",
            content,
        )
        self.assertIn(
            "does not become a blocker merely because it is present in only one checkout",
            content,
        )

    def test_destination_blocks_only_on_task_bearing_state(self):
        content = handoff_instructions()

        self.assertIn("Verification gates only task-bearing state", content)
        self.assertIn("task-required dirty state", content)
        self.assertIn(
            "If a task-required artifact or semantic workstream is missing",
            content,
        )
        self.assertNotIn("If anything is missing, reclassified, or conflicting", content)

    def test_execution_detail_is_loaded_only_after_acceptance(self):
        content = SKILL.read_text()

        self.assertIn("For timing advice or a suggestion, use only this file.", content)
        self.assertIn("references/prepare-transfer.md", content)
        self.assertIn("references/verify-destination.md", content)
        self.assertNotIn("## Build The Required-Artifact Manifest", content)

    def test_compaction_alone_does_not_repeat_handoff_suggestions(self):
        content = SKILL.read_text()

        self.assertIn("Compaction alone is also insufficient", content)
        self.assertIn("at most once per task", content)

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

        self.assertIn("Fast same-host path", content)
        self.assertIn("bound post-creation coordination to at most 30 seconds", content)
        self.assertIn("Do not keep the source turn open", content)
        self.assertIn("one supported identifier-resolution wait", content)
        self.assertIn("do not make the user poll", content)
        self.assertIn("only when the user explicitly requested source archival", content)
        self.assertIn("never require the user to perform cleanup", content)

    def test_committed_handoff_sends_packet_and_ready_in_initial_creation(self):
        content = handoff_instructions()

        self.assertIn("Create exactly one destination", content)
        self.assertIn('`model: "gpt-5.6-sol"`', content)
        self.assertIn('`thinking: "high"`', content)
        self.assertIn("do not rely on task or global defaults", content)
        self.assertIn(
            "put the complete continuation packet, its `Post-verification mode`, "
            "`HANDOFF_READY`, and the "
            "destination-first-response instructions in the initial prompt",
            content,
        )
        self.assertIn(
            "Do not split a committed-tree handoff into a bootstrap prompt and a "
            "follow-up message",
            content,
        )
        self.assertNotIn("Bootstrap only.", content)

    def test_pending_async_creation_is_not_rediscovered_or_recreated(self):
        content = handoff_instructions()

        self.assertIn(
            "A successful or setup-in-progress creation response consumes that attempt",
            content,
        )
        self.assertIn("Retain its `threadId` or `clientThreadId`", content)
        self.assertIn(
            "Do not infer the destination from task titles, recent worktrees, filesystem "
            "timestamps, session logs, or repeated `list_threads` calls",
            content,
        )
        self.assertIn("Do not call destination creation again", content)
        self.assertIn("report the handoff as incomplete", content)

    def test_post_creation_artifacts_require_resolvable_follow_up_before_creation(self):
        content = handoff_instructions()

        self.assertIn("`HANDOFF_PENDING_ARTIFACTS`", content)
        self.assertIn(
            "require follow-up delivery and a supported `clientThreadId`-to-`threadId` "
            "resolution path before creation",
            content,
        )
        self.assertIn(
            "stop before creation instead of starting a destination that cannot receive "
            "the artifacts",
            content,
        )


if __name__ == "__main__":
    unittest.main()
