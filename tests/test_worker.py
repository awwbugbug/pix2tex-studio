from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

from pix2tex_app.worker import (
    _background_is_dark,
    _crop_to_content,
    _model_dir,
    _write_worker_config,
    normalize_prediction,
    prepare_for_model,
)


class NormalizePredictionTests(unittest.TestCase):
    def test_strips_surrounding_whitespace(self) -> None:
        self.assertEqual(normalize_prediction("  E = m c ^ { 2 } \n"), "E = m c ^ { 2 }")

    def test_preserves_inter_token_spaces(self) -> None:
        # Spaces terminate LaTeX command names and must be kept.
        raw = r"\displaystyle \sum _ { n } x"
        self.assertEqual(normalize_prediction(raw), raw)

    def test_drops_limits_from_stacked_operators(self) -> None:
        self.assertEqual(
            normalize_prediction(r"\int \limits _ { b } ^ { a }"),
            r"\int _ { b } ^ { a }",
        )
        self.assertEqual(
            normalize_prediction(r"\sum \nolimits _ { i } x"),
            r"\sum _ { i } x",
        )

    def test_keeps_commands_that_merely_start_with_limits(self) -> None:
        # \limsup must not be mangled by the \limits removal.
        raw = r"\limsup _ { n } a _ { n }"
        self.assertEqual(normalize_prediction(raw), raw)


class ModelDirTests(unittest.TestCase):
    def test_env_override_wins(self) -> None:
        with mock.patch.dict(os.environ, {"PIX2TEX_UNIMERNET_MODEL_DIR": r"X:/custom/model"}):
            self.assertEqual(_model_dir(), Path(r"X:/custom/model"))

    def test_default_is_package_local_models_dir(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            resolved = _model_dir()
        self.assertEqual(resolved.name, "unimernet_tiny")
        self.assertEqual(resolved.parent.name, "models")


class WriteWorkerConfigTests(unittest.TestCase):
    def test_raises_when_no_weights_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                _write_worker_config(Path(tmp))

    def test_writes_config_referencing_model_dir_and_weights(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            model_dir = Path(tmp)
            weights = model_dir / "unimernet_tiny.pth"
            weights.write_bytes(b"")

            config_path = _write_worker_config(model_dir)

            self.assertTrue(config_path.is_file())
            text = config_path.read_text(encoding="utf-8")
            self.assertIn(model_dir.as_posix(), text)
            self.assertIn(weights.as_posix(), text)
            self.assertIn("arch: unimernet", text)


class DarkBackgroundInversionTests(unittest.TestCase):
    def test_dark_background_is_detected(self) -> None:
        image = Image.new("RGB", (40, 20), "black")
        self.assertTrue(_background_is_dark(image))

    def test_light_background_is_not_dark(self) -> None:
        image = Image.new("RGB", (40, 20), "white")
        self.assertFalse(_background_is_dark(image))

    def test_prepare_inverts_dark_capture(self) -> None:
        # Black background with a white mark; after inversion the background
        # becomes white and the mark becomes black.
        image = Image.new("RGB", (40, 20), "black")
        image.putpixel((5, 5), (255, 255, 255))
        prepared = prepare_for_model(image)
        self.assertEqual(prepared.getpixel((0, 0)), (255, 255, 255))
        self.assertEqual(prepared.getpixel((5, 5)), (0, 0, 0))

    def test_prepare_leaves_light_capture_unchanged(self) -> None:
        image = Image.new("RGB", (40, 20), "white")
        image.putpixel((5, 5), (0, 0, 0))
        prepared = prepare_for_model(image)
        self.assertEqual(prepared.getpixel((0, 0)), (255, 255, 255))
        self.assertEqual(prepared.getpixel((5, 5)), (0, 0, 0))


class CropToContentTests(unittest.TestCase):
    def test_crops_small_mark_in_large_whitespace(self) -> None:
        image = Image.new("RGB", (400, 300), "white")
        for x in range(190, 210):
            for y in range(145, 155):
                image.putpixel((x, y), (0, 0, 0))
        cropped = _crop_to_content(image)
        self.assertLess(cropped.width, image.width)
        self.assertLess(cropped.height, image.height)
        # content (20x10) plus a symmetric margin on each side
        self.assertGreaterEqual(cropped.width, 20)
        self.assertGreaterEqual(cropped.height, 10)

    def test_blank_image_is_unchanged(self) -> None:
        image = Image.new("RGB", (120, 80), "white")
        self.assertEqual(_crop_to_content(image).size, image.size)


if __name__ == "__main__":
    unittest.main()
