from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pix2tex_app.evaluation import load_manifest, normalize_latex


class EvaluationTests(unittest.TestCase):
    def test_normalization_removes_wrappers_layout_helpers_and_whitespace(self) -> None:
        self.assertEqual(normalize_latex(r"$$ \left( x + 1 \right) $$"), "(x+1)")

    def test_manifest_resolves_images_and_rejects_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "formula.png"
            image.write_bytes(b"not-decoded-by-manifest-loader")
            item = {
                "id": "case-001",
                "image": "formula.png",
                "ground_truth": "x+1",
                "category": "printed",
            }
            manifest = root / "manifest.jsonl"
            manifest.write_text(json.dumps(item) + "\n", encoding="utf-8")

            cases = load_manifest(manifest)

            self.assertEqual(cases[0].image, image.resolve())
            manifest.write_text(json.dumps(item) + "\n" + json.dumps(item) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate case id"):
                load_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
