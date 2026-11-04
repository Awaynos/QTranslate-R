"""Диагностика Windows."""

from __future__ import annotations

import platform as system_platform
import sys


def report() -> list[str]:
    version = sys.getwindowsversion()
    return [
        "QTranslate Remake: platform diagnostics",
        f"system: Windows {version.major}.{version.minor} build {version.build}",
        f"architecture: {system_platform.machine()}",
        f"python: {sys.version.split()[0]}",
    ]
