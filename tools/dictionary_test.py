"""Проверка словаря: Wiktionary, CSV и панель в окне."""

from __future__ import annotations

import os
import sys
import tempfile
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
from qtranslate_r.services.providers import CsvDictionary, WiktionaryDictionary  # noqa: E402
from qtranslate_r.speech import SpeechController  # noqa: E402
from qtranslate_r.ui.main_window import MainWindow  # noqa: E402
from qtranslate_r.ui.theme import apply_theme  # noqa: E402


def test_providers() -> bool:
    wiktionary = WiktionaryDictionary()
    entries = wiktionary.lookup("hello", "en", "ru")
    print(f"Wiktionary: статей {len(entries)}")
    for entry in entries[:3]:
        first = entry.definitions[0] if entry.definitions else ""
        print(f"  [{entry.part_of_speech}] {first[:80]}")

    csv_file = Path(tempfile.gettempdir()) / "qtr_dict_test.csv"
    csv_file.write_text("hello,привет\nhello,здравствуй\nother,другое\n", encoding="utf-8")
    csv_dict = CsvDictionary()
    csv_dict.configure({"path": str(csv_file), "term_column": 0, "definition_column": 1})
    csv_entries = csv_dict.lookup("hello", "en", "ru")
    print("CSV:", csv_entries[0].definitions if csv_entries else "нет")

    return bool(entries) and bool(csv_entries)


def test_panel() -> bool:
    app = QApplication(sys.argv)
    settings = Settings.load(settings_file())
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
    window._input.setPlainText("hello world")  # noqa: SLF001
    window._toggle_dictionary()  # noqa: SLF001

    deadline = time.time() + 20
    count = 0
    while time.time() < deadline:
        app.processEvents()
        count = window._dictionary_panel._entries_layout.count()  # noqa: SLF001
        if count > 0:
            break
        time.sleep(0.1)

    print("Панель словаря: статей в списке", count)
    return count > 0


def main() -> int:
    providers_ok = test_providers()
    panel_ok = test_panel()
    print("OK" if providers_ok and panel_ok else "ПРОВАЛ")
    return 0 if providers_ok and panel_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
