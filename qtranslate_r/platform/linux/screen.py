"""Захват области экрана в Linux."""

from __future__ import annotations

import re
import subprocess

from PySide6.QtGui import QImage

from .env import session_type, tool_path

_GEOMETRY = re.compile(r"^\s*(-?\d+),(-?\d+)\s+(\d+)x(\d+)\s*$")
_CAPTURE_TIMEOUT = 15
_SELECT_TIMEOUT = 120


def _run(args: list[str], timeout: int) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(args, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None


def parse_geometry(text: str) -> tuple[int, int, int, int] | None:
    match = _GEOMETRY.match(text)
    if match is None:
        return None
    return tuple(int(value) for value in match.groups())


def has_region_selection() -> bool:
    if not tool_path("slurp"):
        return False
    if session_type() == "x11":
        return True
    return bool(tool_path("grim"))


def select_region() -> tuple[int, int, int, int] | None:
    if not has_region_selection():
        return None
    result = _run(["slurp"], _SELECT_TIMEOUT)
    if result is None or result.returncode != 0:
        return None
    return parse_geometry(result.stdout.decode("utf-8", "replace"))


def capture_region(screen, rect) -> QImage:
    if session_type() != "x11" and tool_path("grim"):
        geometry = f"{rect.x()},{rect.y()} {rect.width()}x{rect.height()}"
        result = _run(["grim", "-g", geometry, "-"], _CAPTURE_TIMEOUT)
        if result is not None and result.returncode == 0 and result.stdout:
            image = QImage.fromData(result.stdout, "PNG")
            if not image.isNull():
                return image

    if screen is not None:
        geometry = screen.geometry()
        image = screen.grabWindow(0).toImage()
        if not image.isNull():
            scale_x = image.width() / max(1, geometry.width())
            scale_y = image.height() / max(1, geometry.height())
            x = round((rect.x() - geometry.x()) * scale_x)
            y = round((rect.y() - geometry.y()) * scale_y)
            width = round(rect.width() * scale_x)
            height = round(rect.height() * scale_y)
            return image.copy(x, y, max(1, width), max(1, height))

    return QImage()
