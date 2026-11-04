"""Глобальные хоткеи Windows по умолчанию."""

from __future__ import annotations


def defaults() -> dict[str, str]:
    return {
        "quick_translate": "Ctrl+Q",
        "replace_selection": "Ctrl+1",
        "ocr": "Ctrl+I",
    }
