"""Быстрый перевод по глобальному хоткею (Ctrl+Q)."""

from __future__ import annotations

import sys

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtGui import QGuiApplication

from .config.settings import Settings
from .core.translation import TranslationService
from .domain.language import AUTO_PAIR
from .hotkeys import binding, combination, virtual_key
from .localization import tr
from .platform.hotkey import GlobalHotkey
from .platform.selection import copy_selection
from .speech import SpeechController
from .ui.loading import CursorLoadingIndicator
from .ui.quick_popup import QuickTranslatePopup
from .ui.workers import TranslateWorker


class _CaptureSignals(QObject):
    done = Signal(bool)


class _CaptureWorker(QRunnable):
    """Скопировать выделение в буфер, не занимая UI-поток."""

    def __init__(self) -> None:
        super().__init__()
        self.signals = _CaptureSignals()

    @Slot()
    def run(self) -> None:
        self.signals.done.emit(copy_selection())


class QuickTranslateController(QObject):
    def __init__(
        self,
        *,
        settings: Settings,
        service: TranslationService,
        speech: SpeechController,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._service = service
        self._speech = speech
        self._pool = QThreadPool.globalInstance()
        self._popup = QuickTranslatePopup()
        self._popup.speakRequested.connect(self._speech.speak)
        self._loading = CursorLoadingIndicator(settings)
        self._token = 0
        self._target = "en"
        self._capture_worker = None
        self._active_worker = None
        self._hotkey: GlobalHotkey | None = None
        self.start()

    def start(self) -> None:
        self.stop()
        if not self._settings.quick_translate_enabled:
            return
        if sys.platform != "win32":
            return
        parsed = combination(binding(self._settings, "quick_translate"))
        if parsed is None:
            return
        qt_key, ctrl, shift, alt, win = parsed
        vk = virtual_key(qt_key)
        if vk is None:
            return
        self._hotkey = GlobalHotkey(vk, ctrl=ctrl, shift=shift, alt=alt, win=win, hotkey_id=0x5154)
        self._hotkey.activated.connect(self._on_hotkey)
        self._hotkey.start()

    def stop(self) -> None:
        if self._hotkey is not None:
            self._hotkey.stop()
            self._hotkey = None

    def _on_hotkey(self) -> None:
        self._loading.show_loading()
        worker = _CaptureWorker()
        worker.signals.done.connect(self._on_captured)
        self._capture_worker = worker
        self._pool.start(worker)

    def _on_captured(self, ok: bool) -> None:
        if not ok:
            self._loading.hide_loading()
            self._popup.show_error(tr("popup.select_text"))
            return
        text = QGuiApplication.clipboard().text().strip()
        if not text:
            self._loading.hide_loading()
            self._popup.show_error(tr("popup.no_selection"))
            return
        self._translate(text)

    def _translate(self, text: str) -> None:
        target = self._settings.target_language or "en"
        self._target = target
        enabled = list(self._settings.enabled_providers) or ["google"]
        primary = self._settings.primary_provider
        primary = [primary] if primary in enabled else enabled[:1]

        self._token += 1
        self._popup.show_loading(text)

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
        worker.signals.finished.connect(self._on_result)
        worker.signals.failed.connect(self._on_failed)
        self._active_worker = worker
        self._pool.start(worker)

    def _on_result(self, token: int, results: list) -> None:
        if token != self._token:
            return
        self._loading.hide_loading()
        if not results:
            self._popup.show_error(tr("popup.failed"))
            return

        result = results[0]
        language = self._target
        if language == AUTO_PAIR:
            native = self._settings.native_language
            language = (
                self._settings.second_language
                if result.detected_source == native
                else native
            )
        self._popup.show_result(result, language)

    def _on_failed(self, token: int, message: str) -> None:
        if token != self._token:
            return
        self._loading.hide_loading()
        self._popup.show_error(tr("popup.error", message=message))
