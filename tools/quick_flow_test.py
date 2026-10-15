"""Сквозная проверка контроллера быстрого перевода (без реального выделения)."""

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

from qtranslate_r.config import Settings  # noqa: E402
from qtranslate_r.core.setup import build_registry, configure_registry  # noqa: E402
from qtranslate_r.core.translation import TranslationService  # noqa: E402
from qtranslate_r.quick import QuickTranslateController  # noqa: E402
from qtranslate_r.localization import tr  # noqa: E402
from qtranslate_r.speech import SpeechController  # noqa: E402
from qtranslate_r.ui.theme import apply_theme  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv)
    settings = Settings()
    settings.enabled_providers = ["google"]
    settings.target_language = "ru"
    apply_theme(app, settings.theme)

    registry = build_registry()
    configure_registry(registry, settings)
    controller = QuickTranslateController(
        settings=settings,
        service=TranslationService(registry),
        speech=SpeechController(settings=settings, registry=registry),
    )

    QGuiApplication.clipboard().setText("Good morning, my friend!")
    controller._on_captured(True)  # noqa: SLF001 — имитируем успешный захват

    deadline = time.time() + 20
    body = ""
    loading = tr("popup.translating")
    while time.time() < deadline:
        app.processEvents()
        body = controller._popup._body.text()  # noqa: SLF001
        if body and body != loading:
            break
        time.sleep(0.1)

    print("попап:", body)
    ok = bool(body) and body != loading and "ошиб" not in body.lower()
    print("OK" if ok else "ПРОВАЛ")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
