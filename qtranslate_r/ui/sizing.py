"""Мелкие правки раскладки."""

from __future__ import annotations

from PySide6.QtWidgets import QPushButton, QWidget


def lock_button_widths(root: QWidget) -> None:
    """Кнопка не должна сжиматься меньше своего текста — иначе он обрезается."""
    for button in root.findChildren(QPushButton):
        hint = button.sizeHint().width()
        if hint > button.minimumWidth():
            button.setMinimumWidth(hint)
