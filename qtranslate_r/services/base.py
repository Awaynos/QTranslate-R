"""Базовые интерфейсы сервисов."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from ..domain.models import DictionaryEntry, TranslationRequest, TranslationResult


class ServiceRole(str, Enum):
    TRANSLATOR = "translator"
    TTS = "tts"
    OCR = "ocr"
    SPELL_CHECKER = "spell_checker"
    DICTIONARY = "dictionary"
    IMAGE_SEARCH = "image_search"


class Service(ABC):
    id: str = ""
    name: str = ""
    role: ServiceRole = ServiceRole.TRANSLATOR
    needs_config: bool = False

    def configure(self, options: dict) -> None:
        """Применить настройки сервиса (ключ, адрес и т.п.)."""

    def validate(self) -> None:
        """Проверить, что сервис настроен. Бросает ServiceError."""


class Translator(Service):
    role = ServiceRole.TRANSLATOR
    # Поддерживает ли сервис source="auto".
    supports_auto: bool = True
    max_characters: int = 0

    @abstractmethod
    def translate(self, request: TranslationRequest) -> TranslationResult:
        raise NotImplementedError


class TextToSpeech(Service):
    """Сервис озвучки текста."""

    role = ServiceRole.TTS

    def speak(self, text: str, language: str) -> None:
        """Прочитать текст вслух. Блокирует поток до конца воспроизведения."""
        raise NotImplementedError

    def stop(self) -> None:
        """Прервать текущее воспроизведение, если оно идёт."""


class Dictionary(Service):
    """Сервис словаря: определения слова."""

    role = ServiceRole.DICTIONARY

    def lookup(self, word: str, language: str, target_language: str) -> list[DictionaryEntry]:
        """Вернуть статьи для слова. Ошибки — через ServiceError."""
        raise NotImplementedError
