"""Google Translate через публичные эндпоинты (без ключа)."""

from __future__ import annotations

from ...domain.errors import ServiceError
from ...domain.models import TranslationRequest, TranslationResult
from ...localization import tr
from ..base import Translator
from ._http import http_get
from ._util import chunk_text

_ENDPOINTS: list[tuple[str, dict]] = [
    ("https://clients5.google.com/translate_a/t", {"client": "dict-chrome-ex"}),
    ("https://translate.googleapis.com/translate_a/single", {"client": "gtx", "dt": "t"}),
]
_CHUNK_LIMIT = 4000


class GoogleTranslator(Translator):
    id = "google"
    name = "Google"
    supports_auto = True
    max_characters = _CHUNK_LIMIT

    def translate(self, request: TranslationRequest) -> TranslationResult:
        text = request.text
        if not text.strip():
            raise ServiceError(tr("errors.empty_text"), kind="unsupported")

        parts: list[str] = []
        detected: str | None = None
        for chunk in chunk_text(text, _CHUNK_LIMIT):
            translated, chunk_detected = self._translate_chunk(chunk, request.source, request.target)
            parts.append(translated)
            detected = detected or chunk_detected

        return TranslationResult(
            provider_id=self.id,
            provider_name=self.name,
            text="".join(parts),
            detected_source=detected,
        )

    def _translate_chunk(self, text: str, source: str, target: str) -> tuple[str, str | None]:
        last_error: ServiceError | None = None
        for url, extra in _ENDPOINTS:
            params = {"sl": source, "tl": target, "q": text, **extra}
            try:
                return self._parse(http_get(url, params).json())
            except ServiceError as exc:
                last_error = exc
            except ValueError:
                last_error = ServiceError(tr("errors.bad_response"), kind="error")
        raise last_error or ServiceError(tr("errors.network"), kind="network")

    @staticmethod
    def _parse(data: object) -> tuple[str, str | None]:
        if not isinstance(data, list) or not data:
            raise ServiceError(tr("errors.bad_response"), kind="error")

        first = data[0]

        # gtx: [[[текст, оригинал, ...], ...], null, "en", ...]
        if isinstance(first, list) and first and isinstance(first[0], list):
            text = "".join(
                segment[0]
                for segment in first
                if isinstance(segment, list) and segment and isinstance(segment[0], str)
            )
            detected = data[2] if len(data) > 2 and isinstance(data[2], str) else None
            return text, detected

        # dict-chrome-ex: [["текст", "en"]]
        if isinstance(first, list) and first and isinstance(first[0], str):
            text = "".join(
                segment[0]
                for segment in data
                if isinstance(segment, list) and segment and isinstance(segment[0], str)
            )
            detected = first[1] if len(first) > 1 and isinstance(first[1], str) else None
            return text, detected

        # ["текст", "en"]
        if isinstance(first, str):
            detected = data[1] if len(data) > 1 and isinstance(data[1], str) else None
            return first, detected

        raise ServiceError(tr("errors.bad_response"), kind="error")
