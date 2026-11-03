"""Выбор реализации системной озвучки."""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from .windows.speech import SystemTTS
elif sys.platform == "darwin":
    from .macos.speech import SystemTTS
else:
    from .linux.speech import SystemTTS

__all__ = ["SystemTTS"]
