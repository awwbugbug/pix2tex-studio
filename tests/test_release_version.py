from __future__ import annotations

import re
import unittest
from pathlib import Path


class ReleaseVersionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_root = Path(__file__).resolve().parents[1]

    def _text(self, relative: str) -> str:
        return (self.project_root / relative).read_text(encoding="utf-8")

    def test_python_package_is_the_2_0_rc2_candidate(self) -> None:
        pyproject = self._text("pyproject.toml")
        project_section = pyproject.split("[project]", 1)[1].split("[", 1)[0]
        match = re.search(r'^version\s*=\s*"([^"]+)"', project_section, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "2.0.0rc2")

    def test_windows_resources_and_installer_use_the_same_version(self) -> None:
        version_info = self._text("packaging/version_info.txt")
        installer = self._text("installer/Pix2TexStudio.nsi")
        self.assertIn("filevers=(2, 0, 0, 2)", version_info)
        self.assertIn("prodvers=(2, 0, 0, 2)", version_info)
        self.assertEqual(version_info.count("2.0.0-rc2"), 2)
        self.assertIn('!define APP_VERSION "2.0.0-rc2"', installer)

    def test_release_manifest_and_notes_are_versioned_for_2_0_rc2(self) -> None:
        manifest = self._text("scripts/create-release-manifest.ps1")
        self.assertIn("Pix2TexStudio-2.0.0-rc2-Setup.exe", manifest)
        self.assertIn("version = '2.0.0rc2'", manifest)
        self.assertTrue(
            (self.project_root / "docs/release/RELEASE_NOTES_2.0.0rc2.md").is_file()
        )


if __name__ == "__main__":
    unittest.main()
