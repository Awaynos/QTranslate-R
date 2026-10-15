"""Проверка быстрого перевода: рендер попапа и регистрация хоткея."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication  # noqa: E402

from qtranslate_r.domain.models import TranslationResult  # noqa: E402
from qtranslate_r.platform.hotkey import GlobalHotkey  # noqa: E402
from qtranslate_r.ui.quick_popup import QuickTranslatePopup  # noqa: E402
from qtranslate_r.ui.theme import apply_theme  # noqa: E402

OUT = ROOT / "tools" / "shots"
OUT.mkdir(parents=True, exist_ok=True)

SAMPLE = TranslationResult(
    "google", "Google", text="Перевод — это мост между языками.",
    detected_source="en", elapsed_ms=520,
)
ERROR = TranslationResult("libretranslate", "LibreTranslate", error="Нужен ключ доступа")


def main() -> int:
    app = QApplication(sys.argv)

    for theme in ("dark", "light"):
        apply_theme(app, theme)
        popup = QuickTranslatePopup()
        popup.show_loading("Translation is a bridge between languages.")
        app.processEvents()
        popup.grab().save(str(OUT / f"quick_{theme}_loading.png"))

        popup.show_result(SAMPLE)
        app.processEvents()
        popup.grab().save(str(OUT / f"quick_{theme}_result.png"))

        popup.show_error(ERROR.error)
        app.processEvents()
        popup.grab().save(str(OUT / f"quick_{theme}_error.png"))
        popup.hide()

    hotkey = GlobalHotkey(0x51, ctrl=True, hotkey_id=0x5155)
    hotkey.start()
    time.sleep(0.6)
    print("хоткей Ctrl+Q зарегистрирован:", hotkey.registered)
    hotkey.stop()

    print("скриншоты:", *[p.name for p in sorted(OUT.glob("quick_*.png"))])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
