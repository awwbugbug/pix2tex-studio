from __future__ import annotations

import unittest

from PySide6.QtGui import QGuiApplication

from pix2tex_app.app_icon import render_app_icon


class AppIconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_icon_has_transparent_corners_and_dark_body(self) -> None:
        image = render_app_icon(64).toImage()

        self.assertEqual(image.size().width(), 64)
        self.assertEqual(image.size().height(), 64)
        self.assertEqual(image.pixelColor(0, 0).alpha(), 0)
        self.assertEqual(image.pixelColor(56, 32).name(), "#1b1d20")

    def test_rejects_non_positive_size(self) -> None:
        with self.assertRaises(ValueError):
            render_app_icon(0)


if __name__ == "__main__":
    unittest.main()
