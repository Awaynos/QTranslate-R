"""Рендер индикаторов загрузки и проверка их появления/скрытия."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication  # noqa: E402

from qtranslate_r.config import Settings  # noqa: E402
from qtranslate_r.ui.loading import CursorLoadingIndicator, InlineLoading  # noqa: E402
from qtranslate_r.ui.theme import apply_theme  # noqa: E402

OUT = ROOT / "tools" / "shots"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    app = QApplication(sys.argv)
    settings = Settings()
    settings.theme = "metal"
    apply_theme(app, settings.theme)

    indicator = CursorLoadingIndicator(settings)
    indicator.show_loading()
    app.processEvents()
    print("показан:", indicator.isVisible())
    indicator.grab().save(str(OUT / "loading_cursor.png"))

    # скрытие с минимальной выдержкой
    indicator.hide_loading()
    app.processEvents()
    time.sleep(0.4)
    app.processEvents()
    print("скрыт:", not indicator.isVisible())

    inline = InlineLoading()
    inline.set_loading(True)
    app.processEvents()
    inline.grab().save(str(OUT / "loading_inline.png"))

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
