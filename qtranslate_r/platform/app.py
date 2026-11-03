"""Выбор реализации инициализации приложения."""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from .windows.app import set_taskbar_identity
elif sys.platform == "darwin":
    from .macos.app import set_taskbar_identity
else:
    from .linux.app import set_taskbar_identity

__all__ = ["set_taskbar_identity"]
