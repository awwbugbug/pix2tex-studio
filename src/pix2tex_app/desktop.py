from __future__ import annotations

import ctypes
import getpass
import re
import sys
from collections.abc import Callable

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Qt, Signal, Slot
from PySide6.QtGui import QAction, QIcon, QWindow
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from pix2tex_app.app_icon import render_app_icon


class SingleInstanceGuard(QObject):
    """Own a per-user local server and notify the primary process on relaunch."""

    activationRequested = Signal()

    def __init__(self, app: QApplication, name: str = "Reasonix.Pix2TexStudio.v1") -> None:
        super().__init__(app)
        user = re.sub(r"[^A-Za-z0-9_.-]", "_", getpass.getuser()) or "user"
        self._name = f"{name}.{user}"
        self._server: QLocalServer | None = None
        self.is_primary = not self._notify_existing_instance()
        if self.is_primary:
            self._start_server()

    def _notify_existing_instance(self) -> bool:
        socket = QLocalSocket(self)
        socket.connectToServer(self._name)
        if not socket.waitForConnected(350):
            return False
        socket.write(b"activate\n")
        socket.waitForBytesWritten(350)
        socket.disconnectFromServer()
        return True

    def _start_server(self) -> None:
        server = QLocalServer(self)
        if not server.listen(self._name):
            # A crashed process can leave a stale endpoint on Unix-like hosts.
            # On Windows this is harmless and removeServer simply clears the name.
            QLocalServer.removeServer(self._name)
            if not server.listen(self._name):
                self.is_primary = False
                return
        server.newConnection.connect(self._accept_connections)
        self._server = server

    def _accept_connections(self) -> None:
        if not self._server:
            return
        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            if socket:
                socket.disconnectFromServer()
                socket.deleteLater()
            self.activationRequested.emit()

    def close(self) -> None:
        if self._server:
            self._server.close()
            self._server = None


class _WindowsHotkeyFilter(QAbstractNativeEventFilter):
    WM_HOTKEY = 0x0312

    def __init__(self, hotkey_id: int, callback: Callable[[], None]) -> None:
        super().__init__()
        self._hotkey_id = hotkey_id
        self._callback = callback

    def nativeEventFilter(self, _event_type, message):  # noqa: N802
        if sys.platform == "win32":
            try:
                from ctypes import wintypes

                native_message = wintypes.MSG.from_address(int(message))
                if native_message.message == self.WM_HOTKEY and native_message.wParam == self._hotkey_id:
                    self._callback()
                    return True, 0
            except (TypeError, ValueError):
                pass
        return False, 0


class DesktopIntegration(QObject):
    trayAvailableChanged = Signal()

    _HOTKEY_ID = 0x5054
    _HOTKEYS = {
        "Ctrl+Shift+A": (0x0002 | 0x0004, ord("A")),
        "Alt+S": (0x0001, ord("S")),
        "Ctrl+A": (0x0002, ord("A")),
    }
    _MOD_NOREPEAT = 0x4000

    def __init__(self, app: QApplication, controller: QObject, *, enabled: bool = True) -> None:
        super().__init__(app)
        self._app = app
        self._controller = controller
        self._enabled = enabled
        self._window = None
        self._show_pending = False
        self._quitting = False
        self._tray_hint_shown = False
        self._tray: QSystemTrayIcon | None = None
        self._tray_menu: QMenu | None = None
        self._hotkey_filter: _WindowsHotkeyFilter | None = None
        self._registered_hotkey = ""
        self._icon = self._create_icon()
        self._app.setWindowIcon(self._icon)

        if enabled:
            self._create_tray()
            if sys.platform == "win32":
                self._hotkey_filter = _WindowsHotkeyFilter(self._HOTKEY_ID, self._capture_formula)
                self._app.installNativeEventFilter(self._hotkey_filter)

    @property
    def icon(self) -> QIcon:
        return self._icon

    def attach_window(self, window: object) -> None:
        self._window = window
        try:
            window.setIcon(self._icon)
        except (AttributeError, TypeError):
            pass
        if self._show_pending:
            self._show_pending = False
            self.showWindow()

    def _create_icon(self) -> QIcon:
        return QIcon(render_app_icon())

    def _create_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        tray = QSystemTrayIcon(self._icon, self)
        tray.setToolTip("Pix2Tex Studio")
        menu = QMenu()

        capture_action = QAction("截取公式", menu)
        capture_action.triggered.connect(self._capture_formula)
        menu.addAction(capture_action)

        show_action = QAction("显示主窗口", menu)
        show_action.triggered.connect(self.showWindow)
        menu.addAction(show_action)
        menu.addSeparator()

        quit_action = QAction("退出 Pix2Tex Studio", menu)
        quit_action.triggered.connect(self.quitApplication)
        menu.addAction(quit_action)

        tray.setContextMenu(menu)
        tray.activated.connect(self._tray_activated)
        tray.show()
        self._tray = tray
        self._tray_menu = menu
        self.trayAvailableChanged.emit()

    @Slot(result=bool)
    def shouldHideOnClose(self) -> bool:  # noqa: N802
        return bool(self._tray and self._tray.isVisible() and not self._quitting)

    @Slot()
    def hideToTray(self) -> None:  # noqa: N802
        if self._window:
            self._window.hide()
        if self._tray:
            if not self._tray_hint_shown:
                self._tray_hint_shown = True
                self._tray.showMessage(
                    "Pix2Tex Studio 仍在运行",
                    "CPU 模型保持预热，可使用系统快捷键继续截图。",
                    QSystemTrayIcon.MessageIcon.Information,
                    2200,
                )

    @Slot()
    def showWindow(self) -> None:  # noqa: N802
        if not self._window:
            self._show_pending = True
            return
        if self._window.visibility() == QWindow.Visibility.Minimized:
            self._window.showNormal()
        else:
            self._window.show()
        self._window.raise_()
        self._window.requestActivate()

    def _capture_formula(self) -> None:
        capture = getattr(self._controller, "captureFormula", None)
        if callable(capture):
            capture()

    @Slot(int)
    def _tray_activated(self, reason: int) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.showWindow()

    def apply_global_hotkey(self, sequence: str) -> tuple[bool, str]:
        if not self._enabled:
            return True, "界面预览模式"
        if sys.platform != "win32":
            return False, "系统级快捷键当前仅支持 Windows"
        if sequence not in self._HOTKEYS:
            return False, "不支持这个快捷键组合"

        user32 = ctypes.windll.user32
        previous = self._registered_hotkey
        if previous:
            user32.UnregisterHotKey(None, self._HOTKEY_ID)
            self._registered_hotkey = ""

        modifiers, virtual_key = self._HOTKEYS[sequence]
        registered = bool(
            user32.RegisterHotKey(
                None,
                self._HOTKEY_ID,
                modifiers | self._MOD_NOREPEAT,
                virtual_key,
            )
        )
        if registered:
            self._registered_hotkey = sequence
            warning = " · 会覆盖其他软件的全选" if sequence == "Ctrl+A" else ""
            return True, f"已注册系统快捷键 · {sequence}{warning}"

        if previous:
            old_modifiers, old_key = self._HOTKEYS[previous]
            if user32.RegisterHotKey(
                None,
                self._HOTKEY_ID,
                old_modifiers | self._MOD_NOREPEAT,
                old_key,
            ):
                self._registered_hotkey = previous
        return False, f"{sequence} 已被其他程序占用"

    @Slot()
    def quitApplication(self) -> None:  # noqa: N802
        self._quitting = True
        self._app.quit()

    @Slot()
    def shutdown(self) -> None:
        if self._registered_hotkey and sys.platform == "win32":
            ctypes.windll.user32.UnregisterHotKey(None, self._HOTKEY_ID)
            self._registered_hotkey = ""
        if self._hotkey_filter:
            self._app.removeNativeEventFilter(self._hotkey_filter)
            self._hotkey_filter = None
        if self._tray:
            self._tray.hide()
            self._tray.deleteLater()
            self._tray = None
        if self._tray_menu:
            self._tray_menu.deleteLater()
            self._tray_menu = None
