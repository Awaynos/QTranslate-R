"""Выбор реализации захвата экрана."""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from .windows.screen import capture_region, has_region_selection, select_region
elif sys.platform == "darwin":
    from .macos.screen import capture_region, has_region_selection, select_region
else:
    from .linux.screen import capture_region, has_region_selection, select_region

__all__ = ["capture_region", "has_region_selection", "select_region"]
