"""Reverso Context (без ключа)."""

from __future__ import annotations

from ...domain.errors import ServiceError
from ...domain.models import TranslationRequest, TranslationResult
from ...localization import tr
from ..base import Translator
from ._http import http_post

_ENDPOINT = "https://api.reverso.net/translate/v1/translation"

# ISO 639-1 -> код Reverso.
_CODES = {
    "en": "eng", "ru": "rus", "uk": "ukr", "de": "deu", "fr": "fra", "es": "spa",
    "it": "ita", "pt": "por", "nl": "nld", "pl": "pol", "tr": "tur", "ar": "ara",
    "he": "heb", "ja": "jpn", "ko": "kor", "zh": "chi", "cs": "ces", "da": "dan",
    "el": "ell", "fi": "fin", "hu": "hun", "no": "nor", "ro": "ron", "sk": "slk",
    "sv": "swe", "th": "tha", "vi": "vie", "id": "ind", "bg": "bul", "hr": "hrv",
    "sr": "srp", "sl": "slv", "et": "est", "lv": "lav", "lt": "lit",
}


class ReversoTranslator(Translator):
    id = "reverso"
    name = "Reverso"
    supports_auto = False

    def translate(self, request: TranslationRequest) -> TranslationResult:
        text = request.text
        if not text.strip():
            raise ServiceError(tr("errors.empty_text"), kind="unsupported")

        source = _CODES.get(request.source)
        target = _CODES.get(request.target)
        if not source or not target:
            raise ServiceError(tr("errors.reverso_pair"), kind="unsupported")

        body = {
            "format": "text",
            "from": source,
            "to": target,
            "input": text,
            "options": {
                "contextResults": False,
                "languageDetection": False,
                "sentenceSplitter": True,
                "origin": "translation.web",
                "system": "Chrome",
            },
        }
        data = http_post(_ENDPOINT, body).json()

        if data.get("error"):
            raise ServiceError(str(data["error"]), kind="error")

        parts = data.get("translation") or []
        if not parts:
            raise ServiceError(tr("errors.empty_response"), kind="error")
        return TranslationResult(
            provider_id=self.id,
            provider_name=self.name,
            text=" ".join(str(part) for part in parts),
        )
