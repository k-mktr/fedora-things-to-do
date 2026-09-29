"""Unit tests for check_freshness.py (no network access needed)."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import check_freshness as cf  # noqa: E402


class TestFlatpakRegex(unittest.TestCase):
    def test_matches_simple_id(self):
        self.assertEqual(
            cf.FLATPAK_RE.findall("flatpak install -y flathub org.videolan.VLC"),
            ["org.videolan.VLC"])

    def test_matches_id_with_hyphen(self):
        # regression: hyphens used to terminate the capture
        self.assertEqual(
            cf.FLATPAK_RE.findall("flatpak install -y flathub io.gitlab.librewolf-community"),
            ["io.gitlab.librewolf-community"])
        self.assertEqual(
            cf.FLATPAK_RE.findall("flatpak install -y flathub org.DolphinEmu.dolphin-emu"),
            ["org.DolphinEmu.dolphin-emu"])

    def test_matches_extra_flags(self):
        self.assertEqual(
            cf.FLATPAK_RE.findall("flatpak install --user -y flathub io.mpv.Mpv"),
            ["io.mpv.Mpv"])

    def test_ignores_non_flatpak_commands(self):
        self.assertEqual(cf.FLATPAK_RE.findall("dnf install -y vlc"), [])


class TestUrlRegexAndNormalize(unittest.TestCase):
    def test_plain_url(self):
        urls = cf.extract_urls({"cmd": "wget -O x https://example.com/file.rpm"})
        self.assertEqual(urls, {"https://example.com/file.rpm"})

    def test_fedora_var_substituted(self):
        urls = cf.extract_urls(
            {"cmd": "wget https://download1.rpmfusion.org/free/fedora/"
                    "rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm"})
        self.assertEqual(
            urls,
            {"https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-44.noarch.rpm"})

    def test_unmapped_shell_var_skipped(self):
        # A URL containing an unmapped $() cannot be checked - must be skipped
        urls = cf.extract_urls(
            {"cmd": "wget https://example.com/$(some -thing)/file.rpm"})
        self.assertEqual(urls, set())

    def test_trailing_punctuation_stripped(self):
        urls = cf.extract_urls({"cmd": "see https://example.com/page."})
        self.assertEqual(urls, {"https://example.com/page"})

    def test_real_nattd_json_yields_resources(self):
        nattd_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "nattd.json")
        with open(nattd_path) as f:
            data = json.load(f)
        ids = cf.extract_flatpak_ids(data)
        urls = cf.extract_urls(data)
        self.assertGreater(len(ids), 50)
        self.assertGreater(len(urls), 20)
        for fid in ids:
            self.assertNotIn(" ", fid)
            self.assertTrue(fid[0].isalpha() or fid[0].isdigit())


class TestClassify(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(cf.classify_status(200, "example.com")[0], "ok")
        self.assertEqual(cf.classify_status(302, "example.com")[0], "ok")

    def test_dead(self):
        self.assertEqual(cf.classify_status(404, "example.com")[0], "dead")
        self.assertEqual(cf.classify_status(410, "example.com")[0], "dead")

    def test_botwall_medium(self):
        self.assertEqual(cf.classify_status(403, "medium.com")[0], "botwall")
        self.assertEqual(cf.classify_status(403, "rpmfusion.org")[0], "botwall")

    def test_403_other_host_is_unknown(self):
        self.assertEqual(cf.classify_status(403, "some-host.example")[0], "unknown")

    def test_5xx_unknown(self):
        self.assertEqual(cf.classify_status(503, "example.com")[0], "unknown")


class TestReport(unittest.TestCase):
    def test_counts_and_lines(self):
        id_refs = {"org.a.A": ["cat/app1"], "org.b.B": ["cat/app2"]}
        id_results = {"org.a.A": ("ok", "x"), "org.b.B": ("dead", "not in appstream")}
        url_results = {
            "https://good.example/f.rpm": ("ok", "HTTP 200"),
            "https://bad.example/f.rpm": ("dead", "HTTP 404"),
            "https://meh.example/f.rpm": ("unknown", "timeout"),
        }
        report, dead, unknown = cf.build_report(id_refs, id_results,
                                                list(url_results), url_results)
        self.assertEqual(dead, 2)
        self.assertEqual(unknown, 1)
        self.assertIn("org.b.B", report)
        self.assertIn("https://bad.example/f.rpm", report)
        self.assertIn("🧟", report)

    def test_healthy_report(self):
        report, dead, unknown = cf.build_report(
            {"org.a.A": ["c/a"]}, {"org.a.A": ("ok", "x")}, [],
            {"https://ok.example": ("ok", "HTTP 200")})
        self.assertEqual((dead, unknown), (0, 0))
        self.assertIn("✅", report)


if __name__ == "__main__":
    unittest.main()
