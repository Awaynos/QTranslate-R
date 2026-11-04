"""Определение доступных системных возможностей."""

from __future__ import annotations

import sys

from .base import Capabilities


def _linux() -> Capabilities:
    from .linux.env import session_type, tool_path

    clipboard = any(tool_path(name) for name in ("wl-paste", "xclip", "xsel"))
    injection = any(tool_path(name) for name in ("wtype", "ydotool", "xdotool"))
    screen = session_type() == "x11" or bool(tool_path("slurp") and tool_path("grim"))
    return Capabilities(
        selection_capture=clipboard,
        replace_selection=injection,
        screen_capture=screen,
        tray=True,
    )


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
    if sys.platform == "darwin":
        return Capabilities()
    return _linux()
