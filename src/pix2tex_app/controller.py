from __future__ import annotations

import json
import logging
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import (
    QAbstractListModel,
    QCoreApplication,
    QModelIndex,
    QObject,
    Property,
    QProcess,
    QProcessEnvironment,
    QSettings,
    QStandardPaths,
    Qt,
    QTimer,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QGuiApplication

from .diagnostics import LOGGER_NAME


def _worker_process_command(
    *, frozen: bool | None = None, executable: str | None = None
) -> tuple[str, list[str]]:
    is_frozen = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
    program = executable or sys.executable
    if is_frozen:
        worker_executable = Path(program).with_name("Pix2TexWorker.exe")
        return str(worker_executable), []
    worker_path = Path(__file__).with_name("worker.py")
    return program, ["-u", str(worker_path)]


def _clean_latex(latex: str) -> str:
    """Return compact, delimiter-free LaTeX for Word's equation input.

    UniMERNet wraps plain formulas in a single-row ``array`` and separates every
    token with a space, which Word's LaTeX equation input cannot parse (and which
    also trips the SymPy parser). This unwraps that array, drops layout-only
    commands, and removes token spaces — keeping only the space that terminates a
    command name before a letter, so ``\\sin x`` does not collapse into
    ``\\sinx``.
    """
    text = latex.strip()
    match = re.match(
        r"^\\begin\{array\}\s*\{[^{}]*\}\s*\{(.*)\}\s*\\end\{array\}$",
        text,
        re.DOTALL,
    )
    if match and r"\\" not in match.group(1):
        text = match.group(1).strip()
    text = re.sub(r"\\displaystyle\b", "", text)
    text = re.sub(r"\\(?:no)?limits\b", "", text)
    text = re.sub(r"(\\[a-zA-Z]+) +(?=[A-Za-z])", "\\1\x00", text)
    text = text.replace(" ", "")
    text = text.replace("\x00", " ")
    return text.strip()


class HistoryModel(QAbstractListModel):
    FormulaRole = Qt.ItemDataRole.UserRole + 1
    ImageRole = FormulaRole + 1
    TimestampRole = ImageRole + 1
    DurationRole = TimestampRole + 1
    PreviewLightRole = DurationRole + 1
    PreviewDarkRole = PreviewLightRole + 1
    PreviewWidthRole = PreviewDarkRole + 1
    PreviewHeightRole = PreviewWidthRole + 1
    PreviewReadyRole = PreviewHeightRole + 1

    def __init__(self, entries: list[dict[str, Any]] | None = None) -> None:
        super().__init__()
        self._entries = entries or []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._entries)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._entries):
            return None
        entry = self._entries[index.row()]
        roles = {
            self.FormulaRole: entry.get("formula", ""),
            self.ImageRole: entry.get("image", ""),
            self.TimestampRole: entry.get("timestamp", ""),
            self.DurationRole: entry.get("duration", ""),
            self.PreviewLightRole: QUrl.fromLocalFile(entry.get("_preview_light", "")).toString()
            if entry.get("_preview_light")
            else "",
            self.PreviewDarkRole: QUrl.fromLocalFile(entry.get("_preview_dark", "")).toString()
            if entry.get("_preview_dark")
            else "",
            self.PreviewWidthRole: int(entry.get("_preview_width", 0)),
            self.PreviewHeightRole: int(entry.get("_preview_height", 0)),
            self.PreviewReadyRole: bool(entry.get("_preview_light") and entry.get("_preview_dark")),
        }
        return roles.get(role)

    def roleNames(self) -> dict[int, bytes]:  # noqa: N802
        return {
            self.FormulaRole: b"formula",
            self.ImageRole: b"imagePath",
            self.TimestampRole: b"timestamp",
            self.DurationRole: b"duration",
            self.PreviewLightRole: b"previewLight",
            self.PreviewDarkRole: b"previewDark",
            self.PreviewWidthRole: b"previewWidth",
            self.PreviewHeightRole: b"previewHeight",
            self.PreviewReadyRole: b"previewReady",
        }

    def prepend(self, entry: dict[str, Any]) -> None:
        self.beginInsertRows(QModelIndex(), 0, 0)
        self._entries.insert(0, entry)
        self.endInsertRows()

    def remove(self, row: int) -> dict[str, Any] | None:
        if not 0 <= row < len(self._entries):
            return None
        self.beginRemoveRows(QModelIndex(), row, row)
        entry = self._entries.pop(row)
        self.endRemoveRows()
        return dict(entry)

    def trim(self, limit: int) -> list[dict[str, Any]]:
        limit = max(0, int(limit))
        if len(self._entries) <= limit:
            return []
        last = len(self._entries) - 1
        self.beginRemoveRows(QModelIndex(), limit, last)
        removed = self._entries[limit:]
        del self._entries[limit:]
        self.endRemoveRows()
        return [dict(entry) for entry in removed]

    def entry(self, row: int) -> dict[str, Any] | None:
        return dict(self._entries[row]) if 0 <= row < len(self._entries) else None

    def clear(self) -> None:
        if not self._entries:
            return
        self.beginResetModel()
        self._entries.clear()
        self.endResetModel()

    def serializable(self) -> list[dict[str, Any]]:
        return [{key: value for key, value in entry.items() if not key.startswith("_")} for entry in self._entries]

    def formulas(self) -> list[str]:
        return list(dict.fromkeys(str(entry.get("formula", "")).strip() for entry in self._entries if entry.get("formula")))

    def set_preview_for_formula(
        self, formula: str, light_path: str, dark_path: str, width: int, height: int
    ) -> None:
        roles = [
            self.PreviewLightRole,
            self.PreviewDarkRole,
            self.PreviewWidthRole,
            self.PreviewHeightRole,
            self.PreviewReadyRole,
        ]
        for row, entry in enumerate(self._entries):
            if entry.get("formula") != formula:
                continue
            entry.update(
                {
                    "_preview_light": light_path,
                    "_preview_dark": dark_path,
                    "_preview_width": width,
                    "_preview_height": height,
                }
            )
            model_index = self.index(row, 0)
            self.dataChanged.emit(model_index, model_index, roles)


class AppController(QObject):
    engineStateChanged = Signal()
    engineDetailChanged = Signal()
    busyChanged = Signal()
    latexChanged = Signal()
    formattedLatexChanged = Signal()
    formatModeChanged = Signal()
    formatErrorChanged = Signal()
    imageUrlChanged = Signal()
    imageNameChanged = Signal()
    lastDurationChanged = Signal()
    noticeChanged = Signal()
    themeModeChanged = Signal()
    autoCopyChanged = Signal()
    globalHotkeyChanged = Signal()
    globalHotkeyStatusChanged = Signal()
    historyLimitChanged = Signal()

    _VALID_FORMATS = {"raw", "word", "latex-inline", "latex-display", "sympy"}
    _VALID_THEMES = {"system", "light", "dark"}
    _VALID_GLOBAL_HOTKEYS = {"Ctrl+Shift+A", "Alt+S", "Ctrl+A"}
    _VALID_HISTORY_LIMITS = {50, 100, 200}

    def __init__(
        self,
        start_worker: bool = True,
        data_dir: Path | None = None,
        enable_history_previews: bool = False,
    ) -> None:
        super().__init__()
        self._engine_state = "warming" if start_worker else "preview"
        self._engine_detail = "正在准备 CPU 识别引擎" if start_worker else "界面预览模式"
        self._busy = False
        self._latex = ""
        self._formatted_latex = ""
        self._format_error = ""
        self._image_path = ""
        self._last_duration = "—"
        self._notice = "离线识别 · 数据仅保存在本机"
        self._pending_image = ""
        self._stdout_buffer = ""
        self._process: QProcess | None = None
        self._capture_overlay = None
        self._capture_parent_window = None
        self._history_preview_renderer = None
        self._global_hotkey_apply = None
        self._logger = logging.getLogger(LOGGER_NAME)

        app_data = data_dir or Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))
        self._data_dir = app_data
        self._cache_dir = app_data / "cache"
        self._history_path = app_data / "history.json"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._history = HistoryModel(self._load_history())

        if data_dir is not None:
            self._settings = QSettings(str(app_data / "settings.ini"), QSettings.Format.IniFormat)
        else:
            self._settings = QSettings()
        self._format_mode = str(self._settings.value("formatMode", "latex-inline"))
        if self._format_mode not in self._VALID_FORMATS:
            self._format_mode = "latex-inline"
        self._theme_mode = str(self._settings.value("themeMode", "system"))
        if self._theme_mode not in self._VALID_THEMES:
            self._theme_mode = "system"
        self._auto_copy = str(self._settings.value("autoCopy", "true")).lower() not in {"0", "false", "no"}
        self._global_hotkey = str(self._settings.value("globalHotkey", "Ctrl+Shift+A"))
        if self._global_hotkey not in self._VALID_GLOBAL_HOTKEYS:
            self._global_hotkey = "Ctrl+Shift+A"
        self._global_hotkey_status = "等待注册系统快捷键"
        try:
            self._history_limit = int(self._settings.value("historyLimit", 100))
        except (TypeError, ValueError):
            self._history_limit = 100
        if self._history_limit not in self._VALID_HISTORY_LIMITS:
            self._history_limit = 100
        removed_on_load = self._history.trim(self._history_limit)
        if removed_on_load:
            self._save_history()

        app = QCoreApplication.instance()
        if isinstance(app, QGuiApplication):
            app.styleHints().colorSchemeChanged.connect(lambda _scheme: self.themeModeChanged.emit())

        if enable_history_previews:
            from PySide6.QtWidgets import QApplication

            if isinstance(app, QApplication):
                from .history_preview import HistoryPreviewRenderer

                mathjax_path = Path(__file__).resolve().parent / "ui" / "assets" / "MathJax.js"
                self._history_preview_renderer = HistoryPreviewRenderer(
                    self._data_dir / "history-previews", mathjax_path, self
                )
                self._history_preview_renderer.rendered.connect(self._history_preview_ready)
                self._history_preview_renderer.prune(self._history.formulas())
                QTimer.singleShot(1200, self._queue_existing_history_previews)

        QTimer.singleShot(1600, self._cleanup_generated_cache)

        if start_worker:
            self._start_worker()

    @Property(str, notify=engineStateChanged)
    def engineState(self) -> str:  # noqa: N802
        return self._engine_state

    @Property(str, notify=engineDetailChanged)
    def engineDetail(self) -> str:  # noqa: N802
        return self._engine_detail

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=latexChanged)
    def latex(self) -> str:
        return self._latex

    @Property(str, notify=formattedLatexChanged)
    def formattedLatex(self) -> str:  # noqa: N802
        return self._formatted_latex

    @Property(str, notify=formatModeChanged)
    def formatMode(self) -> str:  # noqa: N802
        return self._format_mode

    @Property(str, notify=formatErrorChanged)
    def formatError(self) -> str:  # noqa: N802
        return self._format_error

    @Property(str, notify=imageUrlChanged)
    def imageUrl(self) -> str:  # noqa: N802
        return QUrl.fromLocalFile(self._image_path).toString() if self._image_path else ""

    @Property(str, notify=imageNameChanged)
    def imageName(self) -> str:  # noqa: N802
        return Path(self._image_path).name if self._image_path else "未导入"

    @Property(str, notify=themeModeChanged)
    def themeMode(self) -> str:  # noqa: N802
        return self._theme_mode

    @Property(bool, notify=themeModeChanged)
    def darkMode(self) -> bool:  # noqa: N802
        if self._theme_mode == "dark":
            return True
        if self._theme_mode == "light":
            return False
        app = QCoreApplication.instance()
        return isinstance(app, QGuiApplication) and app.styleHints().colorScheme() == Qt.ColorScheme.Dark

    @Property(bool, notify=autoCopyChanged)
    def autoCopy(self) -> bool:  # noqa: N802
        return self._auto_copy

    @Property(str, notify=globalHotkeyChanged)
    def globalHotkey(self) -> str:  # noqa: N802
        return self._global_hotkey

    @Property(str, notify=globalHotkeyStatusChanged)
    def globalHotkeyStatus(self) -> str:  # noqa: N802
        return self._global_hotkey_status

    @Property(int, notify=historyLimitChanged)
    def historyLimit(self) -> int:  # noqa: N802
        return self._history_limit

    @Property(str, notify=lastDurationChanged)
    def lastDuration(self) -> str:  # noqa: N802
        return self._last_duration

    @Property(str, notify=noticeChanged)
    def notice(self) -> str:
        return self._notice

    @Property(QObject, constant=True)
    def historyModel(self) -> QObject:  # noqa: N802
        return self._history

    def _set_engine(self, state: str, detail: str) -> None:
        if self._engine_state != state:
            self._engine_state = state
            self.engineStateChanged.emit()
        if self._engine_detail != detail:
            self._engine_detail = detail
            self.engineDetailChanged.emit()

    def _set_busy(self, value: bool) -> None:
        if self._busy != value:
            self._busy = value
            self.busyChanged.emit()

    def _set_notice(self, value: str) -> None:
        if self._notice != value:
            self._notice = value
            self.noticeChanged.emit()

    def bind_global_hotkey(self, apply_callback) -> None:
        self._global_hotkey_apply = apply_callback
        success, status = apply_callback(self._global_hotkey)
        self._global_hotkey_status = status
        self.globalHotkeyStatusChanged.emit()
        if not success:
            self._set_notice(status)

    def _set_latex(self, value: str, *, copy: bool = False) -> None:
        if self._latex != value:
            self._latex = value
            self.latexChanged.emit()
        self._refresh_formatted(copy=copy)

    def _refresh_formatted(self, *, copy: bool = False) -> None:
        raw = self._latex.strip()
        if raw.startswith("$$") and raw.endswith("$$") and len(raw) >= 4:
            raw = raw[2:-2]
        elif raw.startswith("$") and raw.endswith("$") and len(raw) >= 2:
            raw = raw[1:-1]

        error = ""
        if not raw:
            formatted = ""
        elif self._format_mode == "raw":
            formatted = raw
        elif self._format_mode == "word":
            formatted = _clean_latex(raw)
        elif self._format_mode == "latex-inline":
            formatted = f"${raw}$"
        elif self._format_mode == "latex-display":
            formatted = f"$${raw}$$"
        else:
            cleaned = _clean_latex(raw)
            try:
                from sympy.parsing.latex import parse_latex

                normalized = re.sub(r"operatorname\*{(\w+)}", r"\1", cleaned)
                formatted = str(parse_latex(normalized, backend="lark"))
            except Exception:
                formatted = cleaned
                error = "SymPy 解析失败"

        if self._formatted_latex != formatted:
            self._formatted_latex = formatted
            self.formattedLatexChanged.emit()
        if self._format_error != error:
            self._format_error = error
            self.formatErrorChanged.emit()
        if copy and self._auto_copy and formatted:
            self._copy_to_clipboard(formatted)

    def _copy_to_clipboard(self, text: str) -> None:
        app = QCoreApplication.instance()
        if isinstance(app, QGuiApplication):
            app.clipboard().setText(text)

    def _start_worker(self) -> None:
        program, arguments = _worker_process_command()
        process = QProcess(self)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("NO_ALBUMENTATIONS_UPDATE", "1")
        process.setProcessEnvironment(environment)
        process.readyReadStandardOutput.connect(self._read_worker_stdout)
        process.readyReadStandardError.connect(self._read_worker_stderr)
        process.errorOccurred.connect(self._worker_error)
        process.finished.connect(self._worker_finished)
        self._process = process
        self._logger.info("Starting OCR worker: %s", program)
        process.start(program, arguments)

    def _read_worker_stdout(self) -> None:
        if not self._process:
            return
        self._stdout_buffer += bytes(self._process.readAllStandardOutput()).decode("utf-8", errors="replace")
        while "\n" in self._stdout_buffer:
            line, self._stdout_buffer = self._stdout_buffer.split("\n", 1)
            if not line.strip():
                continue
            try:
                self._handle_worker_event(json.loads(line))
            except json.JSONDecodeError:
                self._set_notice("识别进程返回了无法解析的信息")

    def _read_worker_stderr(self) -> None:
        if not self._process:
            return
        message = bytes(self._process.readAllStandardError()).decode("utf-8", errors="replace").strip()
        if message:
            self._logger.warning("OCR worker stderr: %s", message)
        if message and "UserWarning" not in message:
            self._set_notice(message.splitlines()[-1][:160])

    def _handle_worker_event(self, event: dict[str, Any]) -> None:
        event_type = event.get("type")
        if event_type == "ready":
            self._logger.info("OCR worker ready in %.2fs", float(event.get("seconds", 0)))
            self._set_engine("ready", f"CPU 引擎已就绪 · 预热 {event.get('seconds', 0):.1f}s")
            if self._pending_image:
                pending, self._pending_image = self._pending_image, ""
                self._predict(pending)
        elif event_type == "result":
            self._logger.info("OCR prediction completed in %.2fs", float(event.get("seconds", 0)))
            self._set_busy(False)
            self._set_engine("ready", "CPU 引擎已就绪")
            self._set_latex(str(event.get("latex", "")), copy=True)
            seconds = float(event.get("seconds", 0.0))
            self._last_duration = f"{seconds:.2f}s"
            self.lastDurationChanged.emit()
            self._record_history(self._latex, self._image_path, self._last_duration)
            self._set_notice("识别完成" + ("，输出已复制" if self._auto_copy else ""))
        elif event_type == "error":
            self._logger.error("OCR worker error: %s", str(event.get("message", "unknown")))
            self._set_busy(False)
            self._set_engine("error", "识别失败，可重试当前图片")
            self._set_notice(str(event.get("message", "未知错误"))[:180])

    def _worker_error(self, _error: QProcess.ProcessError) -> None:
        self._logger.error("OCR worker process error: %s", _error)
        self._set_busy(False)
        self._set_engine("error", "CPU 识别进程启动失败")

    def _worker_finished(self, _code: int, _status: QProcess.ExitStatus) -> None:
        if self._process is not self.sender():
            return
        if self._engine_state != "error":
            self._set_engine("offline", "CPU 识别进程已停止")
        self._logger.info("OCR worker exited with code %s and status %s", _code, _status)
        self._set_busy(False)

    def _send(self, payload: dict[str, Any]) -> None:
        if not self._process or self._process.state() != QProcess.ProcessState.Running:
            self._set_engine("error", "CPU 识别进程不可用")
            return
        self._process.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))

    def _predict(self, path: str) -> None:
        if self._engine_state == "warming":
            self._pending_image = path
            self._set_notice("图片已接收，等待 CPU 引擎完成预热")
            return
        if self._engine_state != "ready":
            self._set_notice("识别引擎尚未就绪")
            return
        self._set_busy(True)
        self._set_engine("busy", "正在解析公式结构")
        self._send(
            {
                "type": "predict",
                "id": uuid.uuid4().hex,
                "path": path,
            }
        )

    def _accept_image(self, path: str) -> bool:
        image_path = Path(path)
        if not image_path.is_file() or image_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
            self._set_notice("请选择 PNG、JPG、JPEG、BMP 或 WebP 图片")
            return False
        self._image_path = str(image_path.resolve())
        self.imageUrlChanged.emit()
        self.imageNameChanged.emit()
        self._predict(self._image_path)
        return True

    @Slot()
    def openImage(self) -> None:  # noqa: N802
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(None, "选择公式图片", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if path:
            self._accept_image(path)

    @Slot(str)
    def openPath(self, url_or_path: str) -> None:  # noqa: N802
        url = QUrl(url_or_path)
        path = url.toLocalFile() if url.isLocalFile() else url_or_path
        self._accept_image(path)

    @Slot()
    def pasteImage(self) -> None:  # noqa: N802
        app = QCoreApplication.instance()
        if not isinstance(app, QGuiApplication):
            return
        clipboard = app.clipboard()
        image = clipboard.image()
        if not image.isNull():
            path = self._cache_dir / f"clipboard-{datetime.now():%Y%m%d-%H%M%S-%f}.png"
            if image.save(str(path), "PNG"):
                self._accept_image(str(path))
            else:
                self._set_notice("无法保存剪贴板图片")
            return
        urls = clipboard.mimeData().urls()
        if urls and urls[0].isLocalFile():
            self._accept_image(urls[0].toLocalFile())
            return
        self._set_notice("剪贴板里没有图片或图片文件")

    @Slot(result=str)
    def canvasImagePath(self) -> str:  # noqa: N802
        """Return a fresh cache path for the handwriting canvas to save into."""
        path = self._cache_dir / f"drawing-{datetime.now():%Y%m%d-%H%M%S-%f}.png"
        return str(path)

    @Slot()
    def clearImage(self) -> None:  # noqa: N802
        """Drop the current image and result, returning to the initial state."""
        self._image_path = ""
        self.imageUrlChanged.emit()
        self.imageNameChanged.emit()
        self._set_latex("")
        if self._last_duration != "—":
            self._last_duration = "—"
            self.lastDurationChanged.emit()
        self._set_notice("离线识别 · 数据仅保存在本机")

    @Slot()
    def captureFormula(self) -> None:  # noqa: N802
        if self._busy:
            self.interruptInference()
            return
        from .capture import ScreenCaptureOverlay

        parent_window = QGuiApplication.focusWindow()
        self._capture_parent_window = parent_window
        if parent_window:
            parent_window.hide()

        output = self._cache_dir / f"capture-{datetime.now():%Y%m%d-%H%M%S-%f}.png"

        def launch() -> None:
            try:
                overlay = ScreenCaptureOverlay(output)
            except Exception as exc:
                self._restore_main_window()
                self._set_notice(f"无法启动区域截图：{exc}")
                return
            self._capture_overlay = overlay
            overlay.captured.connect(self._capture_completed)
            overlay.cancelled.connect(self._capture_cancelled)
            overlay.start()

        QTimer.singleShot(160, launch)

    @Slot(str)
    def _capture_completed(self, path: str) -> None:
        self._capture_overlay = None
        self._restore_main_window()
        self._accept_image(path)

    @Slot()
    def _capture_cancelled(self) -> None:
        self._capture_overlay = None
        self._restore_main_window()
        self._set_notice("已取消区域截图")

    def _restore_main_window(self) -> None:
        window, self._capture_parent_window = self._capture_parent_window, None
        if window:
            window.show()
            window.raise_()
            window.requestActivate()

    @Slot()
    def predictCurrent(self) -> None:  # noqa: N802
        if self._image_path:
            self._predict(self._image_path)
        else:
            self._set_notice("请先截图、打开或粘贴一张公式图片")

    @Slot()
    def interruptInference(self) -> None:  # noqa: N802
        if not self._busy:
            return
        process, self._process = self._process, None
        if process:
            process.blockSignals(True)
            process.kill()
            process.waitForFinished(800)
            process.deleteLater()
        self._pending_image = ""
        self._stdout_buffer = ""
        self._set_busy(False)
        self._set_engine("warming", "识别已中断，正在重启 CPU 引擎")
        self._set_notice("识别已中断")
        self._start_worker()

    @Slot(str)
    def setLatex(self, value: str) -> None:  # noqa: N802
        self._set_latex(value, copy=True)

    @Slot(str)
    def setFormattedLatex(self, value: str) -> None:  # noqa: N802
        if self._formatted_latex != value:
            self._formatted_latex = value
            self.formattedLatexChanged.emit()
        if self._auto_copy and value:
            self._copy_to_clipboard(value)

    @Slot(str)
    def setFormatMode(self, value: str) -> None:  # noqa: N802
        if value not in self._VALID_FORMATS or value == self._format_mode:
            return
        self._format_mode = value
        self._settings.setValue("formatMode", value)
        self.formatModeChanged.emit()
        self._refresh_formatted(copy=True)

    @Slot(str)
    def setThemeMode(self, value: str) -> None:  # noqa: N802
        if value not in self._VALID_THEMES or value == self._theme_mode:
            return
        self._theme_mode = value
        self._settings.setValue("themeMode", value)
        self.themeModeChanged.emit()

    @Slot(bool)
    def setAutoCopy(self, value: bool) -> None:  # noqa: N802
        value = bool(value)
        if value == self._auto_copy:
            return
        self._auto_copy = value
        self._settings.setValue("autoCopy", value)
        self.autoCopyChanged.emit()

    @Slot(str)
    def setGlobalHotkey(self, value: str) -> None:  # noqa: N802
        if value not in self._VALID_GLOBAL_HOTKEYS or value == self._global_hotkey:
            return
        if self._global_hotkey_apply:
            success, status = self._global_hotkey_apply(value)
            self._global_hotkey_status = status
            self.globalHotkeyStatusChanged.emit()
            if not success:
                self._set_notice(status)
                return
        self._global_hotkey = value
        self._settings.setValue("globalHotkey", value)
        self.globalHotkeyChanged.emit()

    @Slot(int)
    def setHistoryLimit(self, value: int) -> None:  # noqa: N802
        value = int(value)
        if value not in self._VALID_HISTORY_LIMITS or value == self._history_limit:
            return
        self._history_limit = value
        self._settings.setValue("historyLimit", value)
        self.historyLimitChanged.emit()
        self._history.trim(value)
        self._save_history()
        self._cleanup_generated_cache()
        self._prune_history_preview_cache()
        self._set_notice(f"历史记录上限已设为 {value} 条")

    @Slot()
    def copyLatex(self) -> None:  # noqa: N802
        text = self._formatted_latex or self._latex
        if not text:
            self._set_notice("当前没有可复制的内容")
            return
        self._copy_to_clipboard(text)
        self._set_notice("输出已复制到剪贴板")

    @Slot(int)
    def copyHistoryFormula(self, row: int) -> None:  # noqa: N802
        entry = self._history.entry(row)
        formula = str(entry.get("formula", "")) if entry else ""
        if not formula:
            self._set_notice("这条历史记录没有可复制的源码")
            return
        self._copy_to_clipboard(formula)
        self._set_notice("LaTeX 源码已复制")

    @Slot(int)
    def removeHistory(self, row: int) -> None:  # noqa: N802
        if not self._history.remove(row):
            return
        self._save_history()
        self._cleanup_generated_cache()
        self._prune_history_preview_cache()
        self._set_notice("已删除这条历史记录")

    @Slot(int)
    def restoreHistory(self, row: int) -> None:  # noqa: N802
        entry = self._history.entry(row)
        if not entry:
            return
        self._image_path = entry.get("image", "") if Path(entry.get("image", "")).is_file() else ""
        self._last_duration = entry.get("duration", "—")
        self._set_latex(entry.get("formula", ""))
        self.imageUrlChanged.emit()
        self.imageNameChanged.emit()
        self.lastDurationChanged.emit()
        self._set_notice("已恢复历史结果")

    @Slot()
    def clearHistory(self) -> None:  # noqa: N802
        self._history.clear()
        self._save_history()
        self._cleanup_generated_cache()
        self._prune_history_preview_cache()
        self._set_notice("本地历史已清空")

    def _record_history(self, formula: str, image: str, duration: str) -> None:
        self._history.prepend(
            {
                "formula": formula,
                "image": image,
                "duration": duration,
                "timestamp": datetime.now().strftime("%m-%d  %H:%M"),
            }
        )
        self._history.trim(self._history_limit)
        self._save_history()
        self._cleanup_generated_cache()
        self._prune_history_preview_cache()
        if self._history_preview_renderer:
            self._history_preview_renderer.request(formula)

    def _queue_existing_history_previews(self) -> None:
        if not self._history_preview_renderer:
            return
        for formula in self._history.formulas():
            self._history_preview_renderer.request(formula)

    def _history_preview_ready(
        self, formula: str, light_path: str, dark_path: str, width: int, height: int
    ) -> None:
        self._history.set_preview_for_formula(formula, light_path, dark_path, width, height)

    def _prune_history_preview_cache(self) -> int:
        if not self._history_preview_renderer:
            return 0
        return self._history_preview_renderer.prune(self._history.formulas())

    def _cleanup_generated_cache(self) -> int:
        """Delete only app-generated screenshots no longer referenced by retained history."""

        try:
            cache_root = self._cache_dir.resolve()
        except OSError:
            return 0
        retained: set[Path] = set()
        for entry in self._history.serializable():
            image = str(entry.get("image", ""))
            if image:
                try:
                    retained.add(Path(image).resolve())
                except OSError:
                    pass
        if self._image_path:
            try:
                retained.add(Path(self._image_path).resolve())
            except OSError:
                pass

        removed = 0
        for pattern in ("capture-*.png", "clipboard-*.png"):
            for path in self._cache_dir.glob(pattern):
                try:
                    resolved = path.resolve()
                    if resolved.parent != cache_root or resolved in retained:
                        continue
                    path.unlink()
                    removed += 1
                except OSError:
                    self._logger.warning("Unable to remove generated cache file: %s", path)
        if removed:
            self._logger.info("Removed %d unreferenced generated image cache files", removed)
        return removed

    @Slot()
    def cleanCache(self) -> None:  # noqa: N802
        removed_images = self._cleanup_generated_cache()
        removed_previews = self._prune_history_preview_cache()
        total = removed_images + removed_previews
        self._set_notice(f"缓存清理完成 · 删除 {total} 个无引用文件")

    @Slot()
    def exportDiagnostics(self) -> None:  # noqa: N802
        from PySide6.QtWidgets import QFileDialog

        from .diagnostics import export_diagnostics_archive

        downloads = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
        default_name = f"pix2tex-diagnostics-{datetime.now():%Y%m%d-%H%M%S}.zip"
        suggested = str(Path(downloads or str(Path.home())) / default_name)
        destination, _ = QFileDialog.getSaveFileName(
            None,
            "导出诊断信息",
            suggested,
            "ZIP archive (*.zip)",
        )
        if not destination:
            return
        try:
            output = export_diagnostics_archive(
                self._data_dir,
                Path(destination),
                settings={
                    "format_mode": self._format_mode,
                    "theme_mode": self._theme_mode,
                    "auto_copy": self._auto_copy,
                    "global_hotkey": self._global_hotkey,
                    "history_limit": self._history_limit,
                },
                runtime_state={
                    "engine_state": self._engine_state,
                    "engine_detail": self._engine_detail,
                    "busy": self._busy,
                },
            )
        except OSError as exc:
            self._logger.exception("Unable to export diagnostic archive")
            self._set_notice(f"诊断信息导出失败：{exc}")
            return
        self._set_notice(f"诊断信息已导出：{output.name}")

    def _load_history(self) -> list[dict[str, Any]]:
        try:
            data = json.loads(self._history_path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def _save_history(self) -> None:
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            self._history_path.write_text(
                json.dumps(self._history.serializable(), ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            self._set_notice("历史记录暂时无法保存")

    @Slot()
    def shutdown(self) -> None:
        if self._capture_overlay:
            self._capture_overlay.close()
            self._capture_overlay = None
        if self._history_preview_renderer:
            self._history_preview_renderer.close()
            self._history_preview_renderer = None
        if not self._process or self._process.state() == QProcess.ProcessState.NotRunning:
            return
        self._send({"type": "shutdown"})
        if not self._process.waitForFinished(1200):
            self._process.kill()
            self._process.waitForFinished(800)
