"""Модели и типы предметной области."""

from .language import AUTO, LANGUAGES, Language, all_languages, language_name
from .models import TranslationRequest, TranslationResult

__all__ = [
    "AUTO",
    "LANGUAGES",
    "Language",
    "all_languages",
    "language_name",
    "TranslationRequest",
    "TranslationResult",
]
