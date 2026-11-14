"""Инициализация приложения в Linux."""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtGui import QGuiApplication

DESKTOP_ID = "qtranslate-remake"


def _data_dirs() -> list[Path]:
    dirs = []
    base = os.environ.get("XDG_DATA_HOME")
    if base and Path(base).is_absolute():
        dirs.append(Path(base))
    else:
        dirs.append(Path.home() / ".local" / "share")
    for item in os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":"):
        if item:
            dirs.append(Path(item))
    return dirs


def desktop_installed() -> bool:
    return any((base / "applications" / f"{DESKTOP_ID}.desktop").is_file() for base in _data_dirs())


def set_taskbar_identity() -> None:
    if desktop_installed():
        QGuiApplication.setDesktopFileName(DESKTOP_ID)
