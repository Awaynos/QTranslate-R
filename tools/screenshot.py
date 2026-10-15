"""Рендер окон в PNG. По умолчанию offscreen; с QT_QPA_PLATFORM=windows — с системными шрифтами."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication  # noqa: E402

from qtranslate_r.config import Settings, history_file, project_root, settings_file  # noqa: E402
from qtranslate_r.core.history import HistoryStore  # noqa: E402
from qtranslate_r.core.setup import (  # noqa: E402
    build_registry,
    configure_registry,
    dictionary_choices,
    tts_choices,
)
from qtranslate_r.core.translation import TranslationService  # noqa: E402
from qtranslate_r.domain.language import AUTO_PAIR  # noqa: E402
from qtranslate_r.domain.models import DictionaryEntry, TranslationResult  # noqa: E402
from qtranslate_r.localization import set_language  # noqa: E402
from qtranslate_r.speech import SpeechController  # noqa: E402
from qtranslate_r.ui.dialogs import DocumentDialog, SettingsDialog  # noqa: E402
from qtranslate_r.ui.icons import set_directory as set_icons_directory  # noqa: E402
from qtranslate_r.ui.main_window import MainWindow  # noqa: E402
from qtranslate_r.ui.theme import apply_theme  # noqa: E402

OUT = ROOT / "tools" / "shots"
OUT.mkdir(parents=True, exist_ok=True)

SAMPLES = [
    TranslationResult("google", "Google", text="Перевод — это мост между языками.",
                      detected_source="en", elapsed_ms=540),
    TranslationResult("mymemory", "MyMemory", text="Перевод — это мост между языками.",
                      elapsed_ms=910),
    TranslationResult("libretranslate", "LibreTranslate",
                      error="Нужен ключ доступа или он неверный", elapsed_ms=180),
]

DICTIONARY = [
    DictionaryEntry("hello", "Wiktionary", "en", "Interjection",
                    ["Приветствие при встрече.",
                     "Выражение удивления или догадки."]),
    DictionaryEntry("hello", "Wiktionary", "en", "Noun",
                    ['«Hello!» или равнозначное приветствие.']),
]


def build_window(app: QApplication, theme: str) -> MainWindow:
    settings = Settings.load(settings_file())
    settings.theme = theme
    settings.native_language = "ru"
    settings.second_language = "en"
    set_language(settings.interface_language)
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
    apply_theme(app, theme)
    window.resize(1040, 880)
    window.show()
    app.processEvents()
    app.processEvents()
    return window


def render_main(app: QApplication, theme: str) -> MainWindow:
    window = build_window(app, theme)
    window._language_bar.set_languages("auto", AUTO_PAIR)  # noqa: SLF001
    window._input.setPlainText("Translation is a bridge between languages.")  # noqa: SLF001
    window._render_results(SAMPLES)  # noqa: SLF001
    window._last_result_text = SAMPLES[0].text  # noqa: SLF001
    window._render_backward(SAMPLES[1])  # noqa: SLF001
    app.processEvents()
    return window


def main() -> int:
    app = QApplication(sys.argv)
    set_icons_directory(project_root() / "icons")

    metal = render_main(app, "metal")
    metal.grab().save(str(OUT / "metal_results.png"))
    menu = metal._build_theme_menu()  # noqa: SLF001
    menu.popup(metal.mapToGlobal(metal.rect().topLeft()))
    app.processEvents()
    menu.grab().save(str(OUT / "theme_menu.png"))
    menu.close()

    turquoise = render_main(app, "turquoise")
    turquoise.grab().save(str(OUT / "turquoise_results.png"))

    bronze = render_main(app, "bronze")
    bronze._panel_stack.setCurrentIndex(1)  # noqa: SLF001
    bronze._backward_button.setChecked(False)  # noqa: SLF001
    bronze._dictionary_button.setChecked(True)  # noqa: SLF001
    bronze._dictionary_panel.show_entries("hello", "en", DICTIONARY)  # noqa: SLF001
    app.processEvents()
    bronze.grab().save(str(OUT / "bronze_dictionary.png"))

    light = render_main(app, "light")
    light.grab().save(str(OUT / "light_results.png"))

    settings = Settings.load(settings_file())
    set_language(settings.interface_language)
    registry = build_registry()
    configure_registry(registry, settings)
    apply_theme(app, "metal")
    settings_dialog = SettingsDialog(
        settings, tts_choices(registry), dictionary_choices(registry)
    )
    settings_dialog.show()
    app.processEvents()
    settings_dialog._sections.setCurrentRow(4)  # noqa: SLF001
    app.processEvents()
    settings_dialog.grab().save(str(OUT / "settings_dialog.png"))

    document = DocumentDialog(
        service=TranslationService(registry),
        registry=registry,
        source="auto",
        target="ru",
        provider_id="google",
    )
    document.show()
    app.processEvents()
    document.grab().save(str(OUT / "document_dialog.png"))

    print("скриншоты:", *[p.name for p in sorted(OUT.glob("*.png"))])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
