"""Local-only checks: no credentials, network, signing or release publication."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


loader = importlib.machinery.SourceFileLoader("cutswitch_release_dispatcher", str(Path(__file__).with_name("cutswitch-release")))
spec = importlib.util.spec_from_loader(loader.name, loader)
dispatcher = importlib.util.module_from_spec(spec)
loader.exec_module(dispatcher)


class DispatcherTests(unittest.TestCase):
    def test_launcher_executes_directly_without_host_configuration(self):
        result = subprocess.run([str(Path(__file__).with_name("cutswitch-release"))],
                                text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("doctor", result.stdout)

    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="cutswitch-dispatch-")
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name).resolve()
        self.repo = self.root / "private app"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "remote", "add", "origin", "https://github.com/CutSwitch/cutswitch-app.git"], check=True)
        self.script = self.repo / "scripts/cutswitch/release_mac.py"
        self.script.parent.mkdir(parents=True)
        self.script.write_text("# inert test workflow\n")
        self.script.chmod(0o644)
        self.config = self.root / "host.json"
        self.write_config({"app_repo": str(self.repo)})

    def write_config(self, value):
        self.config.write_text(json.dumps(value))
        self.config.chmod(0o600)

    def test_command_preserves_arguments_and_uses_explicit_config(self):
        args = ["prepare", "--notes", "literal $(touch unwanted) ; `false`"]
        command, cwd = dispatcher.workflow_command(self.config, args)
        self.assertEqual(command[-len(args):], args)
        self.assertEqual(command[:4], [dispatcher.sys.executable, str(self.script), "--config", str(self.config)])
        self.assertEqual(cwd, self.repo)

    def test_qa_namespace_uses_only_the_checked_private_companion(self):
        qa = self.script.with_name("release_qa.py")
        qa.write_text("# inert QA companion\n")
        qa.chmod(0o644)
        command, cwd = dispatcher.workflow_command(self.config, ["qa", "prepare", "--release", "example"])
        self.assertEqual(command, [dispatcher.sys.executable, str(qa), "--config", str(self.config),
                                   "prepare", "--release", "example"])
        self.assertEqual(cwd, self.repo)

    def test_qa_namespace_cannot_follow_a_symlinked_companion(self):
        self.script.with_name("release_qa.py").symlink_to(self.script)
        with self.assertRaises(dispatcher.DispatchError):
            dispatcher.workflow_command(self.config, ["qa", "prepare"])

    def test_ssh_origin_is_supported(self):
        subprocess.run(["git", "-C", str(self.repo), "remote", "set-url", "origin", "git@github.com:CutSwitch/cutswitch-app.git"], check=True)
        dispatcher.workflow_command(self.config, ["doctor"])

    def test_wrong_repository_never_dispatches(self):
        subprocess.run(["git", "-C", str(self.repo), "remote", "set-url", "origin", "https://github.com/CutSwitch/releases.git"], check=True)
        with self.assertRaisesRegex(dispatcher.DispatchError, "origin"):
            dispatcher.workflow_command(self.config, ["doctor"])

    def test_remote_lookalike_is_rejected(self):
        subprocess.run(["git", "-C", str(self.repo), "remote", "set-url", "origin", "https://github.com.example.com/CutSwitch/cutswitch-app.git"], check=True)
        with self.assertRaisesRegex(dispatcher.DispatchError, "origin"):
            dispatcher.workflow_command(self.config, ["doctor"])

    def test_relative_checkout_is_rejected(self):
        self.write_config({"app_repo": "private app"})
        with self.assertRaises(dispatcher.DispatchError):
            dispatcher.workflow_command(self.config, ["doctor"])

    def test_config_symlink_is_rejected(self):
        target = self.root / "target.json"
        self.config.rename(target)
        self.config.symlink_to(target)
        with self.assertRaisesRegex(dispatcher.DispatchError, "regular"):
            dispatcher.workflow_command(self.config, ["doctor"])

    def test_shared_config_is_rejected(self):
        self.config.chmod(0o644)
        with self.assertRaisesRegex(dispatcher.DispatchError, "owner-only"):
            dispatcher.workflow_command(self.config, ["doctor"])

    def test_oversized_config_is_rejected(self):
        self.config.write_text(" " * (64 * 1024 + 1))
        with self.assertRaisesRegex(dispatcher.DispatchError, "too large"):
            dispatcher.workflow_command(self.config, ["doctor"])

    def test_workflow_symlink_is_rejected(self):
        target = self.root / "untrusted.py"
        self.script.rename(target)
        self.script.symlink_to(target)
        with self.assertRaisesRegex(dispatcher.DispatchError, "regular"):
            dispatcher.workflow_command(self.config, ["doctor"])

    def test_group_writable_workflow_is_rejected(self):
        self.script.chmod(0o664)
        with self.assertRaisesRegex(dispatcher.DispatchError, "write access"):
            dispatcher.workflow_command(self.config, ["doctor"])

    def test_parent_symlink_cannot_redirect_workflow(self):
        outside = self.root / "redirected"
        self.script.parent.rename(outside)
        (self.repo / "scripts/cutswitch").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(dispatcher.DispatchError, "escaped"):
            dispatcher.workflow_command(self.config, ["doctor"])

    def test_actual_child_exit_and_arguments_are_forwarded_without_a_shell(self):
        self.script.write_text("import os,sys,json\nprint(json.dumps({'cwd':os.getcwd(),'args':sys.argv[1:]}))\nraise SystemExit(7)\n")
        literal = "$(touch unexpected); `false`"
        result = subprocess.run([dispatcher.sys.executable, str(Path(__file__).with_name('cutswitch-release')), '--config', str(self.config), 'doctor', literal], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 7)
        observed = json.loads(result.stdout)
        self.assertEqual(observed['cwd'], str(self.repo))
        self.assertEqual(observed['args'], ['--config',str(self.config),'doctor',literal])
        self.assertFalse((self.repo/'unexpected').exists())

    def test_invalid_config_is_reported_without_contents(self):
        self.config.write_text("not-json-test-value")
        with self.assertRaisesRegex(dispatcher.DispatchError, "app_repo"):
            dispatcher.workflow_command(self.config, ["doctor"])


if __name__ == "__main__":
    unittest.main()
