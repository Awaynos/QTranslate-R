"""LibreTranslate — открытый переводчик, можно поднять свой сервер."""

from __future__ import annotations

from ...domain.errors import ServiceError
from ...domain.models import TranslationRequest, TranslationResult
from ...localization import tr
from ..base import Translator
from ._http import http_post
from ._util import chunk_text

_DEFAULT_URL = "https://libretranslate.com"
_CHUNK_LIMIT = 2000


class LibreTranslateTranslator(Translator):
    id = "libretranslate"
    name = "LibreTranslate"
    supports_auto = True
    max_characters = _CHUNK_LIMIT

    def __init__(self) -> None:
        self._base_url = _DEFAULT_URL
        self._api_key = ""

    def configure(self, options: dict) -> None:
        self._base_url = (str(options.get("url", "") or "").strip() or _DEFAULT_URL).rstrip("/")
        self._api_key = str(options.get("api_key", "") or "").strip()

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
        body = {"q": text, "source": source, "target": target, "format": "text"}
        if self._api_key:
            body["api_key"] = self._api_key

        data = http_post(f"{self._base_url}/translate", body).json()

        if "error" in data:
            raise ServiceError(str(data["error"]), kind="error")

        translated = data.get("translatedText")
        if translated is None:
            raise ServiceError(tr("errors.empty_response"), kind="error")

        detected_block = data.get("detectedLanguage")
        detected = detected_block.get("language") if isinstance(detected_block, dict) else None
        return str(translated), detected
