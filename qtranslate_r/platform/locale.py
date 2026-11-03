"""Выбор определения языка интерфейса."""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from .windows.locale import ui_language
elif sys.platform == "darwin":
    from .macos.locale import ui_language
else:
    from .linux.locale import ui_language

__all__ = ["ui_language"]
