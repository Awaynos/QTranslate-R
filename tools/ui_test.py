"""Проверка полного пути UI: ввод -> воркер -> сигналы -> карточки."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication  # noqa: E402

from qtranslate_r.config import Settings, history_file, settings_file  # noqa: E402
from qtranslate_r.core.history import HistoryStore  # noqa: E402
from qtranslate_r.core.setup import build_registry, configure_registry  # noqa: E402
from qtranslate_r.core.translation import TranslationService  # noqa: E402
from qtranslate_r.speech import SpeechController  # noqa: E402
from qtranslate_r.ui.main_window import MainWindow  # noqa: E402
from qtranslate_r.ui.theme import apply_theme  # noqa: E402
from qtranslate_r.ui.widgets import ResultCard  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv)
    settings = Settings.load(settings_file())
    settings.enabled_providers = ["google", "mymemory"]
    settings.translate_on_type = False
    apply_theme(app, settings.theme)

    registry = build_registry()
    configure_registry(registry, settings)
    window = MainWindow(
        app=app,
        settings=settings,
        settings_path=settings_file(),
        registry=registry,
        translation_service=TranslationService(registry),
        history_store=HistoryStore(history_file()),
        speech=SpeechController(settings=settings, registry=registry),
    )
    window.show()

    window._input.setPlainText("Good morning, my friend!")  # noqa: SLF001
    window._language_bar.set_languages("auto", "ru")  # noqa: SLF001
    window._start_translation()  # noqa: SLF001

    deadline = time.time() + 20
    cards: list[ResultCard] = []
    while time.time() < deadline:
        app.processEvents()
        cards = [
            window._results_layout.itemAt(i).widget()  # noqa: SLF001
            for i in range(window._results_layout.count())  # noqa: SLF001
            if isinstance(window._results_layout.itemAt(i).widget(), ResultCard)  # noqa: SLF001
        ]
        if cards and window._translate_button.isEnabled():  # noqa: SLF001
            break
        time.sleep(0.1)

    if not cards:
        print("ПРОВАЛ: карточки не появились")
        return 1

    print("статус:", window.statusBar().currentMessage())
    for card in cards:
        result = card.result
        tag = "OK" if result.ok else "ОШИБКА"
        print(f"  [{tag}] {result.provider_name} ({result.elapsed_ms} мс): {result.text or result.error}")
    print("история:", len(window._history.entries))  # noqa: SLF001
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
