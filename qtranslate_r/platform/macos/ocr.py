"""Заглушка распознавания текста."""

from __future__ import annotations

from ...localization import tr
from ..base import OcrError


def available_languages() -> list[str]:
    return []


def language_tag(code: str) -> str:
    return code


def pick_language(preferred: str = "") -> str:
    raise OcrError(tr("ocr.no_language"), kind="language")


def recognize(image_path, preferred: str = ""):
    raise OcrError(tr("ocr.unavailable"), kind="unavailable")
