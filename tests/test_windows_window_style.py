from __future__ import annotations

import unittest
from pathlib import Path

from pix2tex_app.__main__ import _application_package_root, _windows_style_with_system_behaviors


class WindowsWindowStyleTests(unittest.TestCase):
    def test_frozen_resources_resolve_inside_packaged_module_directory(self) -> None:
        root = _application_package_root(frozen=True, bundle_dir=r"C:\bundle\_internal")
        self.assertEqual(root, Path(r"C:\bundle\_internal\pix2tex_app"))

    def test_preserves_existing_style_and_adds_system_window_behaviors(self) -> None:
        frameless_qt_style = 0x96000000

        updated = _windows_style_with_system_behaviors(frameless_qt_style)

        self.assertEqual(updated & frameless_qt_style, frameless_qt_style)
        self.assertTrue(updated & 0x00010000)  # WS_MAXIMIZEBOX
        self.assertTrue(updated & 0x00020000)  # WS_MINIMIZEBOX
        self.assertTrue(updated & 0x00040000)  # WS_THICKFRAME
        self.assertTrue(updated & 0x00080000)  # WS_SYSMENU
        self.assertFalse(updated & 0x00C00000)  # keep the native caption hidden


if __name__ == "__main__":
    unittest.main()
