"""Глобальные хоткеи Linux по умолчанию.

Ctrl+Q, Ctrl+1 и Ctrl+I в Linux заняты почти во всех приложениях,
поэтому используются сочетания с Alt.
"""

from __future__ import annotations


def defaults() -> dict[str, str]:
    return {
        "quick_translate": "Ctrl+Alt+Q",
        "replace_selection": "Ctrl+Alt+1",
        "ocr": "Ctrl+Alt+I",
    }
