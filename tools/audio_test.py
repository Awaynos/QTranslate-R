"""Проверка выбора аудиоплеера и ошибок воспроизведения."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qtranslate_r.platform.base import AudioError  # noqa: E402


def main() -> int:
    if not sys.platform.startswith("linux"):
        print("SKIP: not Linux")
        return 0

    from qtranslate_r.platform.linux import audio

    print("player:", "yes" if audio.available() else "no")
    if not audio.available():
        try:
            audio.play_file(Path("missing.mp3"))
        except AudioError:
            print("no player: AudioError")
        else:
            print("FAIL: expected AudioError")
            return 1
        print("OK")
        return 0

    assert audio._command(Path("test.mp3")) is not None  # noqa: SLF001
    try:
        audio.play_file(Path("missing.mp3"))
    except AudioError:
        print("missing file: AudioError")
    else:
        print("FAIL: expected AudioError")
        return 1

    audio.stop_playback()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
