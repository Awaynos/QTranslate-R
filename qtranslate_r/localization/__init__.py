"""Локализация интерфейса."""

from __future__ import annotations

import json
import locale
from pathlib import Path

FALLBACK = "en"

_strings: dict[str, str] = {}
_current = FALLBACK


def languages_dir() -> Path:
    from ..config.paths import resource

    return resource("languages")


def available_languages() -> list[str]:
    directory = languages_dir()
    if not directory.is_dir():
        return [FALLBACK]
    codes = sorted(path.stem for path in directory.glob("*.json"))
    return codes or [FALLBACK]


def current_language() -> str:
    return _current


def set_language(code: str) -> str:
    """Включить язык. Пустой код — определить по системе. Возвращает выбранный код."""
    global _strings, _current

    requested = (code or "").strip() or system_language()
    path = languages_dir() / f"{requested}.json"
    if not path.is_file():
        path = languages_dir() / f"{FALLBACK}.json"
        requested = FALLBACK
    _strings = _load(path)
    _current = requested
    return requested


def tr(key: str, **params) -> str:
    if not _strings:
        set_language("")
    text = _strings.get(key, key)
    if params:
        try:
            return text.format(**params)
        except (KeyError, IndexError):
            return text
    return text


def has(key: str) -> bool:
    return key in _strings


def system_language() -> str:
    code = _windows_ui_language()
    if code:
        return code
    for getter in (lambda: locale.getdefaultlocale()[0], lambda: locale.getlocale()[0]):
        try:
            name = getter() or ""
        except (ValueError, TypeError):
            name = ""
        if name:
            candidate = name.split("_")[0].split("-")[0].lower()
            if 2 <= len(candidate) <= 3 and candidate.isalpha():
                return candidate
    return FALLBACK


# Windows отдаёт полные названия вроде "Russian_Russia", поэтому берём LANGID.
_LANGID = {
    0x01: "ar", 0x04: "zh", 0x05: "cs", 0x06: "da", 0x07: "de", 0x08: "el",
    0x09: "en", 0x0A: "es", 0x0B: "fi", 0x0C: "fr", 0x0D: "nl", 0x0E: "hu",
    0x0F: "is", 0x10: "it", 0x11: "ja", 0x12: "ko", 0x13: "nl", 0x14: "no",
    0x15: "pl", 0x16: "pt", 0x18: "ro", 0x19: "ru", 0x1A: "hr", 0x1B: "sk",
    0x1C: "sq", 0x1D: "sv", 0x1E: "th", 0x1F: "tr", 0x20: "ur", 0x21: "id",
    0x22: "uk", 0x23: "be", 0x24: "sl", 0x25: "et", 0x26: "lv", 0x27: "lt",
    0x29: "fa", 0x2A: "vi", 0x2B: "hy", 0x2D: "az", 0x2E: "eu", 0x2F: "mk",
    0x32: "ka", 0x34: "hi", 0x35: "ms", 0x36: "kk", 0x37: "sw", 0x39: "ta",
    0x3E: "bn", 0x3F: "pa", 0x40: "gu", 0x45: "ta", 0x4E: "mr", 0x56: "te",
    0x5A: "sr",
}


def _windows_ui_language() -> str | None:
    try:
        import ctypes

        langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
    except (AttributeError, OSError):
        return None
    return _LANGID.get(langid & 0x3FF)


def _load(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {key: value for key, value in data.items() if isinstance(value, str)}
