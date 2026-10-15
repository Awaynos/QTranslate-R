"""Настройки и пути к данным."""

from .paths import (
    app_icon_file,
    bundle_dir,
    data_dir,
    history_file,
    project_root,
    resource,
    settings_file,
)
from .settings import Settings

__all__ = [
    "Settings",
    "app_icon_file",
    "bundle_dir",
    "data_dir",
    "history_file",
    "project_root",
    "resource",
    "settings_file",
]
