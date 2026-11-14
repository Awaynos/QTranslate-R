"""Win32-интеграция окна: ресайз безрамочного окна и иконка."""

from __future__ import annotations

import ctypes
from ctypes import wintypes

from PySide6.QtCore import QPoint

_WM_NCHITTEST = 0x0084
_RESIZE_MARGIN = 6


class _WinMessage(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt_x", wintypes.LONG),
        ("pt_y", wintypes.LONG),
    ]


def start_system_move(window) -> bool:
    return False


def start_system_resize(window, edges) -> bool:
    return False


def apply_window_icon(window, ico) -> None:
    if ico is None:
        return
    try:
        user32 = ctypes.windll.user32
        lr_loadfromfile = 0x0010
        image_icon = 1
        wm_seticon = 0x0080
        icon_small = 0
        icon_big = 1

        hwnd = wintypes.HWND(int(window.winId()))
        big = user32.LoadImageW(None, str(ico), image_icon, 32, 32, lr_loadfromfile)
        small = user32.LoadImageW(None, str(ico), image_icon, 16, 16, lr_loadfromfile)
        if big:
            user32.SendMessageW(hwnd, wm_seticon, icon_big, big)
        if small:
            user32.SendMessageW(hwnd, wm_seticon, icon_small, small)
    except (AttributeError, OSError, TypeError):
        pass


def enable_native_resize(window) -> None:
    if getattr(window, "_thick_frame", False):
        return
    try:
        user32 = ctypes.windll.user32
        user32.GetWindowLongPtrW.restype = ctypes.c_longlong
        user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.SetWindowLongPtrW.restype = ctypes.c_longlong
        user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_longlong]

        gwl_style = -16
        ws_thickframe = 0x00040000
        ws_minimizebox = 0x00020000
        ws_maximizebox = 0x00010000

        hwnd = wintypes.HWND(int(window.winId()))
        style = user32.GetWindowLongPtrW(hwnd, gwl_style)
        user32.SetWindowLongPtrW(
            hwnd,
            gwl_style,
            style | ws_thickframe | ws_minimizebox | ws_maximizebox,
        )
        window._thick_frame = True
    except (AttributeError, OSError, TypeError):
        window._thick_frame = False


def native_event(window, event_type, message):
    if window.isMaximized():
        return None
    try:
        msg = ctypes.cast(int(message), ctypes.POINTER(_WinMessage)).contents
    except (TypeError, ValueError):
        return None

    if msg.message != _WM_NCHITTEST:
        return None

    x = ctypes.c_short(msg.lParam & 0xFFFF).value
    y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
    point = window.mapFromGlobal(QPoint(x, y))
    left = point.x() < _RESIZE_MARGIN
    right = point.x() > window.width() - _RESIZE_MARGIN
    top = point.y() < _RESIZE_MARGIN
    bottom = point.y() > window.height() - _RESIZE_MARGIN

    if top and left:
        return True, 13
    if top and right:
        return True, 14
    if bottom and left:
        return True, 16
    if bottom and right:
        return True, 17
    if left:
        return True, 10
    if right:
        return True, 11
    if top:
        return True, 12
    if bottom:
        return True, 15
    return None


def cursor_position() -> tuple[int, int] | None:
    return None


def move_window(title: str, x: int, y: int) -> bool:
    return False
