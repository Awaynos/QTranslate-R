"""Индикаторы загрузки с логотипом приложения."""

from __future__ import annotations

import time

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget

from ..config.paths import app_icon_file
from .theme import palette

# Держим значок чуть дольше мгновенного ответа, чтобы не было мигания.
_MIN_VISIBLE_MS = 350


def logo_pixmap(size: int) -> QPixmap:
    path = app_icon_file()
    if not path.is_file():
        return QPixmap()
    return QPixmap(str(path)).scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


class CursorLoadingIndicator(QWidget):
    """Значок у курсора: логотип в центре и вращающаяся дуга вокруг."""

    def __init__(self, settings, parent: QWidget | None = None) -> None:
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput,
        )
        self._settings = settings
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(46, 46)

        self._logo = logo_pixmap(24)
        self._angle = 0
        self._shown_at = 0.0
        self._hide_timer: QTimer | None = None

        self._spin = QTimer(self)
        self._spin.setInterval(30)
        self._spin.timeout.connect(self._advance)

        self._follow = QTimer(self)
        self._follow.setInterval(50)
        self._follow.timeout.connect(self._move_to_cursor)


    def show_loading(self) -> None:
        if self._hide_timer is not None:
            self._hide_timer.stop()
            self._hide_timer = None
        if self.isVisible():
            return
        self._move_to_cursor()
        self._shown_at = time.monotonic()
        self.show()
        self.raise_()
        self._spin.start()
        self._follow.start()

    def hide_loading(self) -> None:
        if not self.isVisible():
            return
        elapsed = (time.monotonic() - self._shown_at) * 1000
        if elapsed >= _MIN_VISIBLE_MS:
            self._hide_now()
            return
        if self._hide_timer is not None:
            return
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(int(_MIN_VISIBLE_MS - elapsed))
        self._hide_timer.timeout.connect(self._hide_now)
        self._hide_timer.start()

    def _hide_now(self) -> None:
        if self._hide_timer is not None:
            self._hide_timer.stop()
            self._hide_timer = None
        self._spin.stop()
        self._follow.stop()
        self.hide()


    def _advance(self) -> None:
        self._angle = (self._angle + 14) % 360
        self.update()

    def _move_to_cursor(self) -> None:
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        area = screen.availableGeometry()
        point = QCursor.pos()
        x = min(max(point.x() + 16, area.left()), area.right() - self.width())
        y = min(max(point.y() + 20, area.top()), area.bottom() - self.height())
        self.move(x, y)

    def paintEvent(self, event) -> None:  # noqa: N802 — метод Qt
        colors = palette(self._settings.theme)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        ring = QRectF(5, 5, self.width() - 10, self.height() - 10)

        painter.setPen(QPen(QColor(colors["border"]), 2))
        painter.drawEllipse(ring)

        painter.setPen(QPen(QColor(colors["accent"]), 2))
        painter.drawArc(ring, self._angle * 16, 110 * 16)

        if not self._logo.isNull():
            painter.drawPixmap(
                (self.width() - self._logo.width()) // 2,
                (self.height() - self._logo.height()) // 2,
                self._logo,
            )


class InlineLoading(QWidget):
    """Логотип и тонкая полоса — для главного окна, пока идёт перевод."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        logo = QLabel()
        logo.setPixmap(logo_pixmap(16))
        layout.addWidget(logo)

        self._bar = QProgressBar()
        self._bar.setRange(0, 0)
        self._bar.setTextVisible(False)
        self._bar.setFixedSize(96, 6)
        layout.addWidget(self._bar)

        self.setVisible(False)

    def set_loading(self, loading: bool) -> None:
        if self.isVisible() == loading:
            return
        self.setVisible(loading)
