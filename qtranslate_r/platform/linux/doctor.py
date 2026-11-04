"""Диагностика Linux-окружения."""

from __future__ import annotations

import platform as system_platform
import sys

from ...config.paths import cache_dir, config_dir, data_dir
from .env import detect


def report() -> list[str]:
    env = detect()
    lines = [
        "QTranslate Remake: platform diagnostics",
        f"system: Linux ({system_platform.machine()})",
        f"python: {sys.version.split()[0]}",
        f"session: {env.session}",
        f"desktop: {env.desktop or 'unknown'}",
        f"hyprland: {'yes' if env.hyprland else 'no'}",
        "",
        "paths:",
        f"  data: {data_dir()}",
        f"  config: {config_dir()}",
        f"  cache: {cache_dir()}",
        "",
        "tools:",
    ]
    for name, path in env.tools.items():
        lines.append(f"  {name}: {path or 'not found'}")
    return lines
