"""Выбор реализации глобальных горячих клавиш."""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from .windows.hotkey import GlobalHotkey, create_hotkey
elif sys.platform == "darwin":
    from .macos.hotkey import GlobalHotkey, create_hotkey
else:
    from .linux.hotkey import GlobalHotkey, create_hotkey

__all__ = ["GlobalHotkey", "create_hotkey"]
