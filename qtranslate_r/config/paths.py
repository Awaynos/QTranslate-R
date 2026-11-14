"""Пути к данным, настройкам и ресурсам приложения.

Собранное приложение хранит данные по правилам ОС: APPDATA в Windows,
Application Support в macOS, XDG в Linux. При запуске из исходников данные
остаются в `_local`, чтобы не трогать профиль пользователя.
"""

from __future__ import annotations

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


def _user_base(kind: str) -> Path:
    from ..platform.userpaths import base

    return base(kind, APP_DIR_NAME)


def _ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def user_data_dir() -> Path:
    return _user_base("data")


def user_config_dir() -> Path:
    return _user_base("config")


def user_cache_dir() -> Path:
    return _user_base("cache")


def _use_user_dirs() -> bool:
    return is_frozen() or not (project_root() / "_local").is_dir()


def data_dir() -> Path:
    if _use_user_dirs():
        return _ensure(user_data_dir())
    return _ensure(project_root() / "_local" / "data")


def config_dir() -> Path:
    if _use_user_dirs():
        return _ensure(user_config_dir())
    return _ensure(project_root() / "_local" / "data")


def cache_dir() -> Path:
    if _use_user_dirs():
        return _ensure(user_cache_dir())
    return _ensure(project_root() / "_local" / "cache")


def settings_file() -> Path:
    return config_dir() / "settings.json"


def history_file() -> Path:
    return data_dir() / "history.json"


def app_icon_file() -> Path:
    return resource("icons/app.png")
