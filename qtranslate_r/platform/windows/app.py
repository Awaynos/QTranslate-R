"""Идентификация приложения в Windows."""

from __future__ import annotations

import ctypes


def set_taskbar_identity() -> None:
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("QTranslate.Remake")
    except (AttributeError, OSError):
        pass
