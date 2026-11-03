"""Заглушка глобальных хоткеев."""

from __future__ import annotations

from ..base import NullHotkey

GlobalHotkey = NullHotkey


def create_hotkey(sequence: str, hotkey_id: int):
    return NullHotkey()
