"""Проверка замены выделенного текста переводом (вставка подменяется заглушкой)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

import qtranslate_r.inline as inline_module  # noqa: E402
from qtranslate_r.config import Settings  # noqa: E402
from qtranslate_r.core.setup import build_registry, configure_registry  # noqa: E402
from qtranslate_r.core.translation import TranslationService  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv)

    pasted: list[bool] = []
    inline_module.paste_clipboard = lambda: pasted.append(True)  # не шлём Ctrl+V на самом деле

    settings = Settings()
    settings.enabled_providers = ["google"]
    settings.target_language = "ru"
    registry = build_registry()
    configure_registry(registry, settings)

    controller = inline_module.InlineReplaceController(
        settings=settings, service=TranslationService(registry)
    )

    QGuiApplication.clipboard().setText("Good morning, my friend!")
    controller._on_captured(True)  # noqa: SLF001 — имитируем успешное копирование выделения

    deadline = time.time() + 20
    result = ""
    while time.time() < deadline:
        app.processEvents()
        result = QGuiApplication.clipboard().text()
        if result != "Good morning, my friend!" and pasted:
            break
        time.sleep(0.1)

    print("буфер после замены:", result)
    print("вставка вызвана:", bool(pasted))
    ok = result != "Good morning, my friend!" and bool(pasted)
    print("OK" if ok else "ПРОВАЛ")
    controller.stop()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
