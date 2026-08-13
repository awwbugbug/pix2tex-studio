from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap


def render_app_icon(size: int = 64) -> QPixmap:
    """Render the canonical Pix2Tex Studio icon at a square pixel size."""
    if size <= 0:
        raise ValueError("Icon size must be positive")

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    scale = size / 64.0
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#1b1d20"))
    painter.drawRoundedRect(
        QRectF(3 * scale, 3 * scale, 58 * scale, 58 * scale),
        15 * scale,
        15 * scale,
    )

    painter.setPen(QColor("#ffffff"))
    font = QFont("Cambria Math")
    font.setPixelSize(round(48 * scale))
    font.setItalic(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "∫")
    painter.end()
    return pixmap
