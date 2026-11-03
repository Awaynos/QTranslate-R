"""Заглушка захвата экрана."""

from __future__ import annotations

from PySide6.QtGui import QImage


def capture_region(screen, rect) -> QImage:
    return QImage()
