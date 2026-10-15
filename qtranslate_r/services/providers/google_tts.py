"""Озвучка через неофициальный Google TTS."""

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
_ALIAS = "qtr_tts"


def _mci(command: str) -> int:
    return ctypes.windll.winmm.mciSendStringW(command, None, 0, None)


class GoogleTTS(TextToSpeech):
    id = "google-tts"
    name = "Google"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._playing = False

    def speak(self, text: str, language: str) -> None:
        if sys.platform != "win32":
            raise ServiceError(tr("errors.playback_windows"), kind="unsupported")
        if not text.strip():
            return

        for chunk in chunk_text(text, _CHUNK_LIMIT):
            self._play(chunk, language)

    def _play(self, text: str, language: str) -> None:
        audio = http_get_bytes(
            _ENDPOINT,
            {"ie": "UTF-8", "client": "tw-ob", "tl": language, "q": text},
        )
        if not audio:
            raise ServiceError(tr("errors.empty_response"), kind="error")

        handle, path = tempfile.mkstemp(suffix=".mp3")
        os.close(handle)
        try:
            with open(path, "wb") as file:
                file.write(audio)
            with self._lock:
                self._playing = True
            _mci(f'open "{path}" type mpegvideo alias {_ALIAS}')
            try:
                _mci(f"play {_ALIAS} wait")
            finally:
                _mci(f"close {_ALIAS}")
                with self._lock:
                    self._playing = False
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

    def stop(self) -> None:
        with self._lock:
            playing = self._playing
        if playing:
            _mci(f"stop {_ALIAS}")
