"""Язык интерфейса ОС в Linux."""

from __future__ import annotations

import os


def _code(value: str) -> str | None:
    for item in value.split(":"):
        raw = item.strip().split(".")[0].split("@")[0]
        if not raw or raw in {"C", "POSIX"}:
            continue
        parts = raw.replace("-", "_").split("_")
        if not parts or not parts[0]:
            continue
        language = parts[0].lower()
        if len(parts) > 1:
            region = parts[1].upper()
            if language == "pt" and region == "BR":
                return "pt-BR"
            if language == "zh" and region in {"TW", "HK"}:
                return "zh"
        return language
    return None


def ui_language() -> str | None:
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(variable)
        if value:
            code = _code(value)
            if code:
                return code
    return None
