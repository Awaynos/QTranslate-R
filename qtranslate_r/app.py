"""Точка входа: настройка Qt, сборка слоёв, запуск окна."""

from __future__ import annotations

import sys

from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from . import __app_name__
from .config import Settings, app_icon_file, history_file, resource, settings_file
from .core.history import HistoryStore
from .core.setup import build_registry, configure_registry
from .core.translation import TranslationService
from .inline import InlineReplaceController
from .localization import set_language
from .quick import QuickTranslateController
from .speech import SpeechController
from .ui.icons import ensure_ico, set_directory as set_icons_directory
from .ui.main_window import MainWindow
from .ui.theme import apply_theme

_FONT_FAMILY = "Segoe UI"


def _set_taskbar_identity() -> None:
    """Отдельная запись в панели задач (иначе Windows группирует как «Python»)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("QTranslate.Remake")
    except (AttributeError, OSError):
        pass


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setWindowIcon(QIcon(str(app_icon_file())))

    settings = Settings.load(settings_file())
    set_language(settings.interface_language)
    set_icons_directory(resource("icons"))
    _set_taskbar_identity()

    icon_path = ensure_ico() or app_icon_file()
    app.setWindowIcon(QIcon(str(icon_path)))
    app.setFont(QFont(_FONT_FAMILY, int(settings.font_size)))
    apply_theme(app, settings.theme)

    registry = build_registry()
    configure_registry(registry, settings)
    service = TranslationService(registry)
    speech = SpeechController(settings=settings, registry=registry)

    window = MainWindow(
        app=app,
        settings=settings,
        settings_path=settings_file(),
        registry=registry,
        translation_service=service,
        history_store=HistoryStore(history_file()),
        speech=speech,
    )
    window.show()

    quick = QuickTranslateController(settings=settings, service=service, speech=speech)
    window.hotkeysChanged.connect(quick.start)
    app.aboutToQuit.connect(quick.stop)

    inline = InlineReplaceController(settings=settings, service=service)
    window.hotkeysChanged.connect(inline.start)
    app.aboutToQuit.connect(inline.stop)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
