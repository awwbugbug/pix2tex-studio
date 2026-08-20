from __future__ import annotations

import unittest
from pathlib import Path


class PackagingContractTests(unittest.TestCase):
    def test_worker_collects_transformers_dynamic_configuration_family(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        spec = (project_root / "packaging" / "Pix2TexStudio.spec").read_text(
            encoding="utf-8"
        )
        self.assertIn("transformers_configuration_hiddenimports", spec)
        self.assertIn('if ".configuration_" in name', spec)
        self.assertIn("hiddenimports=worker_hiddenimports", spec)

    def test_gui_analysis_does_not_collect_worker_model_registry(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        spec = (project_root / "packaging" / "Pix2TexStudio.spec").read_text(
            encoding="utf-8"
        )
        self.assertIn("hiddenimports=main_hiddenimports", spec)
        self.assertIn("hiddenimports=worker_hiddenimports", spec)


if __name__ == "__main__":
    unittest.main()
