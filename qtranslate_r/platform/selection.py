"""Выбор реализации работы с выделением и буфером."""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from .windows.selection import (
        capture_selection,
        copy_selection,
        paste_clipboard,
        set_clipboard,
    )
elif sys.platform == "darwin":
    from .macos.selection import (
        capture_selection,
        copy_selection,
        paste_clipboard,
        set_clipboard,
    )
else:
    from .linux.selection import (
        capture_selection,
        copy_selection,
        paste_clipboard,
        set_clipboard,
    )

__all__ = [
    "capture_selection",
    "copy_selection",
    "paste_clipboard",
    "set_clipboard",
]
