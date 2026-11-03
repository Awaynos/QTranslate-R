"""Выбор реализации оконных интеграций."""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from .windows.window import apply_window_icon, enable_native_resize, native_event
elif sys.platform == "darwin":
    from .macos.window import apply_window_icon, enable_native_resize, native_event
else:
    from .linux.window import apply_window_icon, enable_native_resize, native_event

__all__ = ["apply_window_icon", "enable_native_resize", "native_event"]
