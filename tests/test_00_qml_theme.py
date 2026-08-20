from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from PIL import Image

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QColor, QImage
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtWebEngineQuick import QtWebEngineQuick
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from pix2tex_app.controller import AppController

QtWebEngineQuick.initialize()


def _channel_luminance(value: int) -> float:
    channel = value / 255.0
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def _contrast(first: QColor, second: QColor) -> float:
    first_luminance = (
        0.2126 * _channel_luminance(first.red())
        + 0.7152 * _channel_luminance(first.green())
        + 0.0722 * _channel_luminance(first.blue())
    )
    second_luminance = (
        0.2126 * _channel_luminance(second.red())
        + 0.7152 * _channel_luminance(second.green())
        + 0.0722 * _channel_luminance(second.blue())
    )
    lighter, darker = sorted((first_luminance, second_luminance), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def _composited_luminance(color: QColor) -> float:
    alpha = color.alphaF()
    red = round(color.red() * alpha + 255 * (1 - alpha))
    green = round(color.green() * alpha + 255 * (1 - alpha))
    blue = round(color.blue() * alpha + 255 * (1 - alpha))
    return (
        0.2126 * _channel_luminance(red)
        + 0.7152 * _channel_luminance(green)
        + 0.0722 * _channel_luminance(blue)
    )


def _find_text(root: QQuickItem, value: str) -> QQuickItem:
    pending = [root]
    while pending:
        item = pending.pop()
        if item.property("text") == value:
            return item
        pending.extend(item.childItems())
    raise AssertionError(f"Text item {value!r} was not found")


class QmlThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_light_primary_text_stays_contrasting_during_hover(self) -> None:
        qml_dir = Path(__file__).resolve().parents[1] / "src" / "pix2tex_app" / "ui" / "qml"
        source = b'''import QtQuick
import QtQuick.Controls
import "components"
import "."
ApplicationWindow {
    width: 240
    height: 110
    visible: true
    Component.onCompleted: Theme.dark = false
    ActionButton {
        objectName: "primaryButton"
        x: 50
        y: 35
        width: 130
        text: "Primary action"
        primary: true
    }
}'''

        engine = QQmlApplicationEngine()
        engine.loadData(source, QUrl.fromLocalFile(str(qml_dir / "ThemeContrastProbe.qml")))
        self.assertTrue(engine.rootObjects())
        window = engine.rootObjects()[0]
        button = window.findChild(QQuickItem, "primaryButton")
        self.assertIsNotNone(button)
        label = _find_text(button.property("contentItem"), "Primary action")
        background = button.property("background")

        samples: list[tuple[str, float]] = []

        def sample(name: str) -> None:
            foreground = label.property("color")
            fill = background.property("color")
            samples.append((name, _contrast(foreground, fill)))

        QTest.qWait(40)
        sample("rest")
        QTest.mouseMove(window, QPoint(90, 50), 5)
        for name, wait_ms in (("hover-start", 0), ("hover-mid", 60), ("hover-end", 100)):
            QTest.qWait(wait_ms)
            sample(name)

        window.close()
        for name, ratio in samples:
            with self.subTest(state=name):
                self.assertGreaterEqual(ratio, 4.5, f"contrast was only {ratio:.2f}:1")

    def test_light_transparent_hover_surfaces_never_pass_through_dark_frames(self) -> None:
        qml_dir = Path(__file__).resolve().parents[1] / "src" / "pix2tex_app" / "ui" / "qml"
        source = b'''import QtQuick
import QtQuick.Controls
import "components"
import "."
ApplicationWindow {
    width: 520
    height: 110
    visible: true
    color: "white"
    Component.onCompleted: Theme.dark = false
    Row {
        x: 20
        y: 30
        spacing: 16
        ActionButton { objectName: "quiet"; quiet: true; text: "Quiet" }
        RailButton { objectName: "rail"; text: "Rail" }
        FormatButton { objectName: "format"; text: "Format" }
        StepButton { objectName: "step"; plus: true }
        WindowButton { objectName: "windowButton"; role: "minimize" }
    }
}'''

        engine = QQmlApplicationEngine()
        engine.loadData(source, QUrl.fromLocalFile(str(qml_dir / "TransparentHoverProbe.qml")))
        self.assertTrue(engine.rootObjects())
        window = engine.rootObjects()[0]
        QTest.qWait(60)

        for object_name in ("quiet", "rail", "format", "step", "windowButton"):
            control = window.findChild(QQuickItem, object_name)
            self.assertIsNotNone(control)
            point = control.mapToScene(QPointF(control.width() / 2, control.height() / 2))
            QTest.mouseMove(window, QPoint(round(point.x()), round(point.y())), 5)
            QTest.qWait(55)
            luminance = _composited_luminance(control.property("background").property("color"))
            with self.subTest(control=object_name):
                self.assertGreaterEqual(luminance, 0.85, f"hover luminance dipped to {luminance:.3f}")
            QTest.mouseMove(window, QPoint(500, 95), 5)
            QTest.qWait(180)

        window.close()

    def test_light_history_hover_never_passes_through_a_dark_frame(self) -> None:
        qml_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "pix2tex_app"
            / "ui"
            / "qml"
            / "App.qml"
        )
        with tempfile.TemporaryDirectory() as directory:
            controller = AppController(start_worker=False, data_dir=Path(directory))
            controller.setThemeMode("light")
            controller._record_history("hover-probe-formula", "", "0.10s")

            engine = QQmlApplicationEngine()
            engine.rootContext().setContextProperty("appController", controller)
            engine.load(QUrl.fromLocalFile(str(qml_path)))
            self.assertTrue(engine.rootObjects())
            window = engine.rootObjects()[0]
            window.setProperty("pageIndex", 1)
            QTest.qWait(220)

            content = window.property("contentItem")
            formula_text = _find_text(content, "hover-probe-formula")
            history_entry = formula_text.parentItem()
            while history_entry is not None:
                entry_color = history_entry.property("color")
                if isinstance(entry_color, QColor):
                    break
                history_entry = history_entry.parentItem()
            self.assertIsNotNone(history_entry)

            point = history_entry.mapToScene(QPointF(24, history_entry.height() / 2))
            QTest.mouseMove(window, QPoint(round(point.x()), round(point.y())), 5)

            samples: list[tuple[str, float]] = []
            for name, wait_ms in (("hover-start", 10), ("hover-mid", 45), ("hover-late", 65), ("hover-end", 100)):
                QTest.qWait(wait_ms)
                samples.append((name, _composited_luminance(history_entry.property("color"))))

            window.close()
            controller.shutdown()
            for name, luminance in samples:
                with self.subTest(state=name):
                    self.assertGreaterEqual(luminance, 0.85, f"hover luminance dipped to {luminance:.3f}")

    def test_history_copy_and_delete_buttons_receive_clicks(self) -> None:
        qml_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "pix2tex_app"
            / "ui"
            / "qml"
            / "App.qml"
        )
        with tempfile.TemporaryDirectory() as directory:
            controller = AppController(start_worker=False, data_dir=Path(directory))
            controller._record_history("action-probe-formula", "", "0.10s")
            copied: list[str] = []
            controller._copy_to_clipboard = copied.append

            engine = QQmlApplicationEngine()
            engine.rootContext().setContextProperty("appController", controller)
            engine.load(QUrl.fromLocalFile(str(qml_path)))
            self.assertTrue(engine.rootObjects())
            window = engine.rootObjects()[0]
            window.setProperty("pageIndex", 1)
            QTest.qWait(220)
            content = window.property("contentItem")

            copy_text = _find_text(content, "复制")
            copy_point = copy_text.mapToScene(QPointF(copy_text.width() / 2, copy_text.height() / 2))
            QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(round(copy_point.x()), round(copy_point.y())))
            QTest.qWait(40)
            self.assertEqual(copied, ["action-probe-formula"])

            delete_text = _find_text(content, "删除")
            delete_point = delete_text.mapToScene(QPointF(delete_text.width() / 2, delete_text.height() / 2))
            QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(round(delete_point.x()), round(delete_point.y())))
            QTest.qWait(80)
            self.assertEqual(controller.historyModel.rowCount(), 0)
            window.close()
            controller.shutdown()

    def test_mouse_wheel_zooms_source_image(self) -> None:
        qml_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "pix2tex_app"
            / "ui"
            / "qml"
            / "App.qml"
        )
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            image_path = data_dir / "formula.png"
            image = QImage(640, 240, QImage.Format.Format_RGB32)
            image.fill(QColor("white"))
            self.assertTrue(image.save(str(image_path)))

            controller = AppController(start_worker=False, data_dir=data_dir)
            controller._accept_image(str(image_path))
            engine = QQmlApplicationEngine()
            engine.rootContext().setContextProperty("appController", controller)
            engine.load(QUrl.fromLocalFile(str(qml_path)))
            self.assertTrue(engine.rootObjects())
            window = engine.rootObjects()[0]
            QTest.qWait(220)
            source_flick = window.findChild(QQuickItem, "sourceFlick")
            self.assertIsNotNone(source_flick)
            center = source_flick.mapToScene(QPointF(source_flick.width() / 2, source_flick.height() / 2))

            QTest.wheelEvent(window, center, QPoint(0, 240))
            QTest.qWait(80)
            zoomed_scale = float(window.property("imageScale"))
            self.assertGreater(zoomed_scale, 1.0)

            QTest.wheelEvent(window, center, QPoint(0, -120))
            QTest.qWait(80)
            self.assertLess(float(window.property("imageScale")), zoomed_scale)
            window.close()
            controller.shutdown()

    def test_handwriting_stroke_is_saved_as_the_current_input_image(self) -> None:
        qml_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "pix2tex_app"
            / "ui"
            / "qml"
            / "App.qml"
        )
        with tempfile.TemporaryDirectory() as directory:
            controller = AppController(start_worker=False, data_dir=Path(directory))
            engine = QQmlApplicationEngine()
            engine.rootContext().setContextProperty("appController", controller)
            engine.load(QUrl.fromLocalFile(str(qml_path)))
            self.assertTrue(engine.rootObjects())
            window = engine.rootObjects()[0]
            window.setProperty("drawMode", True)
            QTest.qWait(220)

            draw_board = window.findChild(QQuickItem, "drawBoard")
            draw_area = window.findChild(QQuickItem, "drawArea")
            recognize_button = window.findChild(QQuickItem, "drawRecognizeButton")
            self.assertIsNotNone(draw_board)
            self.assertIsNotNone(draw_area)
            self.assertIsNotNone(recognize_button)

            start = draw_area.mapToScene(QPointF(draw_area.width() * 0.35, draw_area.height() * 0.45))
            end = draw_area.mapToScene(QPointF(draw_area.width() * 0.65, draw_area.height() * 0.55))
            QTest.mousePress(
                window,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                QPoint(round(start.x()), round(start.y())),
            )
            QTest.mouseMove(window, QPoint(round(end.x()), round(end.y())), 40)
            QTest.mouseRelease(
                window,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                QPoint(round(end.x()), round(end.y())),
            )
            QTest.qWait(100)
            strokes = draw_board.property("strokes")
            if hasattr(strokes, "toVariant"):
                strokes = strokes.toVariant()
            self.assertGreater(len(strokes), 0)

            button_center = recognize_button.mapToScene(
                QPointF(recognize_button.width() / 2, recognize_button.height() / 2)
            )
            QTest.mouseClick(
                window,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                QPoint(round(button_center.x()), round(button_center.y())),
            )
            QTest.qWait(500)

            image_path = Path(QUrl(controller.imageUrl).toLocalFile())
            self.assertTrue(image_path.is_file())
            self.assertTrue(image_path.name.startswith("drawing-"))
            self.assertFalse(bool(window.property("drawMode")))
            with Image.open(image_path) as image:
                self.assertLess(image.convert("L").getextrema()[0], 250)

            window.close()
            controller.shutdown()

    def test_long_history_formula_keeps_actions_inside_entry_background(self) -> None:
        qml_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "pix2tex_app"
            / "ui"
            / "qml"
            / "App.qml"
        )
        long_formula = (r"\left[\begin{array}{ll}\text{very long formula}&\sqrt{3}" * 18) + r"\end{array}\right]"
        with tempfile.TemporaryDirectory() as directory:
            controller = AppController(start_worker=False, data_dir=Path(directory))
            controller._record_history(long_formula, "", "19.68s")
            engine = QQmlApplicationEngine()
            engine.rootContext().setContextProperty("appController", controller)
            engine.load(QUrl.fromLocalFile(str(qml_path)))
            self.assertTrue(engine.rootObjects())
            window = engine.rootObjects()[0]
            window.setProperty("pageIndex", 1)
            QTest.qWait(250)
            content = window.property("contentItem")
            formula_text = _find_text(content, long_formula)
            history_entry = formula_text.parentItem()
            while history_entry is not None and not isinstance(history_entry.property("color"), QColor):
                history_entry = history_entry.parentItem()
            self.assertIsNotNone(history_entry)

            delete_text = _find_text(content, "删除")
            delete_button = delete_text
            while delete_button is not None and delete_button.property("danger") is None:
                delete_button = delete_button.parentItem()
            self.assertIsNotNone(delete_button)
            entry_bottom = history_entry.mapToScene(QPointF(0, history_entry.height())).y()
            button_bottom = delete_button.mapToScene(QPointF(0, delete_button.height())).y()
            self.assertLessEqual(button_bottom, entry_bottom)
            window.close()
            controller.shutdown()


if __name__ == "__main__":
    unittest.main()
