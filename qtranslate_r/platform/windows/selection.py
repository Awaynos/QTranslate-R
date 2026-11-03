"""Захват выделенного в другом приложении текста."""

from __future__ import annotations

import ctypes
import sys
import time

_IS_WINDOWS = sys.platform == "win32"

VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_MENU = 0x12  # Alt
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_C = 0x43
VK_V = 0x56
KEYEVENTF_KEYUP = 0x0002

CAPTURE_TIMEOUT = 0.8


def _key_event(vk: int, flags: int = 0) -> None:
    ctypes.windll.user32.keybd_event(vk, 0, flags, 0)


def _release_modifiers() -> None:
    for vk in (VK_CONTROL, VK_SHIFT, VK_MENU, VK_LWIN, VK_RWIN):
        _key_event(vk, KEYEVENTF_KEYUP)


def copy_selection() -> bool:
    """Отправить Ctrl+C и вернуть True, если буфер обмена изменился."""
    if not _IS_WINDOWS:
        return False

    user32 = ctypes.windll.user32
    before = user32.GetClipboardSequenceNumber()

    _release_modifiers()
    time.sleep(0.05)
    _key_event(VK_CONTROL)
    _key_event(VK_C)
    _key_event(VK_C, KEYEVENTF_KEYUP)
    _key_event(VK_CONTROL, KEYEVENTF_KEYUP)

    deadline = time.time() + CAPTURE_TIMEOUT
    while time.time() < deadline:
        if user32.GetClipboardSequenceNumber() != before:
            return True
        time.sleep(0.02)
    return False


def paste_clipboard() -> None:
    """Отправить Ctrl+V в активное окно (для замены выделенного текста)."""
    if not _IS_WINDOWS:
        return

    _release_modifiers()
    time.sleep(0.05)
    _key_event(VK_CONTROL)
    _key_event(VK_V)
    _key_event(VK_V, KEYEVENTF_KEYUP)
    _key_event(VK_CONTROL, KEYEVENTF_KEYUP)
