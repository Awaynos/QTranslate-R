"""Проверка позиции курсора на Linux."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import Qt  # noqa: E402

from qtranslate_r.platform import window as platform_window  # noqa: E402
from qtranslate_r.platform.window import cursor_position  # noqa: E402


def check_system_move() -> None:
    from qtranslate_r.platform.linux import window as linux_window

    class Handle:
        def startSystemMove(self) -> bool:
            return True

        def startSystemResize(self, edges) -> bool:
            return edges == Qt.Edge.LeftEdge

    class Widget:
        def windowHandle(self):
            return Handle()

    class WaylandApp:
        @staticmethod
        def platformName() -> str:
            return "wayland"

    class X11App:
        @staticmethod
        def platformName() -> str:
            return "xcb"

    original = linux_window.QGuiApplication
    try:
        linux_window.QGuiApplication = WaylandApp
        assert platform_window.start_system_move(Widget())
        assert platform_window.start_system_resize(Widget(), Qt.Edge.LeftEdge)
        assert not platform_window.start_system_resize(Widget(), Qt.Edge.RightEdge)
        linux_window.QGuiApplication = X11App
        assert not platform_window.start_system_move(Widget())
    finally:
        linux_window.QGuiApplication = original
    print("system move: OK")
    print("system resize: OK")


def main() -> int:
    if not sys.platform.startswith("linux"):
        print("SKIP: not Linux")
        return 0

    position = cursor_position()
    print("cursor:", position)
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        assert position is not None
    if position is not None:
        assert len(position) == 2
        assert all(isinstance(value, int) for value in position)
    check_system_move()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
