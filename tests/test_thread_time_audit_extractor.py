import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "codex"
    / "skills"
    / "codex-thread-time-audit"
    / "scripts"
    / "extract_codex_thread_times.py"
)


def load_extractor():
    spec = importlib.util.spec_from_file_location("thread_time_extractor", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")


class ThreadTimeAuditExtractorTests(unittest.TestCase):
    def test_each_turn_uses_its_matching_turn_context_cwd(self):
        extractor = load_extractor()
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir)
            session_id = "session-project-switch"
            write_jsonl(
                codex_home / "sessions" / "2026" / "08" / "25" / "rollout.jsonl",
                [
                    {
                        "timestamp": "2026-08-25T00:00:00Z",
                        "type": "session_meta",
                        "payload": {"id": session_id, "cwd": "/workspace/initial", "source": "vscode"},
                    },
                    {
                        "timestamp": "2026-08-25T00:00:01Z",
                        "type": "event_msg",
                        "payload": {"type": "task_started", "turn_id": "first", "started_at": 1001},
                    },
                    {
                        "timestamp": "2026-08-25T00:00:02Z",
                        "type": "turn_context",
                        "payload": {"turn_id": "first", "cwd": "/workspace/project-a"},
                    },
                    {
                        "timestamp": "2026-08-25T00:00:03Z",
                        "type": "event_msg",
                        "payload": {"type": "task_complete", "turn_id": "first", "completed_at": 1003},
                    },
                    {
                        "timestamp": "2026-08-25T00:00:04Z",
                        "type": "event_msg",
                        "payload": {"type": "task_started", "turn_id": "second", "started_at": 1004},
                    },
                    {
                        "timestamp": "2026-08-25T00:00:05Z",
                        "type": "turn_context",
                        "payload": {"turn_id": "second", "cwd": "/workspace/project-b"},
                    },
                    {
                        "timestamp": "2026-08-25T00:00:06Z",
                        "type": "event_msg",
                        "payload": {"type": "task_complete", "turn_id": "second", "completed_at": 1006},
                    },
                ],
            )

            rows, stats = extractor.extract_rows(
                codex_home,
                1000,
                1100,
                {session_id: "fixture"},
                {},
                "top-level",
            )

            self.assertEqual([row["project"] for row in rows], ["project-a", "project-b"])
            self.assertEqual(stats["tasks_with_session_cwd_fallback"], 0)

    def test_task_start_is_recorded_across_user_marker_formats(self):
        extractor = load_extractor()
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir)
            session_id = "session-main"
            write_jsonl(
                codex_home / "sessions" / "2026" / "08" / "25" / "rollout.jsonl",
                [
                    {
                        "timestamp": "2026-08-25T00:00:00Z",
                        "type": "session_meta",
                        "payload": {"id": session_id, "cwd": "/workspace/project", "source": "vscode"},
                    },
                    {
                        "timestamp": "2026-08-25T00:00:01Z",
                        "type": "event_msg",
                        "payload": {"type": "task_started", "turn_id": "old", "started_at": 1001},
                    },
                    {
                        "timestamp": "2026-08-25T00:00:02Z",
                        "type": "event_msg",
                        "payload": {"type": "user_message"},
                    },
                    {
                        "timestamp": "2026-08-25T00:00:03Z",
                        "type": "event_msg",
                        "payload": {"type": "task_complete", "turn_id": "old", "completed_at": 1003},
                    },
                    {
                        "timestamp": "2026-08-25T00:00:04Z",
                        "type": "event_msg",
                        "payload": {"type": "task_started", "turn_id": "new", "started_at": 1004},
                    },
                    {
                        "timestamp": "2026-08-25T00:00:05Z",
                        "type": "response_item",
                        "payload": {"type": "message", "role": "user", "content": []},
                    },
                    {
                        "timestamp": "2026-08-25T00:00:06Z",
                        "type": "event_msg",
                        "payload": {"type": "task_complete", "turn_id": "new", "completed_at": 1006},
                    },
                    {
                        "timestamp": "2026-08-25T00:00:07Z",
                        "type": "event_msg",
                        "payload": {"type": "task_started", "turn_id": "unmarked", "started_at": 1007},
                    },
                    {
                        "timestamp": "2026-08-25T00:00:08Z",
                        "type": "event_msg",
                        "payload": {"type": "turn_aborted", "turn_id": "unmarked", "completed_at": 1008},
                    },
                ],
            )
            write_jsonl(
                codex_home / "sessions" / "2026" / "08" / "25" / "subagent.jsonl",
                [
                    {
                        "timestamp": "2026-08-25T00:00:00Z",
                        "type": "session_meta",
                        "payload": {
                            "id": "session-subagent",
                            "cwd": "/workspace/project",
                            "source": {"subagent": {"thread_spawn": {"parent_thread_id": session_id}}},
                            "parent_thread_id": session_id,
                        },
                    },
                    {
                        "timestamp": "2026-08-25T00:00:20Z",
                        "type": "event_msg",
                        "payload": {"type": "task_started", "turn_id": "subagent", "started_at": 1020},
                    },
                ],
            )

            rows, stats = extractor.extract_rows(
                codex_home,
                1000,
                1100,
                {session_id: "fixture"},
                {},
                "top-level",
            )

            self.assertEqual([row["turnId"] for row in rows], ["old", "new", "unmarked"])
            self.assertEqual(rows[0]["userEvidence"], ["event_msg.user_message"])
            self.assertEqual(rows[1]["userEvidence"], ["response_item.message.user"])
            self.assertEqual(rows[2]["userEvidence"], [])
            self.assertEqual(stats["raw_task_starts"], 3)
            self.assertEqual(stats["rows"], 3)
            self.assertEqual(stats["tasks_without_known_user_evidence"], 1)
            self.assertEqual(stats["skipped_subagent_files"], 1)
            self.assertEqual(stats["skipped_subagent_task_starts"], 1)

            diagnostics = extractor.build_diagnostics(
                stats,
                datetime.fromtimestamp(1000, timezone.utc),
                datetime.fromtimestamp(1100, timezone.utc),
                "UTC",
                "top-level",
            )
            self.assertEqual(diagnostics["coverage"]["unaccountedTaskStarts"], 0)
            self.assertEqual(diagnostics["status"], "review_required")


if __name__ == "__main__":
    unittest.main()
