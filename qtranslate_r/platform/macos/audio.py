"""Заглушка воспроизведения аудио."""

from __future__ import annotations

from pathlib import Path

from ..base import AudioError


def play_file(path: Path) -> None:
    raise AudioError("playback is unavailable")


def stop_playback() -> None:
    pass
