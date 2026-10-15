"""Всплывающее окно быстрого перевода."""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QCursor, QGuiApplication, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .. import __app_name__
from ..config.paths import app_icon_file
from ..domain.language import AUTO, language_name
from ..domain.models import TranslationResult
from ..localization import tr
from .sizing import lock_button_widths

_WIDTH = 440
_MAX_BODY = 320


def _preview(text: str, limit: int = 140) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[: limit - 1] + "\u2026"


class QuickTranslatePopup(QWidget):
    """Небольшая карточка рядом с курсором: исходный фрагмент и перевод."""

    speakRequested = Signal(str, str)

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(_WIDTH)
        self._pinned = False
        self._result: TranslationResult | None = None
        self._source_text = ""
        self._language = "en"

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("Card")
        outer.addWidget(card)

        inner = QVBoxLayout(card)
        inner.setContentsMargins(14, 12, 14, 12)
        inner.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(6)
        icon_path = app_icon_file()
        if icon_path.is_file():
            logo = QLabel()
            logo.setPixmap(
                QPixmap(str(icon_path)).scaled(
                    18,
                    18,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            header.addWidget(logo)
        title = QLabel(__app_name__)
        title.setObjectName("CardTitle")
        header.addWidget(title)
        self._detected = QLabel()
        self._detected.setObjectName("Detected")
        header.addWidget(self._detected)
        header.addStretch(1)

        self._pin_button = QPushButton("\u2b50")
        self._pin_button.setObjectName("Copy")
        self._pin_button.setToolTip(tr("popup.pin"))
        self._pin_button.clicked.connect(self._toggle_pin)
        header.addWidget(self._pin_button)

        close_button = QPushButton("\u2715")
        close_button.setObjectName("Copy")
        close_button.setToolTip(tr("popup.close"))
        close_button.clicked.connect(self.hide)
        header.addWidget(close_button)
        inner.addLayout(header)

        self._source = QLabel()
        self._source.setObjectName("CardMeta")
        self._source.setWordWrap(True)
        inner.addWidget(self._source)

        self._body = QLabel()
        self._body.setObjectName("CardBody")
        self._body.setWordWrap(True)
        self._body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        inner.addWidget(self._body)

        footer = QHBoxLayout()
        footer.addStretch(1)
        self._speak_button = QPushButton(tr("popup.speak"))
        self._speak_button.setObjectName("Copy")
        self._speak_button.clicked.connect(self._speak)
        footer.addWidget(self._speak_button)

        self._copy_button = QPushButton(tr("popup.copy"))
        self._copy_button.setObjectName("Copy")
        self._copy_button.clicked.connect(self._copy)
        footer.addWidget(self._copy_button)
        inner.addLayout(footer)

        lock_button_widths(self)


    def show_loading(self, source_text: str) -> None:
        self._result = None
        self._source_text = source_text
        self._detected.setText("")
        self._source.setText(_preview(source_text))
        self._body.setObjectName("CardMeta")
        self._body.setText(tr("popup.translating"))
        self._restyle_body()
        self._copy_button.setEnabled(False)
        self._show_near_cursor()

    def show_result(self, result: TranslationResult, language: str = "en") -> None:
        self._result = result
        self._language = language
        self._detected.setText(
            tr("results.detected", language=language_name(result.detected_source))
            if result.detected_source and result.detected_source != AUTO
            else ""
        )
        self._body.setObjectName("CardBody" if result.ok else "CardError")
        self._body.setText(result.text if result.ok else (result.error or tr("errors.empty_response")))
        self._restyle_body()
        self._copy_button.setEnabled(result.ok)
        self._show_near_cursor()

    def show_error(self, message: str) -> None:
        self._result = None
        self._detected.setText("")
        self._source.setText("")
        self._body.setObjectName("CardError")
        self._body.setText(message)
        self._restyle_body()
        self._copy_button.setEnabled(False)
        self._show_near_cursor()


    def _restyle_body(self) -> None:
        self._body.style().unpolish(self._body)
        self._body.style().polish(self._body)

    def _show_near_cursor(self) -> None:
        self.adjustSize()
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        area = screen.availableGeometry()
        pos = QCursor.pos()
        x = min(max(pos.x() + 14, area.left()), area.right() - self.width())
        y = min(max(pos.y() + 14, area.top()), area.bottom() - self.height())
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()

    def focusOutEvent(self, event) -> None:  # noqa: N802 — метод Qt
        if not self._pinned:
            self.hide()
        super().focusOutEvent(event)

    def event(self, event) -> bool:
        if (
            event.type() == QEvent.Type.WindowDeactivate
            and not self._pinned
            and self.isVisible()
        ):
            self.hide()
        return super().event(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802 — метод Qt
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            return
        super().keyPressEvent(event)

    def _toggle_pin(self) -> None:
        self._pinned = not self._pinned
        self._pin_button.setText("\U0001f4cc" if self._pinned else "\u2b50")
        self._pin_button.setToolTip(tr("popup.unpin") if self._pinned else tr("popup.pin"))

    def _copy(self) -> None:
        if self._result is not None and self._result.ok:
            QGuiApplication.clipboard().setText(self._result.text)

    def _speak(self) -> None:
        if self._result is not None and self._result.ok:
            self.speakRequested.emit(self._result.text, self._language)
        elif self._source_text:
            self.speakRequested.emit(self._source_text, self._language)
