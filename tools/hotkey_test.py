"""Проверка Linux-хоткеев без нажатия клавиш."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import Qt  # noqa: E402

from qtranslate_r.platform.linux import hotkey  # noqa: E402
from qtranslate_r.platform.linux.env import session_type  # noqa: E402
from qtranslate_r.platform.linux.x11_hotkey import X11Hotkey, _keysym_name  # noqa: E402


def main() -> int:
    if not sys.platform.startswith("linux"):
        print("SKIP: not Linux")
        return 0

    assert _keysym_name(0x51) == "q"
    assert _keysym_name(0x31) == "1"
    assert _keysym_name(int(Qt.Key.Key_Comma)) == "comma"
    assert _keysym_name(int(Qt.Key.Key_Return)) == "Return"

    instance = hotkey.create_hotkey("Ctrl+Alt+Q", 1)
    instance.start()
    instance.stop()
    print("session:", session_type())
    print("x11 available:", hotkey.available())
    print("registered:", instance.registered)

    if os.environ.get("DISPLAY"):
        direct = X11Hotkey("Ctrl+Alt+Shift+F12", 99)
        direct.start()
        time.sleep(0.5)
        print("x11 grab:", direct.registered)
        direct.stop()

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
