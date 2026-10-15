"""Глобальный хоткей через Win32 RegisterHotKey."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from PySide6.QtCore import QThread, Signal

_IS_WINDOWS = sys.platform == "win32"

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000


class GlobalHotkey(QThread):
    activated = Signal()

    def __init__(
        self,
        virtual_key: int,
        *,
        ctrl: bool = False,
        shift: bool = False,
        alt: bool = False,
        win: bool = False,
        hotkey_id: int = 1,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._vk = virtual_key
        self._id = hotkey_id
        self._modifiers = (
            (MOD_CONTROL if ctrl else 0)
            | (MOD_SHIFT if shift else 0)
            | (MOD_ALT if alt else 0)
            | (MOD_WIN if win else 0)
        )
        self._thread_id = 0
        self._registered = False

    @property
    def registered(self) -> bool:
        return self._registered

    def run(self) -> None:
        if not _IS_WINDOWS:
            return
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        self._thread_id = kernel32.GetCurrentThreadId()
        self._registered = bool(
            user32.RegisterHotKey(None, self._id, self._modifiers | MOD_NOREPEAT, self._vk)
        )
        if not self._registered:
            return

        message = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
            if message.message == WM_HOTKEY and message.wParam == self._id:
                self.activated.emit()

        user32.UnregisterHotKey(None, self._id)
        self._registered = False

    def stop(self) -> None:
        """Корректно завершить поток, вытолкнув WM_QUIT в его цикл сообщений."""
        if _IS_WINDOWS and self._thread_id:
            ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        self.wait(1000)

