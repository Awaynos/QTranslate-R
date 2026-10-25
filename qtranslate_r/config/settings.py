"""Настройки пользователя."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from ..domain.language import AUTO


@dataclass
class Settings:
    theme: str = "metal"
    interface_language: str = ""
    primary_provider: str = ""
    source_language: str = AUTO
    target_language: str = "ru"
    enabled_providers: list[str] = field(default_factory=lambda: ["google", "mymemory"])
    translate_on_type: bool = False
    font_size: int = 10
    window_geometry: str = ""
    quick_translate_enabled: bool = True
    native_language: str = ""
    second_language: str = ""
    tts_provider: str = "system-tts"

    dictionary_provider: str = "wiktionary"
    csv_path: str = ""
    csv_term_column: int = 0
    csv_definition_column: int = 1

    hotkeys: dict = field(default_factory=dict)
    hotkey_scopes: dict = field(default_factory=dict)

    splitter_sizes: list = field(default_factory=list)
    panel_index: int = 0

    mymemory_email: str = ""
    libretranslate_url: str = "https://libretranslate.com"
    libretranslate_api_key: str = ""
    deepl_api_url: str = "https://api-free.deepl.com"
    deepl_api_key: str = ""

    max_chars: int = 5000

    @classmethod
    def load(cls, path: Path) -> "Settings":
        settings = cls()
        if not path.is_file():
            settings.apply_system_languages()
            return settings
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            settings.apply_system_languages()
            return settings
        if not isinstance(raw, dict):
            settings.apply_system_languages()
            return settings
        known = {f.name for f in fields(cls)}
        for key, value in raw.items():
            if key in known:
                setattr(settings, key, value)
        if settings.theme == "dark":
            settings.theme = "metal"
        if not isinstance(settings.hotkeys, dict):
            settings.hotkeys = {}
        if not isinstance(settings.hotkey_scopes, dict):
            settings.hotkey_scopes = {}
        if not isinstance(settings.splitter_sizes, list):
            settings.splitter_sizes = []
        if not settings.native_language or not settings.second_language:
            settings.apply_system_languages(only_missing=True)
        return settings

    def apply_system_languages(self, only_missing: bool = False) -> None:
        """Родной и второй язык — по системе (при первом запуске)."""
        from ..localization import system_language

        native = system_language()
        if not only_missing or not self.native_language:
            self.native_language = native
        if not only_missing or not self.second_language:
            self.second_language = "en" if self.native_language != "en" else "ru"

    def save(self, path: Path) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass
