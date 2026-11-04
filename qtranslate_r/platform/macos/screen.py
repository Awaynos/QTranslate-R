"""Заглушка захвата экрана."""

from __future__ import annotations

from PySide6.QtGui import QImage


def capture_region(screen, rect) -> QImage:
    return QImage()


def has_region_selection() -> bool:
    return False


def select_region() -> tuple[int, int, int, int] | None:
    return None
