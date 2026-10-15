"""Проверка озвучки: системный SAPI и Google TTS (со звуком, текст короткий)."""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qtranslate_r.services.providers import GoogleTTS, SystemTTS  # noqa: E402


def main() -> int:
    text = "Проверка озвучки"

    system = SystemTTS()
    started = time.perf_counter()
    system.speak(text, "ru")
    print(f"Системный TTS: ок ({time.perf_counter() - started:.1f} c)")

    google = GoogleTTS()
    started = time.perf_counter()
    google.speak(text, "ru")
    print(f"Google TTS: ок ({time.perf_counter() - started:.1f} c)")

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
