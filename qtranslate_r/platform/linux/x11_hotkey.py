"""Глобальные хоткеи X11 через XGrabKey."""

from __future__ import annotations

import ctypes
import ctypes.util
import os
import select
import threading

from PySide6.QtCore import QObject, Qt, Signal

from ...hotkeys import combination
from ..base import NullHotkey

_CONTROL = 0x0004
_SHIFT = 0x0001
_ALT = 0x0008
_SUPER = 0x0040
_LOCK = 0x0002
_NUM = 0x0010
_KEY_PRESS = 2
_KEY_PRESS_MASK = 0x0001
_GRAB_MODE_ASYNC = 1
_BAD_ACCESS = 10

_SPECIAL = {
    Qt.Key.Key_Return: "Return",
    Qt.Key.Key_Enter: "Return",
    Qt.Key.Key_Escape: "Escape",
    Qt.Key.Key_Tab: "Tab",
    Qt.Key.Key_Backspace: "BackSpace",
    Qt.Key.Key_Delete: "Delete",
    Qt.Key.Key_Insert: "Insert",
    Qt.Key.Key_Home: "Home",
    Qt.Key.Key_End: "End",
    Qt.Key.Key_PageUp: "Page_Up",
    Qt.Key.Key_PageDown: "Page_Down",
    Qt.Key.Key_Left: "Left",
    Qt.Key.Key_Right: "Right",
    Qt.Key.Key_Up: "Up",
    Qt.Key.Key_Down: "Down",
    Qt.Key.Key_Space: "space",
    Qt.Key.Key_Comma: "comma",
    Qt.Key.Key_Period: "period",
    Qt.Key.Key_Slash: "slash",
    Qt.Key.Key_Backslash: "backslash",
    Qt.Key.Key_Minus: "minus",
    Qt.Key.Key_Equal: "equal",
    Qt.Key.Key_Semicolon: "semicolon",
    Qt.Key.Key_Apostrophe: "apostrophe",
    Qt.Key.Key_BracketLeft: "bracketleft",
    Qt.Key.Key_BracketRight: "bracketright",
    Qt.Key.Key_QuoteLeft: "grave",
}
for _index in range(1, 13):
    _SPECIAL[getattr(Qt.Key, f"Key_F{_index}")] = f"F{_index}"


class _XKeyEvent(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("serial", ctypes.c_ulong),
        ("send_event", ctypes.c_int),
        ("display", ctypes.c_void_p),
        ("window", ctypes.c_ulong),
        ("root", ctypes.c_ulong),
        ("subwindow", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("x_root", ctypes.c_int),
        ("y_root", ctypes.c_int),
        ("state", ctypes.c_uint),
        ("keycode", ctypes.c_uint),
        ("same_screen", ctypes.c_int),
    ]


class _XEvent(ctypes.Union):
    _fields_ = [
        ("type", ctypes.c_int),
        ("xkey", _XKeyEvent),
        ("pad", ctypes.c_long * 24),
    ]


class _XErrorEvent(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("display", ctypes.c_void_p),
        ("resourceid", ctypes.c_ulong),
        ("serial", ctypes.c_ulong),
        ("error_code", ctypes.c_ubyte),
        ("request_code", ctypes.c_ubyte),
        ("minor_code", ctypes.c_ubyte),
    ]


_ErrorHandler = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(_XErrorEvent))


def _load_x11():
    name = ctypes.util.find_library("X11")
    if not name:
        return None
    library = ctypes.CDLL(name)
    library.XOpenDisplay.argtypes = [ctypes.c_char_p]
    library.XOpenDisplay.restype = ctypes.c_void_p
    library.XCloseDisplay.argtypes = [ctypes.c_void_p]
    library.XCloseDisplay.restype = ctypes.c_int
    library.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
    library.XDefaultRootWindow.restype = ctypes.c_ulong
    library.XStringToKeysym.argtypes = [ctypes.c_char_p]
    library.XStringToKeysym.restype = ctypes.c_ulong
    library.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    library.XKeysymToKeycode.restype = ctypes.c_ubyte
    library.XGrabKey.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_uint,
        ctypes.c_ulong,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
    ]
    library.XGrabKey.restype = ctypes.c_int
    library.XUngrabKey.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_uint, ctypes.c_ulong]
    library.XUngrabKey.restype = ctypes.c_int
    library.XSelectInput.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_long]
    library.XSelectInput.restype = ctypes.c_int
    library.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    library.XSync.restype = ctypes.c_int
    library.XNextEvent.argtypes = [ctypes.c_void_p, ctypes.POINTER(_XEvent)]
    library.XNextEvent.restype = ctypes.c_int
    library.XPending.argtypes = [ctypes.c_void_p]
    library.XPending.restype = ctypes.c_int
    library.XConnectionNumber.argtypes = [ctypes.c_void_p]
    library.XConnectionNumber.restype = ctypes.c_int
    library.XSetErrorHandler.argtypes = [ctypes.c_void_p]
    library.XSetErrorHandler.restype = ctypes.c_void_p
    return library


def _keysym_name(key: int) -> str | None:
    if 0x41 <= key <= 0x5A:
        return chr(key).lower()
    if 0x30 <= key <= 0x39:
        return chr(key)
    return _SPECIAL.get(key)


class _Emitter(QObject):
    activated = Signal()


class X11Hotkey:
    def __init__(self, sequence: str, hotkey_id: int = 1) -> None:
        self._sequence = sequence
        self._id = hotkey_id
        self._emitter = _Emitter()
        self._registered = False
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._pipe_r, self._pipe_w = os.pipe()
        self._grab_error = False
        self._x11 = _load_x11()

    @property
    def activated(self) -> Signal:
        return self._emitter.activated

    @property
    def registered(self) -> bool:
        return self._registered

    def start(self) -> None:
        if self._x11 is None or self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name="x11-hotkey", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        try:
            os.write(self._pipe_w, b"x")
        except OSError:
            pass
        if self._thread is not None:
            self._thread.join(1)
            self._thread = None

    def _on_error(self, display, event) -> int:
        self._grab_error = True
        return 0

    def _modifiers(self) -> tuple[int, int] | None:
        parsed = combination(self._sequence)
        if parsed is None:
            return None
        key, ctrl, shift, alt, win = parsed
        name = _keysym_name(int(key))
        if name is None:
            return None
        modifiers = (
            (_CONTROL if ctrl else 0)
            | (_SHIFT if shift else 0)
            | (_ALT if alt else 0)
            | (_SUPER if win else 0)
        )
        return self._keycode(name), modifiers

    def _keycode(self, name: str) -> int:
        keysym = self._x11.XStringToKeysym(name.encode("ascii"))
        if not keysym:
            return 0
        return int(self._x11.XKeysymToKeycode(self._display, keysym))

    def _run(self) -> None:
        self._display = self._x11.XOpenDisplay(None)
        if not self._display:
            self._close_pipe()
            return

        root = self._x11.XDefaultRootWindow(self._display)
        parsed = self._modifiers()
        if parsed is None or parsed[0] == 0:
            self._x11.XCloseDisplay(self._display)
            self._close_pipe()
            return

        keycode, modifiers = parsed
        variants = [
            modifiers,
            modifiers | _LOCK,
            modifiers | _NUM,
            modifiers | _LOCK | _NUM,
        ]
        handler = _ErrorHandler(self._on_error)
        previous = self._x11.XSetErrorHandler(ctypes.cast(handler, ctypes.c_void_p))
        try:
            self._grab_error = False
            for value in variants:
                self._x11.XGrabKey(
                    self._display,
                    keycode,
                    value,
                    root,
                    True,
                    _GRAB_MODE_ASYNC,
                    _GRAB_MODE_ASYNC,
                )
            self._x11.XSync(self._display, False)
            if self._grab_error:
                self._registered = False
                return

            self._x11.XSelectInput(self._display, root, _KEY_PRESS_MASK)
            self._x11.XSync(self._display, False)
            self._registered = True

            fd = self._x11.XConnectionNumber(self._display)
            while not self._stop.is_set():
                ready, _, _ = select.select([fd, self._pipe_r], [], [], 0.2)
                if self._pipe_r in ready:
                    break
                if fd not in ready:
                    continue
                while self._x11.XPending(self._display):
                    event = _XEvent()
                    self._x11.XNextEvent(self._display, ctypes.byref(event))
                    if event.type != _KEY_PRESS:
                        continue
                    state = event.xkey.state & (_CONTROL | _SHIFT | _ALT | _SUPER)
                    if event.xkey.keycode == keycode and state == modifiers:
                        self._emitter.activated.emit()
        finally:
            for value in variants:
                self._x11.XUngrabKey(self._display, keycode, value, root)
            self._x11.XSync(self._display, False)
            self._x11.XSetErrorHandler(previous)
            self._registered = False
            self._x11.XCloseDisplay(self._display)
            self._close_pipe()

    def _close_pipe(self) -> None:
        for fd in (self._pipe_r, self._pipe_w):
            try:
                os.close(fd)
            except OSError:
                pass
        self._pipe_r = self._pipe_w = -1
