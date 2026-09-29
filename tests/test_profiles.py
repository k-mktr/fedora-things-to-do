"""Tests for profiles: overlay building, full expansion, session sync, nattd consistency."""
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import profiles  # noqa: E402
from utils.helpers import load_nattd  # noqa: E402


class TestProfilesConsistency(unittest.TestCase):
    """Every id referenced by any profile must exist in nattd.json."""

    @classmethod
    def setUpClass(cls):
        cls.nattd = load_nattd()

    def test_profile_ids_exist_in_nattd(self):
        for name, profile in profiles.PROFILES.items():
            with self.subTest(profile=name):
                for opt in profile.get("system_config", []):
                    self.assertIn(opt, self.nattd["system_config"], f"{name}: {opt}")
                essential_names = [a["name"] for a in self.nattd["essential_apps"]["apps"]]
                for app in profile.get("essential_apps", []):
                    self.assertIn(app, essential_names, f"{name}: {app}")
                for category, apps in profile.get("additional_apps", {}).items():
                    self.assertIn(category, self.nattd["additional_apps"], f"{name}: {category}")
                    cat_apps = self.nattd["additional_apps"][category]["apps"]
                    for item in apps:
                        app_id = item["id"] if isinstance(item, dict) else item
                        self.assertIn(app_id, cat_apps, f"{name}: {category}/{app_id}")
                        if isinstance(item, dict) and item.get("installation_type"):
                            self.assertIn(item["installation_type"],
                                          cat_apps[app_id]["installation_types"],
                                          f"{name}: {app_id} type {item['installation_type']}")
                for item in profile.get("customization", []):
                    app_id = item["id"] if isinstance(item, dict) else item
                    self.assertIn(app_id, self.nattd["customization"]["apps"], f"{name}: {app_id}")
                    if isinstance(item, dict) and item.get("installation_type"):
                        self.assertIn(item["installation_type"],
                                      self.nattd["customization"]["apps"][app_id]["installation_types"])


class TestProfileOverlay(unittest.TestCase):

    def test_overlay_shape(self):
        profile = profiles.PROFILES["Recommended"]
        overlay = profiles.build_profile_options(profile)
        self.assertEqual(overlay["system_config"].get("configure_dnf"), True)
        self.assertEqual(overlay["essential_apps"].get("mc"), True)
        vivaldi = overlay["additional_apps"]["internet_communication"]["install_vivaldi"]
        self.assertEqual(vivaldi, {"selected": True})
        fonts = overlay["customization"]["install_microsoft_fonts"]
        self.assertEqual(fonts, {"selected": True, "installation_type": "core"})
        # items not in the profile must NOT be in the overlay
        self.assertNotIn("install_steam", overlay["additional_apps"].get("gaming_emulation", {}))


class TestFullExpansion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nattd = load_nattd()

    def test_expansion_covers_every_entry(self):
        overlay = profiles.build_profile_options(profiles.PROFILES["Recommended"])
        full = profiles.build_full_options(overlay, self.nattd)
        # every system_config option present as bool
        for opt, entry in self.nattd["system_config"].items():
            if isinstance(entry, dict) and "command" in entry:
                self.assertIn(opt, full["system_config"])
                self.assertIsInstance(full["system_config"][opt], bool)
        # every essential app present
        for app in self.nattd["essential_apps"]["apps"]:
            self.assertIn(app["name"], full["essential_apps"])
        # every additional app present with selected flag
        for category, cat in self.nattd["additional_apps"].items():
            for app_id in cat["apps"]:
                self.assertIn(app_id, full["additional_apps"][category])
        # profile selections are on
        self.assertTrue(full["system_config"]["configure_dnf"])
        self.assertTrue(full["additional_apps"]["internet_communication"]["install_vivaldi"]["selected"])
        self.assertTrue(full["customization"]["install_microsoft_fonts"]["selected"])
        # non-profile selections are off
        self.assertFalse(full["additional_apps"]["gaming_emulation"]["install_steam"]["selected"])
        self.assertFalse(full["system_config"]["install_docker"] if "install_docker" in full["system_config"] else False)

    def test_unknown_overlay_ids_are_ignored(self):
        overlay = {"additional_apps": {"gaming_emulation": {"install_ghost_app": {"selected": True}}}}
        full = profiles.build_full_options(overlay, self.nattd)
        self.assertNotIn("install_ghost_app", full["additional_apps"]["gaming_emulation"])

    def test_installation_type_falls_back_to_first(self):
        overlay = {"additional_apps": {"media_graphics": {"install_gimp": {"selected": True}}}}
        full = profiles.build_full_options(overlay, self.nattd)
        gimp = full["additional_apps"]["media_graphics"]["install_gimp"]
        self.assertTrue(gimp["selected"])
        self.assertIn(gimp["installation_type"], self.nattd["additional_apps"]["media_graphics"]["apps"]["install_gimp"]["installation_types"])

    def test_roundtrip_through_builder(self):
        """A full expanded profile must build a valid, complete script."""
        from scripts.builder import build_full_script
        overlay = profiles.build_profile_options(profiles.PROFILES["Recommended"])
        full = profiles.build_full_options(overlay, self.nattd)
        full["hostname"] = "profiled-box"
        template = open(os.path.join(REPO, "template.sh")).read()
        script = build_full_script(template, full, "Verbose")
        r = __import__("subprocess").run(["bash", "-n", "/dev/stdin"], input=script,
                                         capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Installing Vivaldi", script)
        self.assertIn("#   - Vivaldi", script)  # header summary
        self.assertNotIn("Installing Steam", script)


class TestSessionSync(unittest.TestCase):
    def test_sync_sets_widget_keys(self):
        import streamlit as st
        options = {
            "system_config": {"enable_rpmfusion": True, "install_ssh": False},
            "essential_apps": {"mc": True},
            "additional_apps": {
                "media_graphics": {"install_gimp": {"selected": True, "installation_type": "Flatpak"}},
            },
            "customization": {"install_tela_icon_theme": True},
        }
        profiles.sync_session_widgets(options)
        self.assertTrue(st.session_state["system_config_enable_rpmfusion"])
        self.assertFalse(st.session_state["system_config_install_ssh"])
        self.assertTrue(st.session_state["essential_app_mc"])
        self.assertTrue(st.session_state["app_media_graphics_install_gimp"])
        self.assertEqual(st.session_state["media_graphics_install_gimp_install_type"], "Flatpak")
        self.assertTrue(st.session_state["customization_install_tela_icon_theme"])


if __name__ == "__main__":
    unittest.main()
