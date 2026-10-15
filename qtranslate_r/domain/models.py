"""Запрос и результат перевода."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TranslationRequest:
    text: str
    source: str
    target: str


@dataclass
class TranslationResult:
    """Ответ одного сервиса."""

    provider_id: str
    provider_name: str
    text: str = ""
    detected_source: str | None = None
    error: str | None = None
    elapsed_ms: int = 0
    alternatives: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.text.strip())


@dataclass
class DictionaryEntry:
    """Статья словаря: одна часть речи и её определения."""

    word: str
    source: str
    language: str
    part_of_speech: str = ""
    definitions: list[str] = field(default_factory=list)
