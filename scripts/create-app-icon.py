from pathlib import Path

from PIL import Image
from PySide6.QtCore import QRectF, QSize
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    source = (
        project_root
        / "runtime"
        / "build_env"
        / "Lib"
        / "site-packages"
        / "pix2tex"
        / "resources"
        / "icon.svg"
    )
    output = project_root / "packaging" / "pix2tex-studio.ico"
    if not source.is_file():
        raise FileNotFoundError(f"Upstream pix2tex icon not found: {source}")

    QGuiApplication([])
    renderer = QSvgRenderer(str(source))
    if not renderer.isValid():
        raise RuntimeError(f"Could not render {source}")
    image = QImage(QSize(256, 256), QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter, QRectF(0, 0, 256, 256))
    painter.end()

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
