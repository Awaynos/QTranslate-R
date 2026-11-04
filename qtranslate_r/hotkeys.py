"""Действия с назначаемыми клавишами и их разбор."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence


@dataclass(frozen=True)
class HotkeyAction:
    id: str
    label_key: str
    default: str
    scope: str


ACTIONS: tuple[HotkeyAction, ...] = (
    HotkeyAction("quick_translate", "hotkey.quick_translate", "Ctrl+Q", "global"),
    HotkeyAction("replace_selection", "hotkey.replace_selection", "Ctrl+1", "global"),
    HotkeyAction("ocr", "hotkey.ocr", "Ctrl+I", "global"),
    HotkeyAction("translate", "hotkey.translate", "Ctrl+Return", "local"),
    HotkeyAction("copy_result", "hotkey.copy_result", "Ctrl+Shift+C", "local"),
    HotkeyAction("clear_input", "hotkey.clear_input", "Ctrl+Shift+X", "local"),
    HotkeyAction("swap_languages", "hotkey.swap_languages", "Ctrl+Shift+S", "local"),
    HotkeyAction("speak", "hotkey.speak", "Ctrl+E", "local"),
    HotkeyAction("dictionary", "hotkey.dictionary", "Ctrl+D", "local"),
    HotkeyAction("document", "hotkey.document", "Ctrl+Shift+D", "local"),
    HotkeyAction("history", "hotkey.history", "Ctrl+H", "local"),
    HotkeyAction("settings", "hotkey.settings", "Ctrl+Comma", "local"),
)

SCOPES: dict[str, str] = {action.id: action.scope for action in ACTIONS}


def defaults() -> dict[str, str]:
    from .platform.hotkey_defaults import defaults as platform_defaults

    merged = {action.id: action.default for action in ACTIONS}
    merged.update(platform_defaults())
    return merged


def default(action_id: str) -> str:
    return defaults().get(action_id, "")


def binding(settings, action_id: str) -> str:
    return (settings.hotkeys or {}).get(action_id) or default(action_id)


def scope(settings, action_id: str) -> str:
    return (settings.hotkey_scopes or {}).get(action_id) or SCOPES.get(action_id, "local")


def combination(sequence: str) -> tuple[int, bool, bool, bool, bool] | None:
    """Строка вида «Ctrl+Q» -> (Qt-клавиша, ctrl, shift, alt, win)."""
    parsed = QKeySequence(sequence)
    if parsed.isEmpty():
        return None
    combo = parsed[0]
    mods = combo.keyboardModifiers()
    return (
        combo.key(),
        bool(mods & Qt.KeyboardModifier.ControlModifier),
        bool(mods & Qt.KeyboardModifier.ShiftModifier),
        bool(mods & Qt.KeyboardModifier.AltModifier),
        bool(mods & Qt.KeyboardModifier.MetaModifier),
    )
