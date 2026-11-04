"""Выбор диагностики платформы."""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from .windows.doctor import report
elif sys.platform == "darwin":
    from .macos.doctor import report
else:
    from .linux.doctor import report

__all__ = ["report"]
