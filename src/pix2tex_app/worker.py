from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def _formula_content_bbox(image: Any) -> tuple[int, int, int, int] | None:
    """Estimate formula bounds while ignoring a decorative border touching the image edge."""
    from collections import Counter

    import cv2
    import numpy as np
    from PIL import Image

    rgb_image = image.convert("RGB")
    sample_width = min(128, rgb_image.width)
    sample_height = min(128, rgb_image.height)
    sample = rgb_image.resize((sample_width, sample_height), Image.Resampling.NEAREST)
    background = Counter(sample.getdata()).most_common(1)[0][0]
    pixels = np.asarray(rgb_image, dtype=np.int16)
    background_pixel = np.asarray(background, dtype=np.int16)
    difference = np.max(np.abs(pixels - background_pixel), axis=2)
    mask = (difference >= 24).astype(np.uint8)
    count, _labels, stats, _centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    boxes: list[tuple[int, int, int, int]] = []
    image_area = rgb_image.width * rgb_image.height
    for index in range(1, count):
        x, y, width, height, area = (int(value) for value in stats[index])
        if area < max(2, int(image_area * 0.00001)):
            continue
        touches_edge = x == 0 or y == 0 or x + width == rgb_image.width or y + height == rgb_image.height
        spans_frame = width >= rgb_image.width * 0.9 or height >= rgb_image.height * 0.9
        if touches_edge and spans_frame:
            continue
        boxes.append((x, y, x + width, y + height))
    if not boxes:
        return None
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def prepare_image(image: Any, *, enabled: bool) -> Any:
    """Crop whitespace around small formula content, then apply the existing enhancement."""
    from PIL import Image, ImageEnhance

    prepared = image.convert("RGB")
    if not enabled:
        return prepared
    bbox = _formula_content_bbox(prepared)
    if bbox:
        left, top, right, bottom = bbox
        content_width = right - left
        content_height = bottom - top
        margin = max(8, round(min(content_width, content_height) * 0.4))
        expanded = (
            max(0, left - margin),
            max(0, top - margin),
            min(prepared.width, right + margin),
            min(prepared.height, bottom + margin),
        )
        if expanded != (0, 0, prepared.width, prepared.height):
            prepared = prepared.crop(expanded)
    width, height = prepared.size
    if width < 100 or height < 100:
        scale = max(100 / max(width, 1), 100 / max(height, 1))
        prepared = prepared.resize(
            (int(width * scale), int(height * scale)),
            Image.Resampling.LANCZOS,
        )
        prepared = ImageEnhance.Contrast(prepared).enhance(1.5)
        prepared = ImageEnhance.Sharpness(prepared).enhance(1.5)
    return prepared


def main() -> int:
    os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")
    started = time.perf_counter()
    try:
        from PIL import Image
        import pix2tex.cli as cli
        from pix2tex.cli import LatexOCR

        cli.clipboard.copy = lambda _value: None
        model = LatexOCR()
    except Exception as exc:  # pragma: no cover - exercised by process smoke tests
        emit({"type": "error", "message": f"模型加载失败：{exc}"})
        traceback.print_exc(file=sys.stderr)
        return 1

    emit({"type": "ready", "seconds": time.perf_counter() - started})

    for raw_line in sys.stdin:
        try:
            command = json.loads(raw_line)
            command_type = command.get("type")
            if command_type == "shutdown":
                return 0
            if command_type != "predict":
                continue

            image_path = Path(str(command.get("path", "")))
            infer_started = time.perf_counter()
            with Image.open(image_path) as image:
                image = prepare_image(
                    image,
                    enabled=bool(command.get("small_image_enhancement", True)),
                )
                model.args.temperature = max(float(command.get("temperature", 0.3)), 1e-8)
                prediction = model(image)
            prediction = prediction.replace("<", r"\lt ").replace(">", r"\gt ")
            emit(
                {
                    "type": "result",
                    "id": command.get("id"),
                    "latex": prediction,
                    "seconds": time.perf_counter() - infer_started,
                }
            )
        except Exception as exc:
            emit({"type": "error", "id": command.get("id") if "command" in locals() else None, "message": str(exc)})
            traceback.print_exc(file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
