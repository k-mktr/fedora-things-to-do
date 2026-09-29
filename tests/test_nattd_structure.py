"""Structural validation of nattd.json: schema, cross-references, command sanity."""
import json
import re
import os
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_nattd():
    with open(os.path.join(REPO, "nattd.json")) as f:
        return json.load(f)

class TestNattdStructure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_nattd()

    def test_top_level_sections(self):
        for section in ("system_config", "essential_apps", "additional_apps", "customization"):
            self.assertIn(section, self.data, f"missing top-level section: {section}")

    def test_system_config_entries_have_name_command_description(self):
        for key, entry in self.data["system_config"].items():
            if key == "description":
                continue
            with self.subTest(option=key):
                self.assertIsInstance(entry, dict)
                self.assertIn("name", entry)
                self.assertIn("command", entry)
                self.assertIn("description", entry)
                cmds = entry["command"]
                self.assertTrue(isinstance(cmds, (list, str)), f"{key}: command must be str or list")

    def test_dependency_targets_exist(self):
        """All 'dependencies' references must point to existing system_config options."""
        deps_found = []

        def collect(entry):
            if isinstance(entry, dict):
                if "dependencies" in entry:
                    d = entry["dependencies"]
                    deps_found.extend(d if isinstance(d, list) else [d])
                for v in entry.values():
                    collect(v)

        collect(self.data)
        for dep in deps_found:
            self.assertIn(dep, self.data["system_config"],
                          f"dependency '{dep}' not found in system_config")

    def test_installation_types_have_command(self):
        for cat_key, cat in self.data["additional_apps"].items():
            for app_id, app in cat.get("apps", {}).items():
                for it_name, it in app.get("installation_types", {}).items():
                    with self.subTest(app=app_id, install_type=it_name):
                        self.assertIn("command", it,
                                      f"{app_id}/{it_name}: installation type without command")
                        if "dependencies" in it:
                            for dep in (it["dependencies"] if isinstance(it["dependencies"], list)
                                        else [it["dependencies"]]):
                                self.assertIn(dep, self.data["system_config"])

    def test_flatpak_ids_look_sane(self):
        """Flatpak install commands must reference a plausible app id (reverse-domain)."""
        pat = re.compile(r"flatpak install .* ([a-zA-Z0-9._]+\.[a-zA-Z0-9._]+\.[a-zA-Z0-9._]+)")
        for cat_key, cat in self.data["additional_apps"].items():
            for app_id, app in cat.get("apps", {}).items():
                cmds = []
                if "installation_types" in app:
                    cmds += [it.get("command", "") for it in app["installation_types"].values()]
                if "command" in app:
                    c = app["command"]
                    cmds.append(" ".join(c) if isinstance(c, list) else c)
                for cmd in cmds:
                    if "flatpak install" in cmd:
                        self.assertRegex(cmd, pat,
                                         f"{app_id}: flatpak command without reverse-domain id: {cmd}")

    def test_no_dead_shortener_urls(self):
        raw = open(os.path.join(REPO, "nattd.json")).read()
        self.assertNotIn("mktr.sbs", raw)

    def test_essential_apps_have_name_and_description(self):
        for app in self.data["essential_apps"]["apps"]:
            with self.subTest(app=app.get("name")):
                self.assertIn("name", app)
                self.assertIn("description", app)

if __name__ == "__main__":
    unittest.main()
