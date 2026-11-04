"""Базовые каталоги пользователя по правилам ОС."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _xdg(variable: str, fallback: str) -> Path:
    value = (os.environ.get(variable) or "").strip()
    if value:
        path = Path(value).expanduser()
        if path.is_absolute():
            return path
    return Path.home() / fallback


def _windows_base(local: bool) -> Path:
    if local:
        value = os.environ.get("LOCALAPPDATA")
        if value:
            return Path(value)
        return Path.home() / "AppData" / "Local"
    value = os.environ.get("APPDATA")
    if value:
        return Path(value)
    return Path.home() / "AppData" / "Roaming"


def base(kind: str, app_name: str) -> Path:
    if kind == "data":
        if sys.platform == "win32":
            return _windows_base(False) / app_name
        if sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / app_name
        return _xdg("XDG_DATA_HOME", ".local/share") / app_name

    if kind == "config":
        if sys.platform == "win32":
            return _windows_base(False) / app_name
        if sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / app_name
        return _xdg("XDG_CONFIG_HOME", ".config") / app_name

    if kind == "cache":
        if sys.platform == "win32":
            return _windows_base(True) / app_name
        if sys.platform == "darwin":
            return Path.home() / "Library" / "Caches" / app_name
        return _xdg("XDG_CACHE_HOME", ".cache") / app_name

    raise ValueError(f"unknown directory kind: {kind}")
