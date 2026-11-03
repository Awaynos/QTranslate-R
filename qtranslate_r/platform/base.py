"""Общие типы платформенного слоя."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal


class PlatformUnavailable(Exception):
    """Системная возможность недоступна в текущем окружении."""

    def __init__(self, message: str = "") -> None:
        super().__init__(message)
        self.message = message


class OcrError(Exception):
    def __init__(self, message: str, *, kind: str = "error") -> None:
        super().__init__(message)
        self.kind = kind


class AudioError(Exception):
    pass


@dataclass(frozen=True)
class Capabilities:
    global_hotkeys: bool = False
    selection_capture: bool = False
    replace_selection: bool = False
    screen_capture: bool = False
    system_tts: bool = False
    audio_playback: bool = False
    spellcheck: bool = False
    tray: bool = False


class NullHotkey(QObject):
    """Заглушка глобального хоткея для платформ без поддержки."""

    activated = Signal()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    @property
    def registered(self) -> bool:
        return False
