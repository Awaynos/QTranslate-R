"""Заглушка работы с выделением."""

from __future__ import annotations


def copy_selection() -> bool:
    return False


def capture_selection() -> str | None:
    return None


def set_clipboard(text: str) -> bool:
    return False


def paste_clipboard() -> None:
    pass
