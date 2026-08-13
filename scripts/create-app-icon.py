from pathlib import Path
import sys

from PIL import Image
from PySide6.QtGui import QGuiApplication


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pix2tex_app.app_icon import render_app_icon  # noqa: E402


def main() -> int:
    output = PROJECT_ROOT / "packaging" / "pix2tex-studio.ico"

    QGuiApplication([])
    image = render_app_icon(256).toImage()

    png = output.with_suffix(".png")
    if not image.save(str(png), "PNG"):
        raise RuntimeError(f"Could not save {png}")
    with Image.open(png) as source_image:
        source_image.save(
            output,
            format="ICO",
            sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
    png.unlink()
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
