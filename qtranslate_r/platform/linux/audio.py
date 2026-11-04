"""Воспроизведение аудио в Linux через ffplay, mpv или paplay."""

from __future__ import annotations

import shutil
import subprocess
import threading
from pathlib import Path

from ...localization import tr
from ..base import AudioError

_players = ("ffplay", "mpv", "paplay")
_lock = threading.Lock()
_proc: subprocess.Popen | None = None
_stopped = False


def available() -> bool:
    return any(shutil.which(name) for name in _players)


def _command(path: Path) -> list[str] | None:
    executable = shutil.which("ffplay")
    if executable:
        return [
            executable,
            "-nodisp",
            "-autoexit",
            "-xerror",
            "-loglevel",
            "quiet",
            str(path),
        ]

    executable = shutil.which("mpv")
    if executable:
        return [executable, "--no-video", "--really-quiet", "--no-terminal", str(path)]

    if path.suffix.lower() == ".wav":
        executable = shutil.which("paplay")
        if executable:
            return [executable, str(path)]
    return None


def play_file(path: Path) -> None:
    global _proc, _stopped

    if not path.is_file():
        raise AudioError(tr("errors.file_not_found"))

    command = _command(path)
    if command is None:
        raise AudioError(tr("errors.audio_playback"))

    with _lock:
        _stopped = False
        proc = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _proc = proc

    try:
        code = proc.wait()
    finally:
        with _lock:
            if _proc is proc:
                _proc = None

    with _lock:
        stopped = _stopped
    if stopped:
        return
    if code != 0:
        raise AudioError(f"exit {code}")


def stop_playback() -> None:
    global _stopped

    with _lock:
        _stopped = True
        proc = _proc
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
