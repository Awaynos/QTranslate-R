"""Определение доступных системных возможностей."""

from __future__ import annotations

import sys

from .base import Capabilities


def capabilities() -> Capabilities:
    if sys.platform == "win32":
        return Capabilities(
            global_hotkeys=True,
            selection_capture=True,
            replace_selection=True,
            screen_capture=True,
            system_tts=True,
            audio_playback=True,
            spellcheck=True,
            tray=True,
        )
    return Capabilities()
