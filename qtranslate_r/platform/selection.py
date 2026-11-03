"""Выбор реализации работы с выделением и буфером."""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from .windows.selection import copy_selection, paste_clipboard
elif sys.platform == "darwin":
    from .macos.selection import copy_selection, paste_clipboard
else:
    from .linux.selection import copy_selection, paste_clipboard

__all__ = ["copy_selection", "paste_clipboard"]
