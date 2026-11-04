"""Системная озвучка Linux через speech-dispatcher или espeak-ng."""

from __future__ import annotations

import shutil
import subprocess
import threading

from ...domain.errors import ServiceError
from ...localization import tr
from ...services.base import TextToSpeech

_ENGINES = ("spd-say", "espeak-ng", "espeak")


def available() -> bool:
    return any(shutil.which(name) for name in _ENGINES)


def _command(text: str, language: str) -> list[str] | None:
    tag = language or "en"
    executable = shutil.which("spd-say")
    if executable:
        return [executable, "--wait", "--language", tag, "--", text]

    for name in ("espeak-ng", "espeak"):
        executable = shutil.which(name)
        if executable:
            return [executable, "-v", tag, "--", text]
    return None


class SystemTTS(TextToSpeech):
    id = "system-tts"

    @property
    def name(self) -> str:
        return tr("service.system_tts")

    def __init__(self) -> None:
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()

    def speak(self, text: str, language: str) -> None:
        if not text.strip():
            return

        command = _command(text, language)
        if command is None:
            raise ServiceError(tr("errors.no_tts"), kind="unavailable")

        with self._lock:
            proc = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            self._proc = proc
        try:
            _, error = proc.communicate()
        finally:
            with self._lock:
                if self._proc is proc:
                    self._proc = None

        if proc.returncode not in (0, None):
            detail = (error or b"").decode("utf-8", "replace").strip()
            raise ServiceError(
                tr("errors.speech", message=detail or f"exit {proc.returncode}"),
                kind="error",
            )

    def stop(self) -> None:
        with self._lock:
            proc = self._proc
        if proc is not None and proc.poll() is None:
            proc.terminate()
