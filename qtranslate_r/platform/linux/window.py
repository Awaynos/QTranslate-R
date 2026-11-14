"""Оконные интеграции Linux."""

from __future__ import annotations

import re
import subprocess
import time

from .env import session_type, tool_path

_CURSOR = re.compile(r"^\s*(-?\d+)\s*,\s*(-?\d+)\s*$")
_CACHE_SECONDS = 0.05

_cached_at = 0.0
_cached_position: tuple[int, int] | None = None


def _regex_escape(value: str) -> str:
    return re.sub(r"([\\.^$|?*+()\[\]{}])", r"\\\1", value)


def move_window(title: str, x: int, y: int) -> bool:
    if session_type() == "x11" or not tool_path("hyprctl"):
        return False
    selector = f"title:^({_regex_escape(title)})$"
    command = (
        f'hl.dsp.window.move({{ x = {int(x)}, y = {int(y)}, '
        f'window = "{selector}" }})'
    )
    try:
        result = subprocess.run(
            ["hyprctl", "dispatch", command],
            capture_output=True,
            timeout=1.5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def apply_window_icon(window, ico) -> None:
    pass


def enable_native_resize(window) -> None:
    pass


def native_event(window, event_type, message):
    return None


def cursor_position() -> tuple[int, int] | None:
    global _cached_at, _cached_position

    now = time.monotonic()
    if now - _cached_at < _CACHE_SECONDS:
        return _cached_position

    position = None
    if session_type() != "x11" and tool_path("hyprctl"):
        try:
            result = subprocess.run(
                ["hyprctl", "cursorpos"],
                capture_output=True,
                timeout=0.3,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            result = None
        if result is not None and result.returncode == 0:
            match = _CURSOR.match(result.stdout.decode("utf-8", "replace"))
            if match is not None:
                position = (int(match.group(1)), int(match.group(2)))

    _cached_at = now
    _cached_position = position
    return position
