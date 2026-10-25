"""Выбор области экрана для распознавания текста."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ..localization import tr

_ACCENT = QColor("#3d9bff")
_MIN_SIZE = 8


class OcrOverlay(QWidget):
    selected = Signal(QRect)
    cancelled = Signal()

    def __init__(self, screen) -> None:
        super().__init__()
        self._screen = screen
        self._origin = None
        self._current = None
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setGeometry(screen.geometry())

    def start(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.FocusReason.OtherFocusReason)

    def mousePressEvent(self, event) -> None:  # noqa: N802 — метод Qt
        if event.button() == Qt.MouseButton.RightButton:
            self._cancel()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.position().toPoint()
            self._current = self._origin
            self.update()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 — метод Qt
        if self._origin is not None:
            self._current = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 — метод Qt
        if event.button() != Qt.MouseButton.LeftButton or self._origin is None:
            return
        rect = self._selection()
        self._origin = None
        self._current = None
        if rect.width() < _MIN_SIZE or rect.height() < _MIN_SIZE:
            self.update()
            return
        self.hide()
        self.selected.emit(rect)

    def keyPressEvent(self, event) -> None:  # noqa: N802 — метод Qt
        if event.key() == Qt.Key.Key_Escape:
            self._cancel()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:  # noqa: N802 — метод Qt
        self.cancelled.emit()
        super().closeEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802 — метод Qt
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        rect = self._selection()
        if rect.isValid() and rect.width() > 0 and rect.height() > 0:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(QPen(_ACCENT, 2))
            painter.drawRect(rect)

            label = f"{rect.width()} × {rect.height()}"
            painter.setFont(QFont("Segoe UI", 9))
            metrics = painter.fontMetrics()
            box = metrics.boundingRect(label).adjusted(-8, -4, 8, 4)
            box.moveTopLeft(rect.bottomLeft() + QPoint(0, 8))
            painter.fillRect(box, QColor(0, 0, 0, 170))
            painter.setPen(QColor("#ffffff"))
            painter.drawText(box, Qt.AlignmentFlag.AlignCenter, label)
        else:
            painter.setPen(QColor("#ffffff"))
            painter.setFont(QFont("Segoe UI", 13))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                tr("ocr.select"),
            )

    def _selection(self) -> QRect:
        if self._origin is None or self._current is None:
            return QRect()
        return QRect(self._origin, self._current).normalized()

    def _cancel(self) -> None:
        self.hide()
        self.cancelled.emit()


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
