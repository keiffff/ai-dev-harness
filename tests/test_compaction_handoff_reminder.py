import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK_DIR = ROOT / "hooks" / "codex"
SCRIPT = HOOK_DIR / "compaction-handoff-reminder.py"
HOOK_PYTHON = Path("/usr/bin/python3")
if not HOOK_PYTHON.exists():
    HOOK_PYTHON = Path(sys.executable)


def run_hook(state_dir: str, session_id: str = "session-1", source: str = "compact", payload: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({
        "PYTHONPATH": str(HOOK_DIR),
        "CODEX_HANDOFF_STATE_DIR": state_dir,
    })
    if payload is None:
        payload = json.dumps({
            "hook_event_name": "SessionStart",
            "source": source,
            "session_id": session_id,
        })
    return subprocess.run(
        [str(HOOK_PYTHON), str(SCRIPT)],
        input=payload,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )


class CompactionHandoffReminderTests(unittest.TestCase):
    def test_reminds_on_second_and_later_compactions(self):
        with tempfile.TemporaryDirectory() as state_dir:
            first = run_hook(state_dir)
            second = run_hook(state_dir)
            third = run_hook(state_dir)

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, "")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(third.returncode, 0, third.stderr)
        for result in (second, third):
            output = json.loads(result.stdout)
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "SessionStart")
            self.assertIn("codex-thread-handoff", hook_output["additionalContext"])
            self.assertIn("explicit user approval", hook_output["additionalContext"])
            self.assertIn("cover the whole root task", hook_output["additionalContext"])
            self.assertIn(
                "unless the user explicitly asks to split",
                hook_output["additionalContext"],
            )
            self.assertIn("at most once for each observed compaction", hook_output["additionalContext"])
            self.assertIn("Do not interrupt", hook_output["additionalContext"])

    def test_reads_existing_state_with_legacy_reminder_field(self):
        with tempfile.TemporaryDirectory() as state_dir:
            session_key = hashlib.sha256(b"session-1").hexdigest()
            path = Path(state_dir) / f"{session_key}.json"
            path.write_text(json.dumps({
                "compaction_count": 2,
                "reminder_emitted": True,
            }))
            result = run_hook(state_dir)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotEqual(result.stdout, "")

    def test_tracks_sessions_independently(self):
        with tempfile.TemporaryDirectory() as state_dir:
            self.assertEqual(run_hook(state_dir, session_id="session-a").stdout, "")
            self.assertEqual(run_hook(state_dir, session_id="session-b").stdout, "")
            self.assertNotEqual(run_hook(state_dir, session_id="session-a").stdout, "")
            self.assertNotEqual(run_hook(state_dir, session_id="session-b").stdout, "")

    def test_ignores_non_compaction_and_invalid_input(self):
        with tempfile.TemporaryDirectory() as state_dir:
            self.assertEqual(run_hook(state_dir, source="startup").stdout, "")
            self.assertEqual(run_hook(state_dir, session_id="").stdout, "")
            malformed = run_hook(state_dir, payload="{not json")
            self.assertEqual(malformed.returncode, 0)
            self.assertEqual(malformed.stdout, "")
            self.assertEqual(malformed.stderr, "")


if __name__ == "__main__":
    unittest.main()
