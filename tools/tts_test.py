"""Проверка озвучки: системный TTS и Google TTS (со звуком, текст короткий)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qtranslate_r.services.providers import GoogleTTS, SystemTTS  # noqa: E402


def system_available() -> bool:
    if sys.platform.startswith("linux"):
        from qtranslate_r.platform.linux import speech

        return speech.available()
    return True


def audio_available() -> bool:
    if sys.platform.startswith("linux"):
        from qtranslate_r.platform.linux import audio

        return audio.available()
    return True


def main() -> int:
    text = "Проверка озвучки"

    if system_available():
        SystemTTS().speak(text, "ru")
        print("Системный TTS: ок")
    else:
        print("SKIP: системный TTS не установлен")

    if audio_available():
        GoogleTTS().speak(text, "ru")
        print("Google TTS: ок")
    else:
        print("SKIP: нет плеера для Google TTS")

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
