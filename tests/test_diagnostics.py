from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from pix2tex_app.diagnostics import export_diagnostics_archive


class DiagnosticsTests(unittest.TestCase):
    def test_export_excludes_formula_images_and_redacts_local_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            (data_dir / "logs").mkdir(parents=True)
            (data_dir / "cache").mkdir()
            (data_dir / "history-previews" / "v1").mkdir(parents=True)
            secret_formula = r"\operatorname{privateResearchFormula}"
            (data_dir / "history.json").write_text(
                json.dumps([{"formula": secret_formula, "timestamp": "07-31  12:00"}]),
                encoding="utf-8",
            )
            (data_dir / "cache" / "capture-private.png").write_bytes(b"private image")
            (data_dir / "logs" / "pix2tex-studio.log").write_text(
                r"2026-07-31 ERROR failed at C:\Users\Alice\private\formula.png" + "\n",
                encoding="utf-8",
            )

            output = export_diagnostics_archive(
                data_dir,
                Path(directory) / "diagnostics.zip",
                settings={"history_limit": 100},
                runtime_state={"engine_state": "ready"},
            )
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                combined = "\n".join(
                    archive.read(name).decode("utf-8", errors="replace") for name in names
                )
                payload = json.loads(archive.read("diagnostics.json"))
            self.assertIn("diagnostics.json", names)
            self.assertNotIn(secret_formula, combined)
            self.assertNotIn("private image", combined)
            self.assertNotIn(r"C:\Users\Alice", combined)
            self.assertNotIn("capture-private.png", names)
            self.assertEqual(payload["history"]["count"], 1)
            self.assertFalse(payload["privacy"]["formula_content_included"])
