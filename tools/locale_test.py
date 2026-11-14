"""Проверка определения языка системы и текстов интерфейса."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qtranslate_r.platform.linux.locale import _code, ui_language  # noqa: E402

KEYS = ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")
CHECKED = (
    "service.system_tts",
    "errors.tts_windows",
    "errors.tts_no_voice",
    "errors.playback_windows",
    "ocr.no_language",
)


def snapshot() -> dict[str, str | None]:
    return {key: os.environ.get(key) for key in KEYS}


def restore(values: dict[str, str | None]) -> None:
    for key, value in values.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def main() -> int:
    assert _code("ru_RU.UTF-8") == "ru"
    assert _code("pt_BR.UTF-8") == "pt-BR"
    assert _code("zh_CN.UTF-8") == "zh"
    assert _code("zh_TW.UTF-8") == "zh"
    assert _code("de_DE@euro") == "de"
    assert _code("C.UTF-8") is None
    assert _code("ru:en") == "ru"

    saved = snapshot()
    try:
        for key in KEYS:
            os.environ.pop(key, None)
        os.environ["LANG"] = "de_DE.UTF-8"
        assert ui_language() == "de"
        os.environ["LANGUAGE"] = "ru:en"
        assert ui_language() == "ru"
        os.environ["LC_ALL"] = "pt_BR.UTF-8"
        os.environ.pop("LANGUAGE", None)
        assert ui_language() == "pt-BR"
    finally:
        restore(saved)

    for path in Path("languages").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for key in CHECKED:
            assert "Windows" not in data[key], (path, key)

    print("locale: OK")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
