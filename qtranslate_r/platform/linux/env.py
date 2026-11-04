"""Определение окружения Linux."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass

TOOLS = (
    "wl-paste",
    "wl-copy",
    "wtype",
    "ydotool",
    "xclip",
    "xsel",
    "xdotool",
    "grim",
    "slurp",
    "spectacle",
    "gnome-screenshot",
    "maim",
    "scrot",
    "flameshot",
    "tesseract",
    "spd-say",
    "espeak-ng",
    "ffplay",
    "mpv",
    "paplay",
    "aplay",
    "hyprctl",
    "swaymsg",
)


def session_type() -> str:
    value = (os.environ.get("XDG_SESSION_TYPE") or "").strip().lower()
    if value in {"wayland", "x11"}:
        return value
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "unknown"


def desktop() -> str:
    return (os.environ.get("XDG_CURRENT_DESKTOP") or "").strip()


def tool_path(name: str) -> str | None:
    return shutil.which(name)


def available_tools(names: tuple[str, ...] = TOOLS) -> dict[str, str | None]:
    return {name: shutil.which(name) for name in names}


@dataclass(frozen=True)
class Environment:
    session: str
    desktop: str
    tools: dict[str, str | None]

    @property
    def wayland(self) -> bool:
        return self.session == "wayland"

    @property
    def x11(self) -> bool:
        return self.session == "x11"

    @property
    def hyprland(self) -> bool:
        return "hyprland" in self.desktop.lower()


def detect() -> Environment:
    return Environment(session_type(), desktop(), available_tools())
