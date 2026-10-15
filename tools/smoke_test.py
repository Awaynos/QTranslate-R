"""Сборка окна в offscreen-режиме и реальный перевод текста."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication  # noqa: E402

from qtranslate_r.config import Settings, history_file, settings_file  # noqa: E402
from qtranslate_r.core.history import HistoryStore  # noqa: E402
from qtranslate_r.core.setup import build_registry, configure_registry  # noqa: E402
from qtranslate_r.core.translation import TranslationService  # noqa: E402
from qtranslate_r.speech import SpeechController  # noqa: E402
from qtranslate_r.ui.main_window import MainWindow  # noqa: E402
from qtranslate_r.ui.theme import apply_theme  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv)
    settings = Settings.load(settings_file())
    apply_theme(app, settings.theme)

    registry = build_registry()
    configure_registry(registry, settings)
    service = TranslationService(registry)

    window = MainWindow(
        app=app,
        settings=settings,
        settings_path=settings_file(),
        registry=registry,
        translation_service=service,
        history_store=HistoryStore(history_file()),
        speech=SpeechController(settings=settings, registry=registry),
    )
    window.show()
    print("UI:", window.windowTitle())

    providers = window._provider_bar.enabled_ids()  # noqa: SLF001
    print("сервисы:", providers)

    for result in service.translate("Hello, world!", "auto", "ru", providers):
        tag = "OK" if result.ok else "ОШИБКА"
        print(f"  [{tag}] {result.provider_name} ({result.elapsed_ms} мс): {result.text or result.error}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
