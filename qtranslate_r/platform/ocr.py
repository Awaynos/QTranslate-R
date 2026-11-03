"""Выбор реализации распознавания текста."""

from __future__ import annotations

import sys

from .base import OcrError

if sys.platform == "win32":
    from .windows.ocr import available_languages, language_tag, pick_language, recognize
elif sys.platform == "darwin":
    from .macos.ocr import available_languages, language_tag, pick_language, recognize
else:
    from .linux.ocr import available_languages, language_tag, pick_language, recognize

__all__ = [
    "OcrError",
    "available_languages",
    "language_tag",
    "pick_language",
    "recognize",
]
