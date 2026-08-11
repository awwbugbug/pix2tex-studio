from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


_GWL_STYLE = -16
_WS_MAXIMIZEBOX = 0x00010000
_WS_MINIMIZEBOX = 0x00020000
_WS_THICKFRAME = 0x00040000
_WS_SYSMENU = 0x00080000
_SYSTEM_WINDOW_BEHAVIORS = (
    _WS_MAXIMIZEBOX | _WS_MINIMIZEBOX | _WS_THICKFRAME | _WS_SYSMENU
)


def _application_package_root(
    *, frozen: bool | None = None, bundle_dir: str | Path | None = None
) -> Path:
    """Resolve packaged resources in both source and PyInstaller layouts."""
    is_frozen = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
    if is_frozen:
        root = Path(bundle_dir or getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        return root / "pix2tex_app"
    return Path(__file__).resolve().parent


def _windows_style_with_system_behaviors(style: int) -> int:
    """Restore native window management without adding a visible caption."""
    return style | _SYSTEM_WINDOW_BEHAVIORS


def _apply_windows_window_style(window: object) -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes

        hwnd = int(window.winId())
        user32 = ctypes.windll.user32
        long_ptr = ctypes.c_ssize_t
        user32.GetWindowLongPtrW.argtypes = (wintypes.HWND, ctypes.c_int)
        user32.GetWindowLongPtrW.restype = long_ptr
        user32.SetWindowLongPtrW.argtypes = (wintypes.HWND, ctypes.c_int, long_ptr)
        user32.SetWindowLongPtrW.restype = long_ptr
        user32.SetWindowPos.argtypes = (
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        )
        user32.SetWindowPos.restype = wintypes.BOOL

        style = int(user32.GetWindowLongPtrW(hwnd, _GWL_STYLE))
        updated_style = _windows_style_with_system_behaviors(style)
        if updated_style != style:
            user32.SetWindowLongPtrW(hwnd, _GWL_STYLE, updated_style)
            user32.SetWindowPos(
                hwnd,
                0,
                0,
                0,
                0,
                0,
                0x0001  # SWP_NOSIZE
                | 0x0002  # SWP_NOMOVE
                | 0x0004  # SWP_NOZORDER
                | 0x0010  # SWP_NOACTIVATE
                | 0x0020,  # SWP_FRAMECHANGED
            )

        transitions_disabled = wintypes.BOOL(False)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            3,  # DWMWA_TRANSITIONS_FORCEDISABLED
            ctypes.byref(transitions_disabled),
            ctypes.sizeof(transitions_disabled),
        )
        preference = ctypes.c_int(2)  # DWMWCP_ROUND
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            33,  # DWMWA_WINDOW_CORNER_PREFERENCE
            ctypes.byref(preference),
            ctypes.sizeof(preference),
        )
    except (AttributeError, OSError, TypeError, ValueError):
        pass


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Pix2Tex Studio")
    parser.add_argument("--no-worker", action="store_true", help="Do not start the OCR worker")
    parser.add_argument("--smoke-test", action="store_true", help="Load QML and exit automatically")
    parser.add_argument("--render-preview", type=Path, help="Render the main window to a PNG and exit")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

    from PySide6.QtCore import QCoreApplication, QStandardPaths, QTimer, QUrl
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuick import QQuickItem  # noqa: F401 - registers QQuickItem converters
    from PySide6.QtWebEngineQuick import QtWebEngineQuick
    from PySide6.QtWidgets import QApplication

    from pix2tex_app.controller import AppController
    from pix2tex_app.desktop import DesktopIntegration, SingleInstanceGuard
    from pix2tex_app.diagnostics import configure_crash_logging

    QtWebEngineQuick.initialize()
    app = QApplication(sys.argv)
    app.setApplicationDisplayName("Pix2Tex Studio")
    app.setApplicationName("Pix2TexStudio")
    app.setOrganizationName("Reasonix")
    app_data = Path(
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    )
    configure_crash_logging(app_data)
    interactive_desktop = not (args.smoke_test or args.render_preview)
    app.setQuitOnLastWindowClosed(not interactive_desktop)

    instance_guard = SingleInstanceGuard(app) if interactive_desktop else None
    if instance_guard and not instance_guard.is_primary:
        return 0

    controller = AppController(
        start_worker=not (args.no_worker or args.smoke_test or args.render_preview),
        enable_history_previews=not (args.smoke_test or args.render_preview),
    )
    desktop = DesktopIntegration(app, controller, enabled=interactive_desktop)
    if interactive_desktop:
        controller.bind_global_hotkey(desktop.apply_global_hotkey)
    app.aboutToQuit.connect(controller.shutdown)
    app.aboutToQuit.connect(desktop.shutdown)
    if instance_guard:
        app.aboutToQuit.connect(instance_guard.close)
        instance_guard.activationRequested.connect(desktop.showWindow)

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("appController", controller)
    engine.rootContext().setContextProperty("desktopIntegration", desktop)
    qml_path = _application_package_root() / "ui" / "qml" / "App.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        controller.shutdown()
        return 1
    root_window = engine.rootObjects()[0]
    desktop.attach_window(root_window)
    _apply_windows_window_style(root_window)

    if args.render_preview:
        output = args.render_preview.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        preview_grabs: list[object] = []

        def render_and_exit() -> None:
            root = engine.rootObjects()[0]
            content_item = root.property("contentItem")
            if content_item is None:
                QCoreApplication.exit(2)
                return

            grab_result = content_item.grabToImage()
            preview_grabs.append(grab_result)

            def save_grab() -> None:
                saved = grab_result.saveToFile(str(output))
                QCoreApplication.exit(0 if saved else 2)

            grab_result.ready.connect(save_grab)

        QTimer.singleShot(1200, render_and_exit)
        QTimer.singleShot(8000, lambda: QCoreApplication.exit(3))
    elif args.smoke_test:
        QTimer.singleShot(700, app.quit)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
