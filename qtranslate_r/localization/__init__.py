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
    code = _ui_language()
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


def _ui_language() -> str | None:
    try:
        from ..platform.locale import ui_language
    except ImportError:
        return None
    return ui_language()


def _load(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {key: value for key, value in data.items() if isinstance(value, str)}
