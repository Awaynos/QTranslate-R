"""Проверка, что изменения пользователя переживают перезапуск."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication  # noqa: E402

from qtranslate_r.config import Settings, history_file, settings_file  # noqa: E402
from qtranslate_r.core.history import HistoryStore  # noqa: E402
from qtranslate_r.core.setup import build_registry, configure_registry  # noqa: E402
from qtranslate_r.core.translation import TranslationService  # noqa: E402
from qtranslate_r.localization import set_language  # noqa: E402
from qtranslate_r.speech import SpeechController  # noqa: E402
from qtranslate_r.ui.main_window import MainWindow  # noqa: E402
from qtranslate_r.ui.theme import apply_theme  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv)
    path = Path(tempfile.mkdtemp(prefix="qtr_persist_")) / "settings.json"

    settings = Settings.load(path)
    settings.theme = "bronze"
    settings.font_size = 12
    settings.enabled_providers = ["yandex", "reverso"]
    settings.primary_provider = "reverso"
    settings.tts_provider = "google-tts"
    settings.native_language = "de"
    settings.second_language = "fr"
    settings.hotkeys = {"translate": "Ctrl+Shift+Enter"}
    settings.hotkey_scopes = {"translate": "global"}
    settings.splitter_sizes = [200, 300, 250]
    settings.panel_index = 1
    settings.save(path)

    reloaded = Settings.load(path)
    checks = {
        "theme": reloaded.theme == "bronze",
        "font_size": reloaded.font_size == 12,
        "enabled_providers": reloaded.enabled_providers == ["yandex", "reverso"],
        "primary_provider": reloaded.primary_provider == "reverso",
        "tts_provider": reloaded.tts_provider == "google-tts",
        "native/second": (reloaded.native_language, reloaded.second_language) == ("de", "fr"),
        "hotkeys": reloaded.hotkeys.get("translate") == "Ctrl+Shift+Enter",
        "hotkey_scopes": reloaded.hotkey_scopes.get("translate") == "global",
        "splitter_sizes": reloaded.splitter_sizes == [200, 300, 250],
        "panel_index": reloaded.panel_index == 1,
    }
    for name, ok in checks.items():
        print(f"  {'OK ' if ok else 'ПРОВАЛ'} {name}")

    # Проверяем, что окно пишет состояние само (сплиттер и панель).
    set_language("")
    apply_theme(app, reloaded.theme)
    registry = build_registry()
    configure_registry(registry, reloaded)
    window = MainWindow(
        app=app,
        settings=reloaded,
        settings_path=path,
        registry=registry,
        translation_service=TranslationService(registry),
        history_store=HistoryStore(history_file()),
        speech=SpeechController(settings=reloaded, registry=registry),
    )
    window.show()
    app.processEvents()
    # окно само пишет состояние
    window._splitter.setSizes([111, 222, 333])  # noqa: SLF001
    window._select_panel(0)  # noqa: SLF001
    actual_sizes = list(window._splitter.sizes())  # noqa: SLF001
    window._persist()  # noqa: SLF001

    after = Settings.load(path)
    checks["window splitter"] = after.splitter_sizes == actual_sizes
    checks["window panel"] = after.panel_index == 0
    print(f"  {'OK ' if checks['window splitter'] else 'ПРОВАЛ'} window splitter ({actual_sizes})")
    print(f"  {'OK ' if checks['window panel'] else 'ПРОВАЛ'} window panel")

    ok = all(checks.values())
    print("OK" if ok else "ПРОВАЛ")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
