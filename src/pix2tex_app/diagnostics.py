from __future__ import annotations

import importlib.metadata
import json
import logging
import platform
import re
import sys
import threading
import traceback
import zipfile
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from PySide6.QtCore import QtMsgType, qInstallMessageHandler


LOGGER_NAME = "pix2tex_studio"
_configured_log_path: Path | None = None
_previous_exception_hook = None
_previous_thread_hook = None
_previous_qt_handler = None


def configure_crash_logging(data_dir: Path) -> Path:
    """Install rotating file, Python exception, thread, and Qt message logging."""

    global _configured_log_path, _previous_exception_hook, _previous_thread_hook, _previous_qt_handler
    if _configured_log_path is not None:
        return _configured_log_path

    log_dir = data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "pix2tex-studio.log"
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handler = RotatingFileHandler(
        log_path,
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)

    _previous_exception_hook = sys.excepthook

    def exception_hook(exc_type, exc_value, exc_traceback) -> None:
        logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        if _previous_exception_hook:
            _previous_exception_hook(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_hook

    if hasattr(threading, "excepthook"):
        _previous_thread_hook = threading.excepthook

        def thread_hook(args) -> None:
            logger.critical(
                "Uncaught thread exception in %s",
                getattr(args.thread, "name", "unknown"),
                exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
            )
            if _previous_thread_hook:
                _previous_thread_hook(args)

        threading.excepthook = thread_hook

    _previous_qt_handler = qInstallMessageHandler(_qt_message_handler)
    _configured_log_path = log_path
    logger.info(
        "Application logging started | Python %s | %s",
        platform.python_version(),
        platform.platform(),
    )
    return log_path


def _qt_message_handler(message_type, context, message: str) -> None:
    logger = logging.getLogger(LOGGER_NAME)
    level = {
        QtMsgType.QtDebugMsg: logging.DEBUG,
        QtMsgType.QtInfoMsg: logging.INFO,
        QtMsgType.QtWarningMsg: logging.WARNING,
        QtMsgType.QtCriticalMsg: logging.ERROR,
        QtMsgType.QtFatalMsg: logging.CRITICAL,
    }.get(message_type, logging.INFO)
    location = ""
    if context and getattr(context, "file", None):
        location = f" ({context.file}:{getattr(context, 'line', 0)})"
    logger.log(level, "Qt: %s%s", message, location)
    if _previous_qt_handler:
        _previous_qt_handler(message_type, context, message)


def _package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def _history_summary(history_path: Path) -> dict[str, Any]:
    try:
        entries = json.loads(history_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        entries = []
    if not isinstance(entries, list):
        entries = []
    timestamps = [str(item.get("timestamp", "")) for item in entries if isinstance(item, dict)]
    return {
        "count": len(entries),
        "first_timestamp": timestamps[-1] if timestamps else "",
        "latest_timestamp": timestamps[0] if timestamps else "",
        "content_included": False,
    }


def _directory_summary(directory: Path, patterns: tuple[str, ...]) -> dict[str, int]:
    files: list[Path] = []
    if directory.is_dir():
        for pattern in patterns:
            files.extend(path for path in directory.glob(pattern) if path.is_file())
    return {
        "file_count": len(set(files)),
        "bytes": sum(path.stat().st_size for path in set(files)),
    }


def _sanitized_log_text(path: Path, data_dir: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    replacements = {
        str(Path.home()): "%USERPROFILE%",
        str(data_dir): "%APP_DATA%",
    }
    for original, replacement in replacements.items():
        if original:
            text = text.replace(original, replacement)
            text = text.replace(original.replace("\\", "/"), replacement)
    # Redact any remaining absolute Windows path, including external source images.
    return re.sub(r"(?i)\b[A-Z]:[\\/][^\r\n\t\"']+", "<local-path>", text)


def export_diagnostics_archive(
    data_dir: Path,
    destination: Path,
    *,
    settings: dict[str, Any],
    runtime_state: dict[str, Any],
) -> Path:
    """Write a privacy-safe diagnostic ZIP without formulas, screenshots, or image paths."""

    destination = destination.with_suffix(".zip")
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "privacy": {
            "formula_content_included": False,
            "screenshots_included": False,
            "image_paths_included": False,
            "logs_sanitized": True,
        },
        "system": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": platform.python_version(),
        },
        "packages": {
            "pix2tex": _package_version("pix2tex"),
            "torch": _package_version("torch"),
            "PySide6": _package_version("PySide6"),
            "Pillow": _package_version("Pillow"),
            "latex2sympy2": _package_version("latex2sympy2"),
        },
        "settings": settings,
        "runtime_state": runtime_state,
        "history": _history_summary(data_dir / "history.json"),
        "generated_image_cache": _directory_summary(
            data_dir / "cache", ("capture-*.png", "clipboard-*.png")
        ),
        "history_preview_cache": _directory_summary(
            data_dir / "history-previews" / "v1", ("*.png",)
        ),
    }

    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("diagnostics.json", json.dumps(payload, ensure_ascii=False, indent=2))
        log_dir = data_dir / "logs"
        if log_dir.is_dir():
            for log_path in sorted(log_dir.glob("pix2tex-studio.log*")):
                if log_path.is_file():
                    archive.writestr(
                        f"logs/{log_path.name}",
                        _sanitized_log_text(log_path, data_dir),
                    )
    logging.getLogger(LOGGER_NAME).info("Diagnostic archive exported to %s", destination)
    return destination


def log_exception(context: str) -> None:
    logging.getLogger(LOGGER_NAME).error("%s\n%s", context, traceback.format_exc())
