"""Выделение и буфер обмена в Linux."""

from __future__ import annotations

import subprocess
import time

from .env import session_type, tool_path

CAPTURE_TIMEOUT = 0.8
COMMAND_TIMEOUT = 2.0

_KEY_CODES = {"c": 46, "v": 47}
_CTRL_CODE = 29


def _run(
    args: list[str],
    data: bytes | None = None,
    *,
    capture: bool = True,
) -> subprocess.CompletedProcess | None:
    options = {
        "input": data,
        "timeout": COMMAND_TIMEOUT,
        "check": False,
    }
    if capture:
        options["capture_output"] = True
    else:
        options["stdout"] = subprocess.DEVNULL
        options["stderr"] = subprocess.DEVNULL
    try:
        return subprocess.run(args, **options)
    except (OSError, subprocess.TimeoutExpired):
        return None


def _decode(result: subprocess.CompletedProcess | None) -> str | None:
    if result is None or result.returncode != 0:
        return None
    text = result.stdout.decode("utf-8", "replace")
    return text if text else None


def _primary_text() -> str | None:
    if session_type() != "x11" and tool_path("wl-paste"):
        text = _decode(_run(["wl-paste", "--primary", "--no-newline"]))
        if text:
            return text
    if tool_path("xclip"):
        text = _decode(_run(["xclip", "-o", "-selection", "primary"]))
        if text:
            return text
    if tool_path("xsel"):
        text = _decode(_run(["xsel", "-o", "--primary"]))
        if text:
            return text
    return None


def _clipboard_text() -> str | None:
    if session_type() != "x11" and tool_path("wl-paste"):
        text = _decode(_run(["wl-paste", "--no-newline"]))
        if text:
            return text
    if tool_path("xclip"):
        text = _decode(_run(["xclip", "-o", "-selection", "clipboard"]))
        if text:
            return text
    if tool_path("xsel"):
        text = _decode(_run(["xsel", "-o", "--clipboard"]))
        if text:
            return text
    return None


def _set_clipboard(text: str) -> bool:
    data = text.encode("utf-8")
    if session_type() != "x11" and tool_path("wl-copy"):
        result = _run(["wl-copy"], data, capture=False)
        if result is not None and result.returncode == 0:
            return True
    if tool_path("xclip"):
        result = _run(["xclip", "-selection", "clipboard", "-i"], data, capture=False)
        if result is not None and result.returncode == 0:
            return True
    if tool_path("xsel"):
        result = _run(["xsel", "--clipboard", "--input"], data, capture=False)
        if result is not None and result.returncode == 0:
            return True
    return False


def _send_shortcut(key: str) -> bool:
    if session_type() != "x11":
        if tool_path("wtype"):
            result = _run(["wtype", "-M", "ctrl", "-k", key, "-m", "ctrl"])
            if result is not None and result.returncode == 0:
                return True
        if tool_path("ydotool"):
            code = _KEY_CODES[key]
            result = _run(
                ["ydotool", "key", f"{_CTRL_CODE}:1", f"{code}:1", f"{code}:0", f"{_CTRL_CODE}:0"]
            )
            if result is not None and result.returncode == 0:
                return True

    if tool_path("xdotool"):
        result = _run(["xdotool", "key", "--clearmodifiers", f"ctrl+{key}"])
        if result is not None and result.returncode == 0:
            return True
    if tool_path("ydotool"):
        code = _KEY_CODES[key]
        result = _run(
            ["ydotool", "key", f"{_CTRL_CODE}:1", f"{code}:1", f"{code}:0", f"{_CTRL_CODE}:0"]
        )
        if result is not None and result.returncode == 0:
            return True
    if tool_path("wtype"):
        result = _run(["wtype", "-M", "ctrl", "-k", key, "-m", "ctrl"])
        return result is not None and result.returncode == 0
    return False


def capture_selection() -> str:
    """Вернуть выделенный текст: PRIMARY, затем Ctrl+C и буфер обмена."""
    text = _primary_text()
    if text:
        return text

    before = _clipboard_text()
    if not _send_shortcut("c"):
        return ""

    deadline = time.time() + CAPTURE_TIMEOUT
    while time.time() < deadline:
        current = _clipboard_text()
        if current and current != before:
            return current
        time.sleep(0.02)
    return _clipboard_text() or ""


def copy_selection() -> bool:
    """Скопировать выделение в буфер обмена и вернуть True при успехе."""
    return bool(capture_selection())


def set_clipboard(text: str) -> bool:
    """Записать текст в системный буфер обмена."""
    return _set_clipboard(text)


def paste_clipboard() -> None:
    """Отправить Ctrl+V в активное окно."""
    _send_shortcut("v")
