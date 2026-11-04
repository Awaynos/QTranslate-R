"""Замена выделенного текста переводом (по умолчанию Ctrl+1)."""

from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtGui import QGuiApplication

from .config.settings import Settings
from .core.translation import TranslationService
from .hotkeys import binding
from .platform.hotkey import create_hotkey
from .platform.selection import (
    capture_selection,
    copy_selection,
    paste_clipboard,
    set_clipboard,
)
from .ui.loading import CursorLoadingIndicator
from .ui.workers import TranslateWorker


class _Signals(QObject):
    done = Signal(bool)


class _CaptureSignals(QObject):
    done = Signal(object)


class _CaptureWorker(QRunnable):
    """Захватить выделение в фоне."""

    def __init__(self) -> None:
        super().__init__()
        self.signals = _CaptureSignals()

    @Slot()
    def run(self) -> None:
        text = capture_selection()
        if text is None:
            self.signals.done.emit(copy_selection())
        else:
            self.signals.done.emit(text)


class _RunWorker(QRunnable):
    """Выполнить небольшую операцию в фоне (вставка)."""

    def __init__(self, action) -> None:
        super().__init__()
        self.signals = _Signals()
        self._action = action

    @Slot()
    def run(self) -> None:
        try:
            ok = bool(self._action())
        except Exception:  # noqa: BLE001 — молча, это фоновая операция
            ok = False
        self.signals.done.emit(ok)


class InlineReplaceController(QObject):
    def __init__(
        self,
        *,
        settings: Settings,
        service: TranslationService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._service = service
        self._pool = QThreadPool.globalInstance()
        self._token = 0
        self._hotkey = None
        self._workers: list[QRunnable] = []
        self._loading = CursorLoadingIndicator(settings)
        self.start()

    def start(self) -> None:
        self.stop()
        self._hotkey = create_hotkey(binding(self._settings, "replace_selection"), 0x5160)
        self._hotkey.activated.connect(self._on_hotkey)
        self._hotkey.start()

    def stop(self) -> None:
        if self._hotkey is not None:
            self._hotkey.stop()
            self._hotkey = None

    def _track(self, worker: QRunnable) -> None:
        self._workers.append(worker)
        del self._workers[:-4]

    def _on_hotkey(self) -> None:
        self._loading.show_loading()
        worker = _CaptureWorker()
        worker.signals.done.connect(self._on_captured)
        self._track(worker)
        self._pool.start(worker)

    def _on_captured(self, result) -> None:
        if isinstance(result, str):
            ok = bool(result)
            text = result
        else:
            ok = bool(result)
            text = QGuiApplication.clipboard().text()
        if not ok:
            self._loading.hide_loading()
            return
        text = text.strip()
        if not text:
            self._loading.hide_loading()
            return

        target = self._settings.target_language or "en"
        enabled = list(self._settings.enabled_providers) or ["google"]
        primary = self._settings.primary_provider
        primary = [primary] if primary in enabled else enabled[:1]

        self._token += 1
        worker = TranslateWorker(
            self._service,
            self._token,
            text,
            "auto",
            target,
            primary,
            native=self._settings.native_language or None,
            second=self._settings.second_language or None,
        )
        worker.signals.finished.connect(self._on_translated)
        self._track(worker)
        self._pool.start(worker)

    def _on_translated(self, token: int, results: list) -> None:
        if token != self._token:
            return
        best = next((result for result in results if result.ok), None)
        if best is None:
            self._loading.hide_loading()
            return

        if not set_clipboard(best.text):
            QGuiApplication.clipboard().setText(best.text)
        worker = _RunWorker(paste_clipboard)
        self._track(worker)
        self._pool.start(worker)
        self._loading.hide_loading()
