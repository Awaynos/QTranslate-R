"""Озвучка через открытый Google Translate TTS."""

from __future__ import annotations

import os
import tempfile
import threading
from pathlib import Path

from ...domain.errors import ServiceError
from ...localization import tr
from ...platform.audio import play_file, stop_playback
from ...platform.base import AudioError
from ..base import TextToSpeech
from ._http import http_get_bytes
from ._util import chunk_text

_ENDPOINT = "https://translate.google.com/translate_tts"
_CHUNK_LIMIT = 180
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


class GoogleTTS(TextToSpeech):
    id = "google-tts"
    name = "Google"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._playing = False
        self._stopped = threading.Event()

    def speak(self, text: str, language: str) -> None:
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

        handle, name = tempfile.mkstemp(suffix=".mp3")
        os.close(handle)
        path = Path(name)
        try:
            with open(path, "wb") as file:
                file.write(audio)
            if self._stopped.is_set():
                return
            try:
                play_file(path)
            except AudioError as exc:
                if not self._stopped.is_set():
                    raise ServiceError(tr("errors.speech", message=str(exc)), kind="error") from exc
        finally:
            try:
                path.unlink()
            except OSError:
                pass

    def stop(self) -> None:
        self._stopped.set()
        with self._lock:
            playing = self._playing
        if playing:
            stop_playback()
