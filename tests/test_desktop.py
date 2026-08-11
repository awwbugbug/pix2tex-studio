from __future__ import annotations

import unittest
import uuid

from PySide6.QtCore import QCoreApplication

from pix2tex_app.desktop import SingleInstanceGuard


class DesktopIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_second_guard_detects_primary_and_requests_activation(self) -> None:
        name = f"Reasonix.Pix2TexStudio.test.{uuid.uuid4().hex}"
        primary = SingleInstanceGuard(self.app, name)
        activations: list[bool] = []
        primary.activationRequested.connect(lambda: activations.append(True))
        secondary = SingleInstanceGuard(self.app, name)
        try:
            QCoreApplication.processEvents()
            self.assertTrue(primary.is_primary)
            self.assertFalse(secondary.is_primary)
            self.assertEqual(activations, [True])
        finally:
            secondary.close()
            primary.close()


if __name__ == "__main__":
    unittest.main()
