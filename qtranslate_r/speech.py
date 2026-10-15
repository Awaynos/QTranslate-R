"""Озвучка: запуск выбранного TTS-сервиса в фоне и управление воспроизведением."""

from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from .config.settings import Settings
from .core.setup import tts_service
from .domain.errors import ServiceError
from .localization import tr
from .services.base import TextToSpeech
from .services.registry import ServiceRegistry


class _SpeakSignals(QObject):
    started = Signal()
    finished = Signal(str)  # пусто при успехе, иначе текст ошибки


class _SpeakWorker(QRunnable):
    def __init__(self, tts: TextToSpeech, text: str, language: str) -> None:
        super().__init__()
        self.signals = _SpeakSignals()
        self._tts = tts
        self._text = text
        self._language = language

    @Slot()
    def run(self) -> None:
        self.signals.started.emit()
        error = ""
        try:
            self._tts.speak(self._text, self._language)
        except ServiceError as exc:
            error = str(exc)
        except Exception as exc:  # noqa: BLE001 — сообщаем пользователю
            error = tr("errors.speech", message=exc)
        self.signals.finished.emit(error)


class SpeechController(QObject):
    """Следит, что играет сейчас, и позволяет прервать озвучку."""

    playingChanged = Signal(bool)
    errorOccurred = Signal(str)

    def __init__(self, *, settings: Settings, registry: ServiceRegistry, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._registry = registry
        self._pool = QThreadPool.globalInstance()
        self._current: TextToSpeech | None = None
        self._worker = None
        self._playing = False

    def is_playing(self) -> bool:
        return self._playing

    def toggle(self, text: str, language: str) -> None:
        if self._playing:
            self.stop()
        else:
            self.speak(text, language)

    def speak(self, text: str, language: str) -> None:
        if not text.strip():
            return
        service = tts_service(self._registry, self._settings.tts_provider)
        if service is None:
            self.errorOccurred.emit(tr("errors.no_tts"))
            return

        self._current = service
        self._playing = True
        self.playingChanged.emit(True)

        worker = _SpeakWorker(service, text, language)
        worker.signals.finished.connect(self._on_finished)
        self._worker = worker  # держим ссылку до завершения
        self._pool.start(worker)

    def stop(self) -> None:
        if self._current is not None:
            self._current.stop()

    def _on_finished(self, error: str) -> None:
        self._playing = False
        self._current = None
        self.playingChanged.emit(False)
        if error:
            self.errorOccurred.emit(error)
