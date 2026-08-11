from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QKeyEvent, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget


class ScreenCaptureOverlay(QWidget):
    """Capture a rectangular region from the screen under the cursor."""

    captured = Signal(str)
    cancelled = Signal()

    def __init__(self, output_path: Path) -> None:
        super().__init__(None)
        self._output_path = output_path
        self._begin = QPoint()
        self._end = QPoint()
        self._dragging = False

        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if screen is None:
            raise RuntimeError("没有可用的显示器")
        self._screen = screen
        self.setGeometry(screen.geometry())
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def start(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

    def _selection(self) -> QRect:
        return QRect(self._begin, self._end).normalized()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(8, 10, 13, 112))

        if not self._dragging:
            painter.setPen(QColor(255, 255, 255, 225))
            painter.drawText(self.rect().adjusted(0, 18, 0, 0), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, "拖动框选公式 · Esc 取消")
            return

        selection = self._selection()
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(selection, Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.setPen(QPen(QColor(255, 255, 255), 1.5))
        painter.drawRect(selection)

        label = f"{selection.width()} × {selection.height()}"
        label_rect = QRect(selection.left(), selection.bottom() + 7, 92, 22)
        if label_rect.bottom() > self.height():
            label_rect.moveBottom(selection.top() - 7)
        painter.fillRect(label_rect, QColor(15, 17, 20, 220))
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            self.cancelled.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._dragging = True
        self._begin = event.position().toPoint()
        self._end = self._begin
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if not self._dragging:
            return
        self._end = event.position().toPoint()
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton or not self._dragging:
            return
        self._end = event.position().toPoint()
        selection = self._selection().intersected(self.rect())
        self._dragging = False

        if selection.width() < 3 or selection.height() < 3:
            self.close()
            self.cancelled.emit()
            return

        pixmap = self._screen.grabWindow(
            0,
            selection.x(),
            selection.y(),
            selection.width(),
            selection.height(),
        )
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        saved = not pixmap.isNull() and pixmap.save(str(self._output_path), "PNG")
        self.close()
        if saved:
            self.captured.emit(str(self._output_path))
        else:
            self.cancelled.emit()
