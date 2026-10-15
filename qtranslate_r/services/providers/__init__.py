"""Встроенные сервисы."""

from .csv_dict import CsvDictionary
from .google import GoogleTranslator
from .google_tts import GoogleTTS
from .libretranslate import LibreTranslateTranslator
from .mymemory import MyMemoryTranslator
from .reverso import ReversoTranslator
from .system_tts import SystemTTS
from .wiktionary import WiktionaryDictionary
from .yandex import YandexTranslator

__all__ = [
    "GoogleTranslator",
    "MyMemoryTranslator",
    "LibreTranslateTranslator",
    "ReversoTranslator",
    "YandexTranslator",
    "SystemTTS",
    "GoogleTTS",
    "WiktionaryDictionary",
    "CsvDictionary",
]
