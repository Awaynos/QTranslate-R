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

DEFAULTS: dict[str, str] = {action.id: action.default for action in ACTIONS}
SCOPES: dict[str, str] = {action.id: action.scope for action in ACTIONS}

_VK_SPECIAL: dict[int, int] = {
    Qt.Key.Key_Space: 0x20,
    Qt.Key.Key_Tab: 0x09,
    Qt.Key.Key_Return: 0x0D,
    Qt.Key.Key_Enter: 0x0D,
    Qt.Key.Key_Escape: 0x1B,
    Qt.Key.Key_Insert: 0x2D,
    Qt.Key.Key_Delete: 0x2E,
    Qt.Key.Key_Home: 0x24,
    Qt.Key.Key_End: 0x23,
    Qt.Key.Key_PageUp: 0x21,
    Qt.Key.Key_PageDown: 0x22,
    Qt.Key.Key_Left: 0x25,
    Qt.Key.Key_Up: 0x26,
    Qt.Key.Key_Right: 0x27,
    Qt.Key.Key_Down: 0x28,
}
for _index, _code in enumerate(range(0x70, 0x7C), start=1):
    _VK_SPECIAL[getattr(Qt.Key, f"Key_F{_index}")] = _code


def binding(settings, action_id: str) -> str:
    return (settings.hotkeys or {}).get(action_id) or DEFAULTS.get(action_id, "")


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


def virtual_key(qt_key: int) -> int | None:
    """Qt-клавиша -> виртуальный код Windows для глобального хоткея."""
    if Qt.Key.Key_A <= qt_key <= Qt.Key.Key_Z:
        return qt_key
    if Qt.Key.Key_0 <= qt_key <= Qt.Key.Key_9:
        return qt_key
    return _VK_SPECIAL.get(qt_key)
