"""Заглушка системной озвучки."""

from __future__ import annotations

from ...localization import tr
from ...services.base import TextToSpeech
from ..base import PlatformUnavailable


class SystemTTS(TextToSpeech):
    id = "system-tts"

    @property
    def name(self) -> str:
        return tr("service.system_tts")

    def speak(self, text: str, language: str) -> None:
        raise PlatformUnavailable(tr("errors.tts_windows"))

    def stop(self) -> None:
        pass
