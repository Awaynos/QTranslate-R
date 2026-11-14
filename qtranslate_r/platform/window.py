"""Выбор реализации оконных интеграций."""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from .windows.window import (
        apply_window_icon,
        cursor_position,
        enable_native_resize,
        move_window,
        native_event,
    )
elif sys.platform == "darwin":
    from .macos.window import (
        apply_window_icon,
        cursor_position,
        enable_native_resize,
        move_window,
        native_event,
    )
else:
    from .linux.window import (
        apply_window_icon,
        cursor_position,
        enable_native_resize,
        move_window,
        native_event,
    )

__all__ = [
    "apply_window_icon",
    "cursor_position",
    "enable_native_resize",
    "move_window",
    "native_event",
]
