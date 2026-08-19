from __future__ import annotations

import unittest
from pathlib import Path


class InstallerContractTests(unittest.TestCase):
    def _script(self) -> str:
        project_root = Path(__file__).resolve().parent.parent
        return (project_root / "installer" / "Pix2TexStudio.nsi").read_text(encoding="utf-8")

    def test_desktop_shortcut_uses_short_name_and_cleans_legacy_name(self) -> None:
        script = self._script()

        expected_shortcut = (
            'CreateShortcut "$DESKTOP\\pix2tex.lnk" "$INSTDIR\\${APP_EXE}" '
            '"" "$INSTDIR\\pix2tex.ico" 0'
        )
        self.assertIn('File /oname=pix2tex.ico "..\\packaging\\pix2tex-studio.ico"', script)
        self.assertIn(expected_shortcut, script)
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

    def test_release_test_mode_isolated_from_user_shell_and_registry(self) -> None:
        script = self._script()
        self.assertEqual(script.count('${GetOptions} $R0 "/RELEASETEST" $R1'), 2)
        self.assertEqual(script.count('${If} $ReleaseTest != 1'), 2)
        self.assertIn('RMDir /r "$INSTDIR"', script)


if __name__ == "__main__":
    unittest.main()
