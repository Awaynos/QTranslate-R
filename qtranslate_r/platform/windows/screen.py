"""Захват области экрана."""

from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtGui import QImage


def capture_region(screen, rect: QRect) -> QImage:
    geometry = screen.geometry()
    image = screen.grabWindow(0).toImage()
    if image.isNull():
        return image

    scale_x = image.width() / max(1, geometry.width())
    scale_y = image.height() / max(1, geometry.height())
    x = round((rect.x() - geometry.x()) * scale_x)
    y = round((rect.y() - geometry.y()) * scale_y)
    width = round(rect.width() * scale_x)
    height = round(rect.height() * scale_y)
    return image.copy(x, y, max(1, width), max(1, height))
