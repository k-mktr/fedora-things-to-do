"""Tests for the AI Coding Agents category, Node.js dependency, and generalized dependency resolution."""
import os
import subprocess
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from scripts.builder import build_full_script, process_all_dependencies  # noqa: E402
from utils.helpers import load_nattd  # noqa: E402

TEMPLATE_PATH = os.path.join(REPO, "template.sh")


def build(options, mode="Verbose"):
    template = open(TEMPLATE_PATH).read()
    return build_full_script(template, options, mode)


class TestAiAgentsCategory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nattd = load_nattd()
        cls.cat = cls.nattd["additional_apps"]["ai_agents"]

    def test_category_present_with_expected_apps(self):
        expected = [
            "install_hermes_agent", "install_claude_code", "install_codex_cli",
            "install_opencode", "install_gemini_cli", "install_qwen_code",
            "install_aider", "install_goose", "install_crush", "install_droid",
            "install_amp", "install_pi_agent", "install_unsloth_studio",
        ]
        for app_id in expected:
            self.assertIn(app_id, self.cat["apps"], f"missing agent: {app_id}")

    def test_install_commands_have_verified_urls(self):
        expected_urls = {
            "install_hermes_agent": "hermes-agent.nousresearch.com/install.sh",
            "install_claude_code": "claude.ai/install.sh",
            "install_codex_cli": "chatgpt.com/codex/install.sh",
            "install_opencode": "opencode.ai/install",
            "install_aider": "aider.chat/install.sh",
            "install_droid": "app.factory.ai/cli",
            "install_amp": "ampcode.com/install.sh",
            "install_unsloth_studio": "unsloth.ai/install.sh",
        }
        for app_id, url in expected_urls.items():
            app = self.cat["apps"][app_id]
            cmds = []
            if "installation_types" in app:
                cmds += [it.get("command", "") for it in app["installation_types"].values()]
            if "command" in app:
                c = app["command"]
                cmds.append(" ".join(c) if isinstance(c, list) else c)
            joined = " ".join(c if isinstance(c, str) else " ".join(c) for c in cmds)
            self.assertIn(url, joined, f"{app_id}: expected {url}")

    def test_nodejs_system_option_exists(self):
        entry = self.nattd["system_config"]["install_nodejs"]
        self.assertIn("dnf install -y nodejs npm", " ".join(entry["command"]))

    def test_npm_agents_declare_nodejs_dependency(self):
        for app_id in ("install_gemini_cli", "install_qwen_code", "install_crush", "install_pi_agent"):
            deps = self.cat["apps"][app_id]["dependencies"]
            self.assertIn("install_nodejs", deps, f"{app_id} missing install_nodejs dependency")
        claude_npm = self.cat["apps"]["install_claude_code"]["installation_types"]["npm"]
        self.assertIn("install_nodejs", claude_npm["dependencies"])

    def test_nodejs_dependency_resolution(self):
        options = {"additional_apps": {
            "ai_agents": {"install_gemini_cli": {"selected": True, "installation_type": None}}}}
        updated, notifications = process_all_dependencies(options, self.nattd)
        self.assertTrue(updated["system_config"].get("install_nodejs"))
        self.assertTrue(any("Node.js" in n for n in notifications))

    def test_rpmfusion_dependency_still_works(self):
        options = {"additional_apps": {
            "file_sharing_download": {"install_dropbox": {"selected": True, "installation_type": "DNF"}}}}
        updated, notifications = process_all_dependencies(options, self.nattd)
        self.assertTrue(updated["system_config"].get("enable_rpmfusion"))

    def test_kitchen_sink_build(self):
        options = {
            "system_config": {"install_nodejs": True},
            "additional_apps": {
                "ai_agents": {
                    "install_hermes_agent": {"selected": True},
                    "install_claude_code": {"selected": True, "installation_type": "Native"},
                    "install_gemini_cli": {"selected": True, "installation_type": None},
                },
            },
        }
        script = build(options, "Verbose")
        r = subprocess.run(["bash", "-n", "/dev/stdin"], input=script, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("hermes-agent.nousresearch.com/install.sh", script)
        self.assertIn("claude.ai/install.sh", script)
        self.assertIn("@google/gemini-cli", script)
        self.assertIn("dnf install -y nodejs npm", script)
        self.assertIn("#   - Hermes Agent", script)
        self.assertIn("#   - Gemini CLI", script)

    def test_quiet_mode_still_valid(self):
        options = {"additional_apps": {
            "ai_agents": {"install_codex_cli": {"selected": True}}}}
        script = build(options, "Quiet")
        r = subprocess.run(["bash", "-n", "/dev/stdin"], input=script, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("chatgpt.com/codex/install.sh", script)


if __name__ == "__main__":
    unittest.main()
