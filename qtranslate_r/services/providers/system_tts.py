"""Системная озвучка Windows через SAPI (без внешних зависимостей)."""

from __future__ import annotations

import os
import subprocess
import sys
import threading

from ...domain.errors import ServiceError
from ...localization import tr
from ..base import TextToSpeech

# ISO 639-1 -> культура SAPI.
_CULTURES = {
    "en": "en-US", "ru": "ru-RU", "uk": "uk-UA", "de": "de-DE", "fr": "fr-FR",
    "es": "es-ES", "it": "it-IT", "pt": "pt-BR", "pl": "pl-PL", "nl": "nl-NL",
    "tr": "tr-TR", "cs": "cs-CZ", "sv": "sv-SE", "da": "da-DK", "fi": "fi-FI",
    "no": "nb-NO", "hu": "hu-HU", "ro": "ro-RO", "el": "el-GR", "he": "he-IL",
    "ar": "ar-SA", "hi": "hi-IN", "ja": "ja-JP", "ko": "ko-KR", "zh": "zh-CN",
    "zh-TW": "zh-TW", "bg": "bg-BG", "hr": "hr-HR", "sk": "sk-SK", "sl": "sl-SI",
}

_SCRIPT = (
    "Add-Type -AssemblyName System.Speech; "
    "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
    "$c = $env:QTR_TTS_CULTURE; "
    "if ($c) { try { $s.SelectVoiceByHints("
    "[System.Speech.Synthesis.VoiceGender]::NotSet, "
    "[System.Speech.Synthesis.VoiceAge]::NotSet, 0, "
    "[System.Globalization.CultureInfo]::GetCultureInfo($c)) } catch {} }; "
    "$s.Speak([Console]::In.ReadToEnd())"
)


class SystemTTS(TextToSpeech):
    id = "system-tts"

    @property
    def name(self) -> str:
        return tr("service.system_tts")

    def __init__(self) -> None:
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()

    def speak(self, text: str, language: str) -> None:
        if sys.platform != "win32":
            raise ServiceError(tr("errors.tts_windows"), kind="unsupported")
        if not text.strip():
            return

        env = dict(os.environ)
        culture = _CULTURES.get(language)
        if culture:
            env["QTR_TTS_CULTURE"] = culture
        else:
            env.pop("QTR_TTS_CULTURE", None)

        with self._lock:
            self._proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", _SCRIPT],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                env=env,
            )
            proc = self._proc
        try:
            proc.communicate(text)
        finally:
            with self._lock:
                self._proc = None

    def stop(self) -> None:
        with self._lock:
            proc = self._proc
        if proc is not None and proc.poll() is None:
            proc.terminate()
