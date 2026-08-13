from __future__ import annotations

import unittest
from pathlib import Path


class InstallerContractTests(unittest.TestCase):
    def _script(self) -> str:
        project_root = Path(__file__).resolve().parent.parent
        return (project_root / "installer" / "Pix2TexStudio.nsi").read_text(encoding="utf-8")

    def test_desktop_shortcut_uses_short_name_and_cleans_legacy_name(self) -> None:
        script = self._script()

        self.assertIn('CreateShortcut "$DESKTOP\\pix2tex.lnk"', script)
        self.assertNotIn('CreateShortcut "$DESKTOP\\Pix2Tex Studio.lnk"', script)
        self.assertIn('Delete "$DESKTOP\\pix2tex.lnk"', script)
        self.assertIn('Delete "$DESKTOP\\Pix2Tex Studio.lnk"', script)

    def test_modern_ui_uses_canonical_installer_and_uninstaller_icon(self) -> None:
        script = self._script()

        include_index = script.index('!include "MUI2.nsh"')
        icon_definition = '!define MUI_ICON "..\\packaging\\pix2tex-studio.ico"'
        unicon_definition = '!define MUI_UNICON "..\\packaging\\pix2tex-studio.ico"'
        self.assertLess(script.index(icon_definition), include_index)
        self.assertLess(script.index(unicon_definition), include_index)


if __name__ == "__main__":
    unittest.main()
