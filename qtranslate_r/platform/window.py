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
        start_system_move,
        start_system_resize,
    )
elif sys.platform == "darwin":
    from .macos.window import (
        apply_window_icon,
        cursor_position,
        enable_native_resize,
        move_window,
        native_event,
        start_system_move,
        start_system_resize,
    )
else:
    from .linux.window import (
        apply_window_icon,
        cursor_position,
        enable_native_resize,
        move_window,
        native_event,
        start_system_move,
        start_system_resize,
    )

__all__ = [
    "apply_window_icon",
    "cursor_position",
    "enable_native_resize",
    "move_window",
    "native_event",
    "start_system_move",
    "start_system_resize",
]
