from __future__ import annotations

import hashlib
import json
from collections import deque
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QImage
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView


class HistoryPreviewRenderer(QObject):
    """Render LaTeX previews sequentially with one hidden MathJax page."""

    rendered = Signal(str, str, str, int, int)

    _CACHE_VERSION = "v1"
    _MAX_WIDTH = 4096
    _MAX_HEIGHT = 2048

    def __init__(self, cache_dir: Path, mathjax_path: Path, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._cache_dir = cache_dir / self._CACHE_VERSION
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._mathjax_base = QUrl.fromLocalFile(str(mathjax_path.parent.resolve()) + "/")
        self._pending: deque[tuple[str, str, Path, Path]] = deque()
        self._queued_keys: set[str] = set()
        self._retained_keys: set[str] = set()
        self._current: tuple[str, str, Path, Path] | None = None
        self._job_id = 0

        self._view = QWebEngineView()
        self._view.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        self._view.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self._view.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self._view.setWindowFlag(Qt.WindowType.Tool, True)
        self._view.setWindowFlag(Qt.WindowType.WindowDoesNotAcceptFocus, True)
        self._view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._view.page().setBackgroundColor(QColor("#FFFFFF"))
        self._view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True
        )
        self._view.resize(1400, 800)
        self._view.titleChanged.connect(self._title_changed)
        self._view.show()

    def request(self, formula: str) -> None:
        formula = formula.strip()
        if not formula:
            return
        key = self._cache_key(formula)
        self._retained_keys.add(key)
        light_path = self._cache_dir / f"{key}-light.png"
        dark_path = self._cache_dir / f"{key}-dark.png"
        cached = QImage(str(light_path)) if light_path.is_file() and dark_path.is_file() else QImage()
        if not cached.isNull():
            QTimer.singleShot(
                0,
                lambda: self.rendered.emit(
                    formula,
                    str(light_path),
                    str(dark_path),
                    cached.width(),
                    cached.height(),
                ),
            )
            return
        if key in self._queued_keys:
            return
        self._queued_keys.add(key)
        self._pending.append((formula, key, light_path, dark_path))
        self._start_next()

    @classmethod
    def _cache_key(cls, formula: str) -> str:
        return hashlib.sha256(f"{cls._CACHE_VERSION}\0{formula}".encode("utf-8")).hexdigest()[:24]

    def prune(self, retained_formulas: list[str]) -> int:
        retained_keys = {self._cache_key(formula.strip()) for formula in retained_formulas if formula.strip()}
        self._retained_keys = retained_keys
        self._pending = deque(job for job in self._pending if job[1] in retained_keys)
        self._queued_keys.intersection_update(retained_keys | ({self._current[1]} if self._current else set()))
        removed = 0
        for path in self._cache_dir.glob("*.png"):
            key = path.name.split("-", 1)[0]
            if key in retained_keys:
                continue
            try:
                path.unlink()
                removed += 1
            except OSError:
                pass
        return removed

    def close(self) -> None:
        self._pending.clear()
        self._queued_keys.clear()
        self._retained_keys.clear()
        self._current = None
        self._view.close()
        self._view.deleteLater()

    def _start_next(self) -> None:
        if self._current is not None or not self._pending:
            return
        self._current = self._pending.popleft()
        formula, _key, _light_path, _dark_path = self._current
        self._job_id += 1
        job_id = self._job_id
        formula_json = json.dumps(formula, ensure_ascii=False)
        html = f"""<!doctype html><html><head><meta charset="utf-8">
<script src="MathJax.js"></script>
<script>MathJax.Hub.Config({{messageStyle:'none',showMathMenu:false,tex2jax:{{preview:'none'}}}});</script>
<style>
html,body{{margin:0;padding:0;background:#fff;overflow:hidden}}
body{{font-size:15px;color:#000;font-family:'Cambria Math',serif}}
#equation{{display:inline-block;white-space:nowrap}}
.MathJax_Display{{margin:0!important}}
</style></head><body><div id="equation"></div><script>
const equation=document.getElementById('equation');
equation.textContent='$$'+{formula_json}+'$$';
MathJax.Hub.Queue(['Typeset',MathJax.Hub,equation],function(){{
  const rect=equation.getBoundingClientRect();
  const scale=Math.min(1,{self._MAX_WIDTH - 20}/Math.max(1,rect.width),{self._MAX_HEIGHT - 20}/Math.max(1,rect.height));
  const width=Math.max(1,Math.ceil(rect.width*scale));
  const height=Math.max(1,Math.ceil(rect.height*scale));
  document.body.style.width=(width+20)+'px';
  document.body.style.height=(height+20)+'px';
  equation.style.position='absolute';equation.style.left='10px';equation.style.top='10px';
  equation.style.transformOrigin='top left';equation.style.transform='scale('+scale+')';
  requestAnimationFrame(function(){{document.title=JSON.stringify({{job:{job_id},w:width+20,h:height+20}});}});
}});
</script></body></html>"""
        self._view.resize(1400, 800)
        self._view.setHtml(html, self._mathjax_base)
        QTimer.singleShot(9000, lambda: self._timeout(job_id))

    def _title_changed(self, title: str) -> None:
        if self._current is None:
            return
        try:
            payload = json.loads(title)
            job_id = int(payload["job"])
            width = max(1, min(self._MAX_WIDTH, int(payload["w"])))
            height = max(1, min(self._MAX_HEIGHT, int(payload["h"])))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return
        if job_id != self._job_id:
            return
        self._view.resize(width, height)
        QTimer.singleShot(260, lambda: self._capture(job_id))

    def _capture(self, job_id: int) -> None:
        if self._current is None or job_id != self._job_id:
            return
        formula, key, light_path, dark_path = self._current
        if key not in self._retained_keys:
            self._finish_current(key)
            return
        image = self._view.grab().toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        if image.isNull() or not self._save_variants(image, light_path, dark_path):
            self._finish_current(key)
            return
        self.rendered.emit(
            formula,
            str(light_path),
            str(dark_path),
            image.width(),
            image.height(),
        )
        self._finish_current(key)

    @staticmethod
    def _save_variants(source: QImage, light_path: Path, dark_path: Path) -> bool:
        width, height = source.width(), source.height()
        light = QImage(width, height, QImage.Format.Format_RGBA8888)
        dark = QImage(width, height, QImage.Format.Format_RGBA8888)
        light.fill(Qt.GlobalColor.transparent)
        dark.fill(Qt.GlobalColor.transparent)
        light_ink = QColor("#191C1E")
        dark_ink = QColor("#F0F1F2")
        for y in range(height):
            for x in range(width):
                pixel = source.pixelColor(x, y)
                coverage = 255 - round(
                    0.2126 * pixel.red() + 0.7152 * pixel.green() + 0.0722 * pixel.blue()
                )
                if coverage <= 0:
                    continue
                light_ink.setAlpha(coverage)
                dark_ink.setAlpha(coverage)
                light.setPixelColor(x, y, light_ink)
                dark.setPixelColor(x, y, dark_ink)
        return light.save(str(light_path), "PNG") and dark.save(str(dark_path), "PNG")

    def _timeout(self, job_id: int) -> None:
        if self._current is None or job_id != self._job_id:
            return
        self._finish_current(self._current[1])

    def _finish_current(self, key: str) -> None:
        self._queued_keys.discard(key)
        self._current = None
        QTimer.singleShot(0, self._start_next)
