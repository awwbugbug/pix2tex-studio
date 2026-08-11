from __future__ import annotations

import unittest

from PIL import Image, ImageDraw

from pix2tex_app.worker import prepare_image


class WorkerPreprocessingTests(unittest.TestCase):
    def test_small_content_inside_large_whitespace_is_cropped_then_enhanced(self) -> None:
        image = Image.new("RGB", (470, 240), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((155, 105, 315, 135), fill="black")

        prepared = prepare_image(image, enabled=True)

        self.assertLess(prepared.width, image.width)
        self.assertEqual(prepared.height, 100)

    def test_disabled_enhancement_preserves_original_dimensions(self) -> None:
        image = Image.new("RGB", (470, 240), "white")

        prepared = prepare_image(image, enabled=False)

        self.assertEqual(prepared.size, image.size)


if __name__ == "__main__":
    unittest.main()
