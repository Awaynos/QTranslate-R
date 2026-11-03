"""Qt-клавиши в виртуальные коды Windows."""

from __future__ import annotations

from PySide6.QtCore import Qt

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


def virtual_key(qt_key: int) -> int | None:
    if Qt.Key.Key_A <= qt_key <= Qt.Key.Key_Z:
        return qt_key
    if Qt.Key.Key_0 <= qt_key <= Qt.Key.Key_9:
        return qt_key
    return _VK_SPECIAL.get(qt_key)
