"""Tests for script robustness features: failure tracking, metadata header, docker safety."""
import os
import re
import subprocess
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from scripts.builder import build_full_script  # noqa: E402

TEMPLATE_PATH = os.path.join(REPO, "template.sh")

def build(options, mode="Verbose"):
    template = open(TEMPLATE_PATH).read()
    return build_full_script(template, options, mode)

class TestScriptRobustness(unittest.TestCase):

    def _kitchen(self):
        return {
            "system_config": {
                "set_hostname": True,
                "enable_rpmfusion": True,
                "install_multimedia_codecs": True,
                "enable_wake_on_lan": True,
            },
            "additional_apps": {
                "development_tools": {"install_docker": {"selected": True}},
                "gaming_emulation": {"install_prism_launcher": {"selected": True}},
            },
            "customization": {
                "install_microsoft_fonts": {"selected": True, "installation_type": "core"},
            },
            "custom_script": "echo hi",
        }

    def test_failure_tracking_present(self):
        script = build(self._kitchen())
        self.assertIn("FAILURES=0", script)
        self.assertIn("trap 'FAILURES=$((FAILURES+1))", script)
        self.assertIn('log_message "=== NATTD run finished with $FAILURES failed command(s) ==="', script)
        # old unconditional success message is gone
        self.assertNotIn('color_echo "green" "All steps completed. Enjoy!"', script)

    def test_metadata_header(self):
        script = build(self._kitchen(), "Quiet")
        self.assertRegex(script, r"# Generation date: \d{4}-\d{2}-\d{2} \d{2}:\d{2}")
        self.assertIn("# Output mode: Quiet", script)
        self.assertIn("#   - Multimedia Codecs", script)
        self.assertIn("#   - Docker", script)
        self.assertIn("#   - Microsoft Fonts (core)", script)
        self.assertIn("#   - Enable Wake-on-LAN", script)
        self.assertNotIn("{generation_date}", script)
        self.assertNotIn("{output_mode}", script)

    def test_header_empty_selection(self):
        script = build({"system_config": {}})
        self.assertIn("#   (nothing selected - system upgrade only)", script)

    def test_docker_home_destruction_removed(self):
        script = build(self._kitchen())
        self.assertNotIn("rm -rf $ACTUAL_HOME/.docker", script)
        # pre-remove of conflicting packages tolerates absence (no ERR trap trip)
        self.assertIn("docker-engine --noautoremove || true", script)

    def test_generated_script_still_valid_bash(self):
        for mode in ("Verbose", "Quiet"):
            with self.subTest(mode=mode):
                script = build(self._kitchen(), mode)
                r = subprocess.run(["bash", "-n", "/dev/stdin"], input=script,
                                   capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, f"bash -n failed ({mode}): {r.stderr}")

    def test_log_ordering_no_use_before_definition(self):
        script = build(self._kitchen())
        trap_idx = script.find("trap 'FAILURES")
        logdef_idx = script.find("log_message() {")
        self.assertGreater(trap_idx, logdef_idx,
                           "trap uses log_message before its definition")

if __name__ == "__main__":
    unittest.main()
