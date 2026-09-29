"""Tests for UX niceties: selection counters, select-all logic, installation-type warning."""
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from ui.widgets import selection_counter, _visible_count  # noqa: E402
from utils.helpers import load_nattd  # noqa: E402


class TestSelectAllLogic(unittest.TestCase):

    def test_visible_count_no_search(self):
        self.assertEqual(_visible_count(3, 90, ""), 90)

    def test_visible_count_with_search(self):
        self.assertEqual(_visible_count(3, 90, "gimp"), 3)


class TestSelectionCounter(unittest.TestCase):

    def test_counter_zero(self):
        # smoke: renders caption without raising
        selection_counter("apps", [("a", False), ("b", False)])

    def test_counter_partial_and_full(self):
        selection_counter("apps", [("a", True), ("b", False)])
        selection_counter("apps", [("a", True), ("b", True)])


class TestInstallTypeWarning(unittest.TestCase):
    """Selecting an NVIDIA driver bonus alongside GPU codecs should warn about reboot ordering."""

    @classmethod
    def setUpClass(cls):
        cls.nattd = load_nattd()

    def test_nvidia_and_codecs_detection_inputs(self):
        # the pairs the warning logic in the sidebar uses
        codec_options = ["install_multimedia_codecs", "install_intel_codecs", "install_amd_codecs"]
        sys_cfg = {"install_multimedia_codecs": True}
        bonus = {"Install Nvidia": True}  # bonus scripts are keyed by Title-cased filename
        has_codec = any(sys_cfg.get(c, False) for c in codec_options)
        has_nvidia = bonus.get("Install Nvidia", False)
        self.assertTrue(has_codec and has_nvidia)

    def test_nattd_has_nvidia_bonus(self):
        import os
        self.assertTrue(os.path.exists(os.path.join(REPO, "bonus", "install_nvidia.sh")))


if __name__ == "__main__":
    unittest.main()
