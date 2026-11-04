"""Проверка выбора и захвата области экрана."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QRect  # noqa: E402

from qtranslate_r.platform.linux import screen  # noqa: E402


def main() -> int:
    assert screen.parse_geometry("10,20 300x200") == (10, 20, 300, 200)
    assert screen.parse_geometry("-5,-10 80x40") == (-5, -10, 80, 40)
    assert screen.parse_geometry("bad") is None
    print("geometry: OK")

    available = screen.has_region_selection()
    print("region selection:", "yes" if available else "no")
    if not available:
        print("SKIP: slurp is not available")
        return 0

    image = screen.capture_region(None, QRect(0, 0, 200, 100))
    assert not image.isNull()
    print("capture:", image.width(), "x", image.height())
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
