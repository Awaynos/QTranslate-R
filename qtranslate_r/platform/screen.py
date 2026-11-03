"""Выбор реализации захвата экрана."""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from .windows.screen import capture_region
elif sys.platform == "darwin":
    from .macos.screen import capture_region
else:
    from .linux.screen import capture_region

__all__ = ["capture_region"]
