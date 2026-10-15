"""Чипы включения сервисов."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from ...localization import tr


class ProviderBar(QWidget):
    changed = Signal()

    def __init__(
        self,
        translators: list[tuple[str, str]],
        enabled_ids: list[str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._buttons: dict[str, QPushButton] = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        for provider_id, name in translators:
            button = QPushButton(name)
            button.setObjectName("Chip")
            button.setCheckable(True)
            button.setChecked(provider_id in enabled_ids)
            button.setToolTip(tr("provider.enable_tooltip", name=name))
            button.toggled.connect(lambda _checked: self.changed.emit())
            self._buttons[provider_id] = button
            layout.addWidget(button)

        layout.addStretch(1)

    def enabled_ids(self) -> list[str]:
        return [pid for pid, button in self._buttons.items() if button.isChecked()]

    def set_enabled(self, enabled_ids: list[str]) -> None:
        for provider_id, button in self._buttons.items():
            button.blockSignals(True)
            button.setChecked(provider_id in enabled_ids)
            button.blockSignals(False)
        self.changed.emit()
