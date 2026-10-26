"""Озвучка через открытый Google Translate TTS."""

from __future__ import annotations

import ctypes
import os
import sys
import tempfile
import threading

from ...domain.errors import ServiceError
from ...localization import tr
from ..base import TextToSpeech
from ._http import http_get_bytes
from ._util import chunk_text

_ENDPOINT = "https://translate.google.com/translate_tts"
_CHUNK_LIMIT = 180
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


def _mci(command: str) -> tuple[int, str]:
    buffer = ctypes.create_unicode_buffer(256)
    code = ctypes.windll.winmm.mciSendStringW(command, buffer, 256, None)
    return code, buffer.value


class GoogleTTS(TextToSpeech):
    id = "google-tts"
    name = "Google"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._playing = False
        self._stopped = threading.Event()
        self._alias = ""
        self._counter = 0

    def speak(self, text: str, language: str) -> None:
        if sys.platform != "win32":
            raise ServiceError(tr("errors.playback_windows"), kind="unsupported")
        if not text.strip():
            return

        self._stopped.clear()
        with self._lock:
            self._playing = True
        try:
            for chunk in chunk_text(text, _CHUNK_LIMIT):
                if self._stopped.is_set():
                    break
                self._play(chunk, language)
        finally:
            with self._lock:
                self._playing = False
                self._alias = ""

    def _play(self, text: str, language: str) -> None:
        audio = http_get_bytes(
            _ENDPOINT,
            {
                "ie": "UTF-8",
                "client": "tw-ob",
                "tl": language,
                "q": text,
                "total": "1",
                "idx": "0",
                "textlen": str(len(text)),
            },
            headers={"User-Agent": _USER_AGENT, "Referer": "https://translate.google.com/"},
        )
        if len(audio) < 512 or not (audio.startswith(b"ID3") or audio[0] == 0xFF):
            raise ServiceError(tr("errors.bad_response"), kind="error")

        handle, path = tempfile.mkstemp(suffix=".mp3")
        os.close(handle)
        try:
            with open(path, "wb") as file:
                file.write(audio)

            with self._lock:
                self._counter += 1
                alias = f"qtr_tts_{self._counter}"
                self._alias = alias
            if self._stopped.is_set():
                return

            code, error = _mci(f'open "{path}" type mpegvideo alias {alias}')
            if code:
                code, error = _mci(f'open "{path}" type mpegaudio alias {alias}')
            if code:
                raise ServiceError(tr("errors.speech", message=error), kind="error")

            try:
                code, error = _mci(f"play {alias} wait")
                if code and not self._stopped.is_set():
                    raise ServiceError(tr("errors.speech", message=error), kind="error")
            finally:
                _mci(f"close {alias}")
                with self._lock:
                    if self._alias == alias:
                        self._alias = ""
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

    def stop(self) -> None:
        self._stopped.set()
        with self._lock:
            alias = self._alias
            playing = self._playing
        if playing and alias:
            _mci(f"stop {alias}")
