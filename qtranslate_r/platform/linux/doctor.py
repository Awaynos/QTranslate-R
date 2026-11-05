"""Диагностика Linux-окружения."""

from __future__ import annotations

import platform as system_platform
import sys

from ...config.paths import cache_dir, config_dir, data_dir
from ..capabilities import capabilities
from .env import detect


def report() -> list[str]:
    env = detect()
    caps = capabilities()
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
        "features:",
        f"  global_hotkeys: {'yes' if caps.global_hotkeys else 'no'}",
        f"  hotkey_backend: {'x11' if caps.global_hotkeys else 'desktop binds'}",
        f"  selection_capture: {'yes' if caps.selection_capture else 'no'}",
        f"  replace_selection: {'yes' if caps.replace_selection else 'no'}",
        f"  screen_capture: {'yes' if caps.screen_capture else 'no'}",
        f"  system_tts: {'yes' if caps.system_tts else 'no'}",
        f"  audio_playback: {'yes' if caps.audio_playback else 'no'}",
        f"  spellcheck: {'yes' if caps.spellcheck else 'no'}",
        f"  tray: {'yes' if caps.tray else 'no'}",
        "",
        "tools:",
    ]
    for name, path in env.tools.items():
        lines.append(f"  {name}: {path or 'not found'}")
    return lines
