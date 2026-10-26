"""Системная озвучка Windows через SAPI (без внешних зависимостей)."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from ...domain.errors import ServiceError
from ...domain.language import language_name
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
    "kk": "kk-KZ", "ka": "ka-GE",
}

_SCRIPT = """
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$c = $env:QTR_TTS_CULTURE
if ($c) {
    $voice = $s.GetInstalledVoices() | Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name -eq $c } | Select-Object -First 1
    if ($null -eq $voice) { [Console]::Error.WriteLine('no_voice'); exit 2 }
    $s.SelectVoice($voice.VoiceInfo.Name)
}
$path = $env:QTR_TTS_FILE
if (-not $path -or -not (Test-Path -LiteralPath $path)) { [Console]::Error.WriteLine('no_text'); exit 3 }
$text = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
$s.Speak($text)
"""

_CREATE_NO_WINDOW = 0x08000000


class SystemTTS(TextToSpeech):
    id = "system-tts"

    @property
    def name(self) -> str:
        return tr("service.system_tts")

    def __init__(self) -> None:
        self._proc: subprocess.Popen | None = None
        self._stop: threading.Event | None = None
        self._lock = threading.Lock()

    def speak(self, text: str, language: str) -> None:
        if sys.platform != "win32":
            raise ServiceError(tr("errors.tts_windows"), kind="unsupported")
        if not text.strip():
            return

        culture = _CULTURES.get(language)
        language_label = language_name(language)
        if language and not culture:
            raise ServiceError(
                tr("errors.tts_no_voice", language=language_label),
                kind="unsupported",
            )

        handle, name = tempfile.mkstemp(prefix="qtr_tts_", suffix=".txt")
        path = Path(name)
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as file:
                file.write(text)

            env = dict(os.environ)
            env["QTR_TTS_FILE"] = str(path)
            if culture:
                env["QTR_TTS_CULTURE"] = culture
            else:
                env.pop("QTR_TTS_CULTURE", None)

            stop = threading.Event()
            with self._lock:
                self._stop = stop
                self._proc = subprocess.Popen(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", _SCRIPT],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    env=env,
                    creationflags=_CREATE_NO_WINDOW,
                )
                proc = self._proc
            try:
                _, error = proc.communicate()
            finally:
                with self._lock:
                    if self._proc is proc:
                        self._proc = None
                    if self._stop is stop:
                        self._stop = None

            if stop.is_set():
                return
            if proc.returncode == 2:
                raise ServiceError(
                    tr("errors.tts_no_voice", language=language_label),
                    kind="unsupported",
                )
            if proc.returncode not in (0, None):
                detail = (error or "").strip() or f"exit {proc.returncode}"
                raise ServiceError(tr("errors.speech", message=detail), kind="error")
        finally:
            try:
                path.unlink()
            except OSError:
                pass

    def stop(self) -> None:
        with self._lock:
            stop = self._stop
            proc = self._proc
        if stop is not None:
            stop.set()
        if proc is not None and proc.poll() is None:
            proc.terminate()
