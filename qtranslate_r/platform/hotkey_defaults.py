"""Дефолтные глобальные хоткеи для текущей платформы."""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from .windows.hotkey_defaults import defaults
elif sys.platform == "darwin":
    from .macos.hotkey_defaults import defaults
else:
    from .linux.hotkey_defaults import defaults

__all__ = ["defaults"]
