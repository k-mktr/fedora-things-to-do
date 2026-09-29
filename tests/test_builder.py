"""End-to-end builder tests: generate scripts from representative option sets, validate output."""
import os
import re
import subprocess
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from scripts.builder import build_full_script, check_dependencies, process_all_dependencies  # noqa: E402
from utils.helpers import load_nattd  # noqa: E402

TEMPLATE_PATH = os.path.join(REPO, "template.sh")

def build(options, mode="Verbose"):
    template = open(TEMPLATE_PATH).read()
    return build_full_script(template, options, mode)

class TestBuilderBasics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nattd = load_nattd()

    def test_empty_options_produce_valid_script(self):
        script = build({"system_config": {}, "additional_apps": {}, "customization": {}})
        r = subprocess.run(["bash", "-n", "/dev/stdin"], input=script, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, f"bash -n failed: {r.stderr}")

    def test_full_kitchen_sink_verbose(self):
        options = {
            "system_config": {
                "set_hostname": True,
                "enable_rpmfusion": True,
                "install_multimedia_codecs": True,
                "install_amd_codecs": True,
                "enable_wake_on_lan": True,
            },
            "additional_apps": {
                "development_tools": {"install_docker": {"selected": True}},
                "gaming_emulation": {"install_prism_launcher": {"selected": True}},
                "file_sharing_download": {"install_dropbox": {"selected": True, "installation_type": "DNF"}},
            },
            "customization": {
                "install_nerd_fonts": {"selected": True, "installation_type": "JetBrainsMono"},
                "install_microsoft_fonts": {"selected": True, "installation_type": "core"},
            },
            "custom_script": "echo hi",
            "hostname": "test-box",
        }
        script = build(options, "Verbose")
        r = subprocess.run(["bash", "-n", "/dev/stdin"], input=script, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, f"bash -n failed: {r.stderr}")
        self.assertIn("dnf group install multimedia", script)
        self.assertIn("dnf group install core -y", script)
        self.assertNotIn("@multimedia", script)
        self.assertNotIn("mktr.sbs", script)
        self.assertIn("hostnamectl set-hostname test-box", script)
        self.assertIn("org.prismlauncher.PrismLauncher", script)
        self.assertIn("dnf install -y dropbox nautilus-dropbox", script)
        self.assertIn("rpm --nodigest --nofiledigest -i", script)
        self.assertIn("802-3-ethernet.wake-on-lan magic", script)

    def test_quiet_mode_control_flow_not_redirected(self):
        options = {
            "system_config": {"enable_wake_on_lan": True},
            "additional_apps": {"development_tools": {"install_docker": {"selected": True}}},
        }
        script = build(options, "Quiet")
        for line in script.splitlines():
            stripped = line.strip()
            if re.match(r"^(fi|else|then|elif)\b", stripped):
                self.assertFalse(stripped.endswith("> /dev/null 2>&1"),
                                 f"control-flow line redirected in Quiet mode: {stripped}")
        # docker guard intact
        self.assertIn("if rpm -q docker-ce >/dev/null 2>&1; then", script)

    def test_docker_idempotency_guard(self):
        options = {"additional_apps": {"development_tools": {"install_docker": {"selected": True}}}}
        script = build(options)
        self.assertIn("rpm -q docker-ce", script)
        self.assertIn("groupadd docker 2>/dev/null || true", script)
        self.assertNotIn("\ngroupadd docker\n", script)

    def test_codec_selection_enables_rpmfusion_dependency(self):
        options = {"system_config": {"install_multimedia_codecs": True}}
        updated = check_dependencies(options)
        self.assertTrue(updated["system_config"].get("enable_rpmfusion"))

    def test_app_dependency_notification(self):
        options = {"additional_apps": {
            "file_sharing_download": {"install_dropbox": {"selected": True, "installation_type": "DNF"}}}}
        updated, notes = process_all_dependencies(options, self.nattd)
        self.assertTrue(updated["system_config"].get("enable_rpmfusion"))
        self.assertTrue(any("RPM Fusion" in n for n in notes))

    def test_placeholders_replaced(self):
        script = build({"system_config": {}})
        self.assertNotIn("{{", script)
        self.assertNotIn("{hostname}", script)


class TestFlathubGuard(unittest.TestCase):
    """The generated script must ensure the Flathub remote exists before flatpak installs."""

    @classmethod
    def setUpClass(cls):
        cls.nattd = load_nattd()

    def _script_with_flatpak_app(self):
        options = {"additional_apps": {
            "gaming_emulation": {"install_prism_launcher": {"selected": True}}}}
        return build(options, "Verbose")

    def test_flatpak_install_has_remote_guard(self):
        script = self._script_with_flatpak_app()
        idx = script.find("flatpak install")
        self.assertGreaterEqual(idx, 0, "expected a flatpak install in generated script")
        before = script[:idx]
        self.assertIn("remote-add --if-not-exists flathub", before,
                      "flathub remote not ensured before first flatpak install")


if __name__ == "__main__":
    unittest.main()
