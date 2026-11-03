"""Воспроизведение аудио через MCI."""

from __future__ import annotations

import ctypes
import threading
from pathlib import Path

from ..base import AudioError

_lock = threading.Lock()
_counter = 0
_alias = ""


def _mci(command: str) -> tuple[int, str]:
    buffer = ctypes.create_unicode_buffer(256)
    code = ctypes.windll.winmm.mciSendStringW(command, buffer, 256, None)
    return code, buffer.value


def play_file(path: Path) -> None:
    global _counter, _alias

    with _lock:
        _counter += 1
        alias = f"qtr_tts_{_counter}"
        _alias = alias

    code, error = _mci(f'open "{path}" type mpegvideo alias {alias}')
    if code:
        code, error = _mci(f'open "{path}" type mpegaudio alias {alias}')
    if code:
        raise AudioError(error)

    try:
        code, error = _mci(f"play {alias} wait")
        if code:
            raise AudioError(error)
    finally:
        _mci(f"close {alias}")
        with _lock:
            if _alias == alias:
                _alias = ""


def stop_playback() -> None:
    with _lock:
        alias = _alias
    if alias:
        _mci(f"stop {alias}")
