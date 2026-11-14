"""Инициализация приложения в Linux."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication

DESKTOP_ID = "qtranslate-remake"
_ICON_NAME = "qtranslate-remake.png"


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


def _local_share() -> Path:
    base = os.environ.get("XDG_DATA_HOME")
    if base and Path(base).is_absolute():
        return Path(base)
    return Path.home() / ".local" / "share"


def desktop_installed() -> bool:
    return any((base / "applications" / f"{DESKTOP_ID}.desktop").is_file() for base in _data_dirs())


def _icon_installed() -> bool:
    return any(
        (base / "icons" / "hicolor" / "256x256" / "apps" / _ICON_NAME).is_file()
        for base in _data_dirs()
    )


def _quote(value: str) -> str:
    if not any(char in value for char in ' \t"\'\\'):
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _exec_line() -> str:
    if getattr(sys, "frozen", False):
        executable = os.environ.get("APPIMAGE") or sys.executable
        return _quote(executable)
    from ...config.paths import project_root

    return f"{_quote(sys.executable)} {_quote(str(project_root() / 'run.py'))}"


def _install_desktop() -> None:
    target = _local_share() / "applications" / f"{DESKTOP_ID}.desktop"
    if target.is_file():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=QTranslate Remake\n"
        "Comment=Desktop translator\n"
        f"Exec={_exec_line()}\n"
        f"Icon={DESKTOP_ID}\n"
        "Terminal=false\n"
        "Categories=Utility;\n"
        "Keywords=translate;translator;dictionary;ocr;\n"
        f"StartupWMClass={DESKTOP_ID}\n"
    )
    target.write_text(content, encoding="utf-8")


def _install_icon() -> None:
    from ...config.paths import app_icon_file

    source = app_icon_file()
    if not source.is_file() or _icon_installed():
        return
    target = _local_share() / "icons" / "hicolor" / "256x256" / "apps" / _ICON_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def set_taskbar_identity() -> None:
    if not desktop_installed():
        _install_desktop()
    _install_icon()
    QGuiApplication.setDesktopFileName(DESKTOP_ID)
