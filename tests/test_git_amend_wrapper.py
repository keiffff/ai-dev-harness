import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "wrappers/bin/git-user-approved.example"


class GitAmendWrapperTests(unittest.TestCase):
    def run_wrapper(self, *args):
        with tempfile.TemporaryDirectory() as directory:
            fake_git = Path(directory) / "git"
            fake_git.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
            fake_git.chmod(0o755)
            return subprocess.run(
                ["/bin/zsh", str(WRAPPER), "commit", *args],
                env={**os.environ, "PATH": directory + os.pathsep + os.environ["PATH"]},
                capture_output=True,
                text=True,
            )

    def test_amend_requires_explicit_confirmation(self):
        result = self.run_wrapper("--amend", "--no-edit")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")

    def test_confirmed_amend_passes_only_git_arguments(self):
        result = self.run_wrapper("--confirm-user-requested", "--amend", "--no-edit")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ["commit", "--amend", "--no-edit"])

    def test_confirmation_does_not_allow_implicit_all_staging(self):
        for option in ("-a", "--all"):
            with self.subTest(option=option):
                result = self.run_wrapper("--confirm-user-requested", "--amend", option)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
