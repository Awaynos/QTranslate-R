"""Проверка позиции курсора на Linux."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qtranslate_r.platform.window import cursor_position  # noqa: E402


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
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
