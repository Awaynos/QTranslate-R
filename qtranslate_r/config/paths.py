"""Пути к данным и ресурсам приложения.

Данные приложения:
  - для собранного `.exe` — в профиле пользователя (`%APPDATA%\\QTranslate Remake`),
    потому что папка с программой может быть доступна только на чтение;
  - при запуске из исходников — в `_local/data` рядом с проектом.

Ресурсы (языки, иконки, VERSION) берутся сначала рядом с программой — их можно
править, — а если их там нет, из встроенных в `.exe`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "QTranslate Remake"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def project_root() -> Path:
    """Папка рядом с программой: для `.exe` — папка exe, иначе корень проекта."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def bundle_dir() -> Path:
    """Встроенные ресурсы PyInstaller, либо корень проекта при обычном запуске."""
    return Path(getattr(sys, "_MEIPASS", project_root()))


def resource(relative: str) -> Path:
    """Ресурс: сначала рядом с программой (его можно править), затем встроенный."""
    beside = project_root() / relative
    if beside.exists():
        return beside
    return bundle_dir() / relative


def data_dir() -> Path:
    if is_frozen():
        base = Path(os.environ.get("APPDATA") or Path.home()) / APP_DIR_NAME
    else:
        base = project_root() / "_local" / "data"
    base.mkdir(parents=True, exist_ok=True)
    return base


def settings_file() -> Path:
    return data_dir() / "settings.json"


def history_file() -> Path:
    return data_dir() / "history.json"


def app_icon_file() -> Path:
    return resource("icons/app.png")
