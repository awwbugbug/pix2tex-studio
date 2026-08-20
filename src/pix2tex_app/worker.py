from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def _model_dir() -> Path:
    """Locate the bundled UniMERNet weights directory.

    Resolution order: explicit env override, then a package-local ``models``
    directory (used by the packaged build), so the frozen app finds its
    bundled weights without any environment configuration.
    """
    override = os.environ.get("PIX2TEX_UNIMERNET_MODEL_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent / "models" / "unimernet_tiny"


def _write_worker_config(model_dir: Path) -> Path:
    """Write a resolved UniMERNet config to a temp file and return its path.

    UniMERNet's ``Config`` only loads from a yaml path, so the model directory
    is baked into a small config written next to the OS temp dir at startup.
    """
    weights = next(model_dir.glob("*.pth"), None)
    if weights is None:
        raise FileNotFoundError(f"no .pth weights found in {model_dir}")
    md = model_dir.as_posix()
    text = f"""model:
  arch: unimernet
  model_type: unimernet
  model_config:
    model_name: {md}
    max_seq_len: 1536
  load_pretrained: True
  pretrained: '{weights.as_posix()}'
  tokenizer_config:
    path: {md}
datasets:
  formula_rec_eval:
    vis_processor:
      eval:
        name: "formula_image_eval"
        image_size:
          - 192
          - 672
run:
  runner: runner_iter
  task: unimernet_train
  batch_size_train: 64
  batch_size_eval: 64
  num_workers: 1
  iters_per_inner_epoch: 2000
  max_iters: 60000
  seed: 42
  output_dir: "../output/demo"
  evaluate: True
  test_splits: [ "eval" ]
  device: "cpu"
  world_size: 1
  dist_url: "env://"
  distributed: False
  distributed_type: ddp
  generate_cfg:
    temperature: 0.0
"""
    config_path = Path(tempfile.gettempdir()) / "pix2tex_unimernet_worker.yaml"
    config_path.write_text(text, encoding="utf-8")
    return config_path


def _background_is_dark(image: Any) -> bool:
    """Estimate whether the image is light-on-dark and should be inverted.

    Formula models are trained on white-background black-text images, so a
    dark-background capture is out of distribution. A formula (sparse ink on a
    large background) is dominated by its background, so a low mean luminance
    means the background is dark. Mean luminance is used rather than a border
    ring because a stray light frame around the edge would defeat border
    sampling.
    """
    import numpy as np

    grayscale = np.asarray(image.convert("L"))
    if grayscale.size == 0:
        return False
    return float(grayscale.mean()) < 128.0


def _crop_to_content(image: Any) -> Any:
    """Crop a white-background image to its dark content plus a small margin.

    Handwriting drawn on a large canvas (or a screenshot with wide margins)
    otherwise shrinks to a few pixels once the model resizes the whole frame.
    Expects a white background (call after any inversion).
    """
    import numpy as np

    grayscale = np.asarray(image.convert("L"))
    if grayscale.size == 0:
        return image
    mask = grayscale < 250
    if not mask.any():
        return image
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    top, bottom = int(rows[0]), int(rows[-1])
    left, right = int(cols[0]), int(cols[-1])
    height, width = grayscale.shape
    span = max(right - left, bottom - top)
    margin = max(8, int(span * 0.06))
    box = (
        max(0, left - margin),
        max(0, top - margin),
        min(width, right + margin + 1),
        min(height, bottom + margin + 1),
    )
    if box == (0, 0, width, height):
        return image
    return image.crop(box)


def prepare_for_model(image: Any) -> Any:
    """Return an RGB image with a white background, inverting dark captures and
    cropping away surrounding whitespace so the formula fills the frame."""
    from PIL import ImageOps

    rgb = image.convert("RGB")
    if _background_is_dark(rgb):
        rgb = ImageOps.invert(rgb)
    return _crop_to_content(rgb)


def normalize_prediction(prediction: str) -> str:
    """Trim UniMERNet output and drop layout-only artifacts.

    Handwriting places integral/sum limits stacked above and below the operator,
    so the model emits ``\\limits`` and renders the result spread out. Dropping
    ``\\limits``/``\\nolimits`` restores conventional sub/superscript placement
    without changing the mathematical meaning. Inter-token spaces are otherwise
    kept because they terminate LaTeX command names (e.g. ``\\displaystyle x``).
    """
    text = prediction.strip()
    text = re.sub(r"\\(?:no)?limits\b", "", text)
    text = re.sub(r"[ \t]{2,}", " ", text).strip()
    return text


def main() -> int:
    os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")
    started = time.perf_counter()
    try:
        import torch
        from PIL import Image

        from unimernet.common.config import Config
        import unimernet.tasks as tasks
        from unimernet.processors import load_processor

        # UniMERNet's model classes print construction banners to stdout, which
        # is the JSONL protocol channel. Redirect stdout to stderr during load
        # so those lines never corrupt the result stream.
        with contextlib.redirect_stdout(sys.stderr):
            torch.set_grad_enabled(False)
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

            config_path = _write_worker_config(_model_dir())
            cfg = Config(argparse.Namespace(cfg_path=str(config_path), options=None))
            task = tasks.setup_task(cfg)
            model = task.build_model(cfg).to(device)
            model.eval()
            vis_processor = load_processor(
                "formula_image_eval",
                cfg.config.datasets.formula_rec_eval.vis_processor.eval,
            )
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
            with Image.open(image_path) as image, contextlib.redirect_stdout(sys.stderr):
                pixel_values = vis_processor(prepare_for_model(image)).unsqueeze(0).to(device)
                output = model.generate({"image": pixel_values})
            prediction = normalize_prediction(output["pred_str"][0])
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
