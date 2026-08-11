from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")

from PySide6.QtGui import QImage
from PySide6.QtTest import QSignalSpy
from PySide6.QtWebEngineQuick import QtWebEngineQuick
from PySide6.QtWidgets import QApplication

from pix2tex_app.history_preview import HistoryPreviewRenderer

QtWebEngineQuick.initialize()


class HistoryPreviewRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_renderer_creates_transparent_light_and_dark_previews(self) -> None:
        mathjax_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "pix2tex_app"
            / "ui"
            / "assets"
            / "MathJax.js"
        )
        with tempfile.TemporaryDirectory() as directory:
            renderer = HistoryPreviewRenderer(Path(directory), mathjax_path)
            rendered = QSignalSpy(renderer.rendered)
            renderer.request(r"\begin{bmatrix}a&b\\c&d\end{bmatrix}")
            self.assertTrue(rendered.wait(7000), "MathJax preview did not finish")

            _formula, light_path, dark_path, width, height = rendered.at(0)
            light = QImage(light_path)
            dark = QImage(dark_path)
            self.assertFalse(light.isNull())
            self.assertFalse(dark.isNull())
            self.assertEqual((light.width(), light.height()), (width, height))
            self.assertEqual((dark.width(), dark.height()), (width, height))
            self.assertEqual(light.pixelColor(0, 0).alpha(), 0)
            self.assertEqual(dark.pixelColor(0, 0).alpha(), 0)
            self.assertTrue(
                any(light.pixelColor(x, y).alpha() > 0 for y in range(height) for x in range(width)),
                "preview contained no rendered formula pixels",
            )
            self.assertEqual(renderer.prune([]), 2)
            self.assertFalse(Path(light_path).exists())
            self.assertFalse(Path(dark_path).exists())
            renderer.close()


if __name__ == "__main__":
    unittest.main()
