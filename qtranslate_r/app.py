"""Точка входа: настройка Qt, сборка слоёв, запуск окна."""

from __future__ import annotations

import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from . import __app_name__
from .config import Settings, app_icon_file, history_file, resource, settings_file
from .core.history import HistoryStore
from .core.setup import build_registry, configure_registry
from .core.translation import TranslationService
from .inline import InlineReplaceController
from .localization import set_language
from .platform import app as platform_app
from .quick import QuickTranslateController
from .single_instance import SingleInstance
from .speech import SpeechController
from .ui.icons import ensure_ico, set_directory as set_icons_directory
from .ui.main_window import MainWindow
from .ui.theme import apply_theme

_FONT_FAMILY = "Segoe UI"
_COMMANDS = {
    "--quick": "quick",
    "--replace": "replace",
    "--ocr": "ocr",
    "--show": "show",
}


def _requested_command() -> str:
    for argument in sys.argv[1:]:
        if argument in _COMMANDS:
            return _COMMANDS[argument]
    return ""


def _doctor() -> int:
    from .platform.doctor import report

    for line in report():
        print(line)
    return 0


def _install_hyprland_binds() -> int:
    from .platform.linux.hyprland import install, install_rules, reload_hyprland

    try:
        path, changed = install()
        rules_path, rules_changed = install_rules()
    except FileNotFoundError as exc:
        print(f"Hyprland config not found: {exc}")
        return 1

    if not changed and not rules_changed:
        print(f"Hyprland integration already present: {path}")
        return 0

    print(f"Hyprland binds: {path}")
    if rules_path != path:
        print(f"Hyprland rules: {rules_path}")
    if reload_hyprland():
        print("Hyprland reloaded")
    else:
        print("Run 'hyprctl reload' to apply the changes")
    return 0


def main() -> int:
    if "--install-hyprland-binds" in sys.argv[1:]:
        return _install_hyprland_binds()
    if "--doctor" in sys.argv[1:]:
        return _doctor()

    app = QApplication(sys.argv)
    instance = SingleInstance()
    requested = _requested_command()
    if not instance.start(requested or "show"):
        return 0

    app.setApplicationName(__app_name__)
    app.setWindowIcon(QIcon(str(app_icon_file())))

    settings = Settings.load(settings_file())
    set_language(settings.interface_language)
    set_icons_directory(resource("icons"))
    platform_app.set_taskbar_identity()

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

    def dispatch(command: str) -> None:
        if command == "quick":
            quick.trigger()
        elif command == "replace":
            inline.trigger()
        elif command == "ocr":
            window.trigger_ocr()
        else:
            window.showNormal()
            window.raise_()
            window.activateWindow()

    instance.commandReceived.connect(dispatch)
    app.aboutToQuit.connect(instance.stop)
    if requested:
        QTimer.singleShot(0, lambda: dispatch(requested))

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
