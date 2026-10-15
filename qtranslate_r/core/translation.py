"""Запуск нескольких переводчиков и сбор результатов."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from ..domain.errors import ServiceError
from ..domain.language import AUTO, AUTO_PAIR
from ..domain.models import TranslationRequest, TranslationResult
from ..localization import tr
from ..services.base import Translator
from ..services.registry import ServiceRegistry


class TranslationService:
    def __init__(self, registry: ServiceRegistry) -> None:
        self._registry = registry

    def translate(
        self,
        text: str,
        source: str,
        target: str,
        provider_ids: list[str],
        *,
        native: str | None = None,
        second: str | None = None,
    ) -> list[TranslationResult]:
        providers = [
            service
            for service in (self._registry.get(pid) for pid in provider_ids)
            if isinstance(service, Translator)
        ]
        if not providers:
            return []

        if target == AUTO_PAIR and native and second:
            return self._auto_pair(text, providers, native, second)
        if source == AUTO:
            return self._with_detection(text, target, providers)
        return self._run_all(providers, text, source, target)

    def _auto_pair(
        self,
        text: str,
        providers: list[Translator],
        native: str,
        second: str,
    ) -> list[TranslationResult]:
        """Перевод между родным и вторым языком: направление выбирает определение."""
        auto_providers = [p for p in providers if p.supports_auto]
        fixed_providers = [p for p in providers if not p.supports_auto]

        results: dict[str, TranslationResult] = {}
        for result in self._run_all(auto_providers, text, AUTO, native):
            results[result.provider_id] = result

        detected = next((r.detected_source for r in results.values() if r.detected_source), None)

        if detected == native:
            # Родной язык — переводим на второй.
            results = {}
            for result in self._run_all(providers, text, native, second):
                result.detected_source = result.detected_source or native
                results[result.provider_id] = result
            return [results[p.id] for p in providers]

        if fixed_providers:
            if detected:
                for result in self._run_all(fixed_providers, text, detected, native):
                    result.detected_source = result.detected_source or detected
                    results[result.provider_id] = result
            else:
                message = tr("errors.source_required")
                for provider in fixed_providers:
                    results[provider.id] = TranslationResult(
                        provider_id=provider.id,
                        provider_name=provider.name,
                        error=message,
                    )

        return [results[p.id] for p in providers]

    def _with_detection(
        self,
        text: str,
        target: str,
        providers: list[Translator],
    ) -> list[TranslationResult]:
        auto_providers = [p for p in providers if p.supports_auto]
        fixed_providers = [p for p in providers if not p.supports_auto]

        results: dict[str, TranslationResult] = {}
        for result in self._run_all(auto_providers, text, AUTO, target):
            results[result.provider_id] = result

        detected = next((r.detected_source for r in results.values() if r.detected_source), None)

        if fixed_providers:
            if detected:
                for result in self._run_all(fixed_providers, text, detected, target):
                    results[result.provider_id] = result
            else:
                message = tr("errors.source_required")
                for provider in fixed_providers:
                    results[provider.id] = TranslationResult(
                        provider_id=provider.id,
                        provider_name=provider.name,
                        error=message,
                    )

        return [results[p.id] for p in providers]

    def _run_all(
        self,
        providers: list[Translator],
        text: str,
        source: str,
        target: str,
    ) -> list[TranslationResult]:
        if not providers:
            return []
        with ThreadPoolExecutor(max_workers=min(len(providers), 8)) as pool:
            return list(pool.map(lambda p: self._run_one(p, text, source, target), providers))

    @staticmethod
    def _run_one(
        provider: Translator,
        text: str,
        source: str,
        target: str,
    ) -> TranslationResult:
        started = time.perf_counter()
        try:
            provider.validate()
            result = provider.translate(TranslationRequest(text=text, source=source, target=target))
        except ServiceError as exc:
            result = TranslationResult(provider.id, provider.name, error=str(exc))
        except Exception as exc:  # noqa: BLE001 — один сервис не должен ронять остальные
            result = TranslationResult(provider.id, provider.name, error=tr("errors.internal", message=exc))
        result.elapsed_ms = int((time.perf_counter() - started) * 1000)
        return result
