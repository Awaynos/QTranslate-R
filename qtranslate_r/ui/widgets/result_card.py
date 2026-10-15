"""Карточка результата одного сервиса."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...domain.language import AUTO, language_name
from ...domain.models import TranslationResult
from ...localization import tr

# Узкая карточка: метаданные скрываем, чтобы не резать кнопку.
_NARROW_WIDTH = 430


class ResultCard(QFrame):
    def __init__(self, result: TranslationResult, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._result = result
        self.setObjectName("Card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(8)

        self._title = QLabel(result.provider_name)
        self._title.setObjectName("CardTitle")
        header.addWidget(self._title)

        self._detected = QLabel()
        self._detected.setObjectName("Detected")
        if result.detected_source and result.detected_source != AUTO:
            self._detected.setText(
                tr("results.detected", language=language_name(result.detected_source))
            )
        header.addWidget(self._detected)

        header.addStretch(1)

        self._meta = QLabel(tr("results.elapsed", ms=result.elapsed_ms))
        self._meta.setObjectName("CardMeta")
        header.addWidget(self._meta)

        self._copy_button = QPushButton(tr("results.copy"))
        self._copy_button.setObjectName("Copy")
        self._copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_button.setEnabled(result.ok)
        self._copy_button.setMinimumWidth(96)
        self._copy_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._copy_button.clicked.connect(self._copy)
        header.addWidget(self._copy_button)

        layout.addLayout(header)

        body = QLabel(result.text if result.ok else (result.error or tr("errors.empty_response")))
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        body.setObjectName("CardBody" if result.ok else "CardError")
        layout.addWidget(body)

    @property
    def result(self) -> TranslationResult:
        return self._result

    def resizeEvent(self, event) -> None:  # noqa: N802 — метод Qt
        super().resizeEvent(event)
        narrow = self.width() < _NARROW_WIDTH
        self._meta.setVisible(not narrow)
        self._detected.setVisible(not narrow and bool(self._detected.text()))

    def _copy(self) -> None:
        QGuiApplication.clipboard().setText(self._result.text)
        self._copy_button.setText("\u2713")
        self._copy_button.setEnabled(False)
        QTimer.singleShot(1200, self._reset_copy_button)

    def _reset_copy_button(self) -> None:
        self._copy_button.setText(tr("results.copy"))
        self._copy_button.setEnabled(True)
