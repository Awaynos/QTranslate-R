"""Диалог истории переводов."""

from __future__ import annotations

import time

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...core.history import HistoryEntry, HistoryStore
from ...domain.language import language_name
from ...localization import tr
from ..sizing import lock_button_widths


def _preview(text: str, limit: int = 70) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[: limit - 1] + "\u2026"


class HistoryDialog(QDialog):
    def __init__(self, history: HistoryStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._history = history
        self._selected: HistoryEntry | None = None

        self.setWindowTitle(tr("history.title"))
        self.resize(680, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(lambda _: self._accept_selected())
        layout.addWidget(self._list, 1)

        self._empty = QLabel(tr("history.empty"))
        self._empty.setObjectName("EmptyState")
        self._empty.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._empty)

        buttons = QHBoxLayout()
        clear_button = QPushButton(tr("history.clear_all"))
        clear_button.clicked.connect(self._clear)
        buttons.addWidget(clear_button)
        buttons.addStretch(1)

        restore = QPushButton(tr("history.restore"))
        restore.setObjectName("Primary")
        restore.clicked.connect(self._accept_selected)
        buttons.addWidget(restore)

        close = QPushButton(tr("history.close"))
        close.clicked.connect(self.reject)
        buttons.addWidget(close)
        layout.addLayout(buttons)

        self._reload()
        lock_button_widths(self)

    def _reload(self) -> None:
        self._list.clear()
        entries = self._history.entries
        self._empty.setVisible(not entries)
        self._list.setVisible(bool(entries))
        for index, entry in enumerate(entries):
            stamp = time.strftime("%d.%m.%Y %H:%M", time.localtime(entry.timestamp))
            item = QListWidgetItem(
                f"{_preview(entry.source_text)}\n"
                f"\u2192 {_preview(entry.translated_text)}  \u00b7  "
                f"{language_name(entry.source_language)} \u2192 {language_name(entry.target_language)}"
                f"  \u00b7  {entry.provider_name}  \u00b7  {stamp}"
            )
            item.setData(Qt.UserRole, index)
            self._list.addItem(item)

    def _selected_entry(self) -> HistoryEntry | None:
        item = self._list.currentItem()
        if item is None:
            return None
        index = item.data(Qt.UserRole)
        entries = self._history.entries
        if isinstance(index, int) and 0 <= index < len(entries):
            return entries[index]
        return None

    def _accept_selected(self) -> None:
        entry = self._selected_entry()
        if entry is not None:
            self._selected = entry
            self.accept()

    def _clear(self) -> None:
        self._history.clear()
        self._reload()

    def selected_entry(self) -> HistoryEntry | None:
        return self._selected
