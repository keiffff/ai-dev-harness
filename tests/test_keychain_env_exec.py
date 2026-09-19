import importlib.machinery
import importlib.util
import os
import subprocess
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "wrappers" / "bin" / "keychain-env-exec.example"


def load_module():
    loader = importlib.machinery.SourceFileLoader("keychain_env_exec", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class KeychainEnvExecTests(unittest.TestCase):
    def test_tool_wrappers_do_not_read_keychain_directly(self):
        wrapper_names = [
            "claude-strategic-review.example",
            "claude-fable-strategic-review.example",
            "claude-html-report.example",
            "gemini-japanese-polish.example",
            "grok-x-research.example",
        ]
        for name in wrapper_names:
            with self.subTest(name=name):
                content = (ROOT / "wrappers" / "bin" / name).read_text()
                self.assertNotIn("find-generic-password", content)
                self.assertIn("keychain-env-exec", content)

    def test_existing_environment_value_skips_keychain(self):
        module = load_module()
        with mock.patch.dict(os.environ, {"EXAMPLE_API_KEY": "from-env"}, clear=True):
            with mock.patch.object(module.subprocess, "run") as run:
                self.assertEqual(module.load_secret("EXAMPLE_API_KEY", "EXAMPLE_SERVICE"), "from-env")
        run.assert_not_called()

    def test_keychain_value_is_captured_without_stderr(self):
        module = load_module()
        result = subprocess.CompletedProcess([], 0, stdout="from-keychain\n", stderr="")
        with mock.patch.dict(os.environ, {"USER": "kei"}, clear=True):
            with mock.patch.object(module.subprocess, "run", return_value=result) as run:
                self.assertEqual(module.load_secret("EXAMPLE_API_KEY", "EXAMPLE_SERVICE"), "from-keychain")
        self.assertEqual(run.call_args.args[0], [
            "/usr/bin/security", "find-generic-password", "-a", "kei",
            "-s", "EXAMPLE_SERVICE", "-w",
        ])
        self.assertIs(run.call_args.kwargs["stderr"], subprocess.DEVNULL)

    def test_explicit_account_is_used_for_keychain_lookup(self):
        module = load_module()
        result = subprocess.CompletedProcess([], 0, stdout="from-keychain\n", stderr="")
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(module.subprocess, "run", return_value=result) as run:
                self.assertEqual(module.load_secret("EXAMPLE_API_KEY", "EXAMPLE_SERVICE", "other"), "from-keychain")
        self.assertEqual(run.call_args.args[0][3], "other")

    def test_main_injects_secret_only_into_child_environment(self):
        module = load_module()
        with mock.patch.object(module.sys, "argv", [
            "keychain-env-exec", "EXAMPLE_API_KEY", "EXAMPLE_SERVICE", "--", "/usr/bin/true",
        ]):
            with mock.patch.object(module, "load_secret", return_value="secret-value"):
                with mock.patch.object(module.os, "execvpe", side_effect=RuntimeError("captured")) as execute:
                    with self.assertRaisesRegex(RuntimeError, "captured"):
                        module.main()
        command, argv, child_env = execute.call_args.args
        self.assertEqual(command, "/usr/bin/true")
        self.assertEqual(argv, ["/usr/bin/true"])
        self.assertEqual(child_env["EXAMPLE_API_KEY"], "secret-value")


if __name__ == "__main__":
    unittest.main()
