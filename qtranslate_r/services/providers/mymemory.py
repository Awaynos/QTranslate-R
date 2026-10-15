"""MyMemory — бесплатный перевод без ключа."""

from __future__ import annotations

from ...domain.errors import ServiceError
from ...domain.models import TranslationRequest, TranslationResult
from ...localization import tr
from ..base import Translator
from ._http import http_get
from ._util import chunk_text

_ENDPOINT = "https://api.mymemory.translated.net/get"
_CHUNK_LIMIT = 480


class MyMemoryTranslator(Translator):
    id = "mymemory"
    name = "MyMemory"
    supports_auto = False
    max_characters = _CHUNK_LIMIT

    def __init__(self) -> None:
        self._email = ""

    def configure(self, options: dict) -> None:
        self._email = str(options.get("email", "") or "").strip()

    def translate(self, request: TranslationRequest) -> TranslationResult:
        text = request.text
        if not text.strip():
            raise ServiceError(tr("errors.empty_text"), kind="unsupported")

        parts = [
            self._translate_chunk(chunk, request.source, request.target)
            for chunk in chunk_text(text, _CHUNK_LIMIT)
        ]
        return TranslationResult(
            provider_id=self.id,
            provider_name=self.name,
            text="".join(parts).strip(),
        )

    def _translate_chunk(self, text: str, source: str, target: str) -> str:
        params = {"q": text, "langpair": f"{source}|{target}"}
        if self._email:
            params["de"] = self._email

        data = http_get(_ENDPOINT, params).json()

        status = data.get("responseStatus")
        if status not in (200, "200"):
            detail = data.get("responseDetails") or tr("errors.rejected", status=status)
            raise ServiceError(str(detail), kind="limit" if status == 429 else "error")

        translated = data.get("responseData", {}).get("translatedText")
        if not translated:
            raise ServiceError(tr("errors.empty_response"), kind="error")
        return str(translated)
