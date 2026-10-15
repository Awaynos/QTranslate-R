"""Выбор языков: источник, обмен, цель."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget

from ...domain.language import AUTO, AUTO_PAIR, all_languages, pair_label
from ...localization import tr


def _fill_source(combo: QComboBox) -> None:
    combo.clear()
    for language in all_languages(include_auto=True):
        combo.addItem(language.name, language.code)
    combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)


def _select(combo: QComboBox, code: str) -> None:
    index = combo.findData(code)
    if index >= 0:
        combo.setCurrentIndex(index)


class LanguageBar(QWidget):
    swapRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pair_native = ""
        self._pair_second = ""

        self.source_combo = QComboBox()
        self.target_combo = QComboBox()
        self.swap_button = QPushButton("\u21c4")
        self.swap_button.setObjectName("Ghost")
        self.swap_button.setToolTip(tr("button.swap"))
        self.swap_button.setFixedWidth(40)
        self.swap_button.clicked.connect(self.swapRequested.emit)

        _fill_source(self.source_combo)
        self._rebuild_target()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.source_combo, 1)
        layout.addWidget(self.swap_button)
        layout.addWidget(self.target_combo, 1)


    def source(self) -> str:
        return self.source_combo.currentData() or AUTO

    def target(self) -> str:
        return self.target_combo.currentData() or "en"

    def set_languages(self, source: str, target: str) -> None:
        _select(self.source_combo, source)
        _select(self.target_combo, target)

    def set_pair(self, native: str, second: str) -> None:
        """Родной и второй язык для пункта «Автоопределение (Родной-Второй)»."""
        self._pair_native = native or ""
        self._pair_second = second or ""
        self._rebuild_target()

    def _rebuild_target(self) -> None:
        current = self.target_combo.currentData()
        self.target_combo.blockSignals(True)
        self.target_combo.clear()
        if self._pair_native and self._pair_second:
            self.target_combo.addItem(
                pair_label(self._pair_native, self._pair_second), AUTO_PAIR
            )
        for language in all_languages(include_auto=False):
            self.target_combo.addItem(language.name, language.code)
        self.target_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        index = self.target_combo.findData(current) if current else -1
        self.target_combo.setCurrentIndex(index if index >= 0 else 0)
        self.target_combo.blockSignals(False)

    def swap(self) -> None:
        source = self.source()
        target = self.target()

        if target == AUTO_PAIR:
            # Из авто-пары выходим в её же языки.
            _select(self.source_combo, self._pair_native or AUTO)
            _select(self.target_combo, self._pair_second or "en")
            return

        if source == AUTO:
            # Из "авто" в цель не поставить: источником делаем прежнюю цель.
            _select(self.source_combo, target)
            _select(self.target_combo, "en" if target != "en" else "ru")
        else:
            _select(self.source_combo, target)
            _select(self.target_combo, source)
