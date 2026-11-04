"""Диагностика macOS."""

from __future__ import annotations

import platform as system_platform
import sys


def report() -> list[str]:
    release = system_platform.mac_ver()[0] or "unknown"
    return [
        "QTranslate Remake: platform diagnostics",
        f"system: macOS {release} ({system_platform.machine()})",
        f"python: {sys.version.split()[0]}",
    ]
