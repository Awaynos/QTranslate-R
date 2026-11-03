"""Платформенные интеграции."""

from __future__ import annotations

from . import app, audio, ocr, screen, selection, speech, spellcheck, window
from .base import Capabilities, OcrError, PlatformUnavailable
from .capabilities import capabilities
from .hotkey import GlobalHotkey, create_hotkey

__all__ = [
    "Capabilities",
    "GlobalHotkey",
    "OcrError",
    "PlatformUnavailable",
    "app",
    "audio",
    "capabilities",
    "create_hotkey",
    "ocr",
    "screen",
    "selection",
    "speech",
    "spellcheck",
    "window",
]
