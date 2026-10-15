"""Панель словаря: статьи для слова, полученные от сервиса."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..domain.language import language_name
from ..domain.models import DictionaryEntry
from ..localization import tr


class DictionaryPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        self._word = QLabel(tr("dict.title"))
        self._word.setObjectName("CardTitle")
        header.addWidget(self._word)
        self._meta = QLabel("")
        self._meta.setObjectName("CardMeta")
        header.addWidget(self._meta)
        header.addStretch(1)
        layout.addLayout(header)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        holder = QWidget()
        self._entries_layout = QVBoxLayout(holder)
        self._entries_layout.setContentsMargins(0, 0, 0, 0)
        self._entries_layout.setSpacing(10)
        self._scroll.setWidget(holder)
        layout.addWidget(self._scroll, 1)

        self._placeholder = QLabel(tr("dict.placeholder"))
        self._placeholder.setObjectName("EmptyState")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setWordWrap(True)
        layout.addWidget(self._placeholder)

        self._show_placeholder(tr("dict.placeholder"))


    def show_loading(self, word: str, language: str) -> None:
        self._word.setText(word)
        self._meta.setText(language_name(language))
        self._clear_entries()
        self._placeholder.setText(tr("dict.searching"))
        self._placeholder.setVisible(True)
        self._scroll.setVisible(False)

    def show_entries(self, word: str, language: str, entries: list[DictionaryEntry]) -> None:
        self._word.setText(word)
        self._meta.setText(language_name(language))
        self._clear_entries()

        if not entries:
            self._placeholder.setText(tr("dict.not_found"))
            self._placeholder.setVisible(True)
            self._scroll.setVisible(False)
            return

        for entry in entries:
            self._entries_layout.addWidget(self._build_entry(entry))
        self._entries_layout.addStretch(1)
        self._placeholder.setVisible(False)
        self._scroll.setVisible(True)

    def show_error(self, message: str) -> None:
        self._clear_entries()
        self._placeholder.setText(message)
        self._placeholder.setVisible(True)
        self._scroll.setVisible(False)


    def _show_placeholder(self, text: str) -> None:
        self._placeholder.setText(text)
        self._placeholder.setVisible(True)
        self._scroll.setVisible(False)

    def _clear_entries(self) -> None:
        while self._entries_layout.count():
            item = self._entries_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def _build_entry(self, entry: DictionaryEntry) -> QWidget:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        if entry.part_of_speech:
            pos = QLabel(entry.part_of_speech)
            pos.setObjectName("Detected")
            layout.addWidget(pos)

        for index, definition in enumerate(entry.definitions, start=1):
            line = QLabel(f"{index}. {definition}")
            line.setObjectName("CardBody")
            line.setWordWrap(True)
            line.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            layout.addWidget(line)

        return card
