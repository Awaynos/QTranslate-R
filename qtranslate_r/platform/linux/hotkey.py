"""Глобальные хоткеи Linux: X11 через XGrabKey, Wayland через бинды DE."""

from __future__ import annotations

import ctypes.util

from ..base import NullHotkey
from .env import session_type

GlobalHotkey = NullHotkey


def available() -> bool:
    return session_type() == "x11" and bool(ctypes.util.find_library("X11"))


def create_hotkey(sequence: str, hotkey_id: int):
    if session_type() == "x11":
        from .x11_hotkey import X11Hotkey

        return X11Hotkey(sequence, hotkey_id)
    return NullHotkey()
