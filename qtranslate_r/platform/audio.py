"""Выбор реализации воспроизведения аудио."""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from .windows.audio import play_file, stop_playback
elif sys.platform == "darwin":
    from .macos.audio import play_file, stop_playback
else:
    from .linux.audio import play_file, stop_playback

__all__ = ["play_file", "stop_playback"]
