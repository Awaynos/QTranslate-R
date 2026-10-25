"""Сборка сервисов и применение настроек."""

from __future__ import annotations

from ..config.settings import Settings
from ..services.base import Dictionary, ServiceRole, TextToSpeech
from ..services.providers import (
    BingTranslator,
    CsvDictionary,
    DeepLTranslator,
    GoogleTTS,
    GoogleTranslator,
    LibreTranslateTranslator,
    MyMemoryTranslator,
    ReversoTranslator,
    SystemTTS,
    WiktionaryDictionary,
    YandexTranslator,
)
from ..services.registry import ServiceRegistry


def build_registry() -> ServiceRegistry:
    registry = ServiceRegistry()
    registry.register(GoogleTranslator())
    registry.register(BingTranslator())
    registry.register(DeepLTranslator())
    registry.register(MyMemoryTranslator())
    registry.register(LibreTranslateTranslator())
    registry.register(YandexTranslator())
    registry.register(ReversoTranslator())
    registry.register(SystemTTS())
    registry.register(GoogleTTS())
    registry.register(WiktionaryDictionary())
    registry.register(CsvDictionary())
    return registry


def configure_registry(registry: ServiceRegistry, settings: Settings) -> None:
    mymemory = registry.get("mymemory")
    if mymemory is not None:
        mymemory.configure({"email": settings.mymemory_email})

    libretranslate = registry.get("libretranslate")
    if libretranslate is not None:
        libretranslate.configure(
            {
                "url": settings.libretranslate_url,
                "api_key": settings.libretranslate_api_key,
            }
        )

    csv_dict = registry.get("csv")
    if csv_dict is not None:
        csv_dict.configure(
            {
                "path": settings.csv_path,
                "term_column": settings.csv_term_column,
                "definition_column": settings.csv_definition_column,
            }
        )

    deepl = registry.get("deepl")
    if deepl is not None:
        deepl.configure(
            {
                "api_key": settings.deepl_api_key,
                "api_url": settings.deepl_api_url,
            }
        )


def translator_choices(registry: ServiceRegistry) -> list[tuple[str, str]]:
    return [(service.id, service.name) for service in registry.translators()]


def tts_choices(registry: ServiceRegistry) -> list[tuple[str, str]]:
    return [(service.id, service.name) for service in registry.by_role(ServiceRole.TTS)]


def tts_service(registry: ServiceRegistry, preferred_id: str) -> TextToSpeech | None:
    service = registry.get(preferred_id)
    if isinstance(service, TextToSpeech):
        return service
    for candidate in registry.by_role(ServiceRole.TTS):
        if isinstance(candidate, TextToSpeech):
            return candidate
    return None


def dictionary_choices(registry: ServiceRegistry) -> list[tuple[str, str]]:
    return [(service.id, service.name) for service in registry.by_role(ServiceRole.DICTIONARY)]


def dictionary_service(registry: ServiceRegistry, preferred_id: str) -> Dictionary | None:
    service = registry.get(preferred_id)
    if isinstance(service, Dictionary):
        return service
    for candidate in registry.by_role(ServiceRole.DICTIONARY):
        if isinstance(candidate, Dictionary):
            return candidate
    return None
