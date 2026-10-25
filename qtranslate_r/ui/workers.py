"""Фоновый перевод, чтобы не морозить интерфейс."""

from __future__ import annotations

import threading

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from ..core.documents import DocumentCancelled, DocumentTranslator
from ..core.translation import TranslationService
from ..services.base import Dictionary


class WorkerSignals(QObject):
    finished = Signal(int, object)  # token, list[TranslationResult]
    failed = Signal(int, str)


class TranslateWorker(QRunnable):
    def __init__(
        self,
        service: TranslationService,
        token: int,
        text: str,
        source: str,
        target: str,
        provider_ids: list[str],
        *,
        native: str | None = None,
        second: str | None = None,
    ) -> None:
        super().__init__()
        self.signals = WorkerSignals()
        self._service = service
        self._token = token
        self._text = text
        self._source = source
        self._target = target
        self._provider_ids = provider_ids
        self._native = native
        self._second = second

    @Slot()
    def run(self) -> None:
        try:
            results = self._service.translate(
                self._text,
                self._source,
                self._target,
                self._provider_ids,
                native=self._native,
                second=self._second,
            )
        except Exception as exc:  # noqa: BLE001 — показываем пользователю
            self.signals.failed.emit(self._token, str(exc))
            return
        self.signals.finished.emit(self._token, results)


class DictionaryWorker(QRunnable):
    """Ищет слово в словаре в фоне."""

    def __init__(
        self,
        dictionary: Dictionary,
        token: int,
        word: str,
        language: str,
        target_language: str,
    ) -> None:
        super().__init__()
        self.signals = WorkerSignals()
        self._dictionary = dictionary
        self._token = token
        self._word = word
        self._language = language
        self._target_language = target_language

    @Slot()
    def run(self) -> None:
        try:
            entries = self._dictionary.lookup(self._word, self._language, self._target_language)
        except Exception as exc:  # noqa: BLE001 — показываем пользователю
            self.signals.failed.emit(self._token, str(exc))
            return
        self.signals.finished.emit(self._token, entries)


class OcrSignals(QObject):
    finished = Signal(int, str, str)  # токен, текст, язык
    failed = Signal(int, str)


class OcrWorker(QRunnable):
    """Распознавание текста с изображения в фоновом потоке."""

    def __init__(self, token: int, image_path, language: str) -> None:
        super().__init__()
        self.signals = OcrSignals()
        self._token = token
        self._path = image_path
        self._language = language

    @Slot()
    def run(self) -> None:
        from ..platform.ocr import OcrError, recognize

        try:
            text, language = recognize(self._path, self._language)
        except OcrError as exc:
            self._cleanup()
            self.signals.failed.emit(self._token, str(exc))
            return
        except Exception as exc:  # noqa: BLE001 — ошибки платформы
            self._cleanup()
            self.signals.failed.emit(self._token, str(exc))
            return
        self._cleanup()
        self.signals.finished.emit(self._token, text, language)

    def _cleanup(self) -> None:
        try:
            self._path.unlink()
        except OSError:
            pass


class DocumentSignals(QObject):
    progress = Signal(int, int, str)  # сделано, всего, этап
    finished = Signal(str)            # путь к результату
    failed = Signal(str)
    cancelled = Signal()


class DocumentWorker(QRunnable):
    """Переводит документ в фоне, сообщая прогресс и поддерживая отмену."""

    def __init__(
        self,
        translator: DocumentTranslator,
        input_path,
        output_path,
        source: str,
        target: str,
    ) -> None:
        super().__init__()
        self.signals = DocumentSignals()
        self._translator = translator
        self._input = input_path
        self._output = output_path
        self._source = source
        self._target = target
        self._cancel = threading.Event()

    def cancel(self) -> None:
        self._cancel.set()

    @Slot()
    def run(self) -> None:
        try:
            self._translator.translate_file(
                self._input,
                self._output,
                self._source,
                self._target,
                progress=lambda done, total, stage: self.signals.progress.emit(done, total, stage),
                cancel=self._cancel.is_set,
            )
        except DocumentCancelled:
            self.signals.cancelled.emit()
            return
        except Exception as exc:  # noqa: BLE001 — показываем пользователю
            self.signals.failed.emit(str(exc))
            return
        self.signals.finished.emit(str(self._output))
