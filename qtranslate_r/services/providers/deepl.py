"""DeepL: официальный API по ключу или бесплатный веб-эндпоинт."""

from __future__ import annotations

import requests

from ...domain.errors import ServiceError
from ...domain.language import AUTO
from ...domain.models import TranslationRequest, TranslationResult
from ...localization import tr
from ..base import Translator
from ._util import chunk_text

_WEB_URL = "https://oneshot-free.www.deepl.com/v1/translate"
_DEFAULT_API_URL = "https://api-free.deepl.com"
_CHUNK_LIMIT = 5000
_TIMEOUT = 20
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

_WEB_TARGET = {"zh": "zh", "zh-TW": "zh", "pt": "pt"}
_API_TARGET = {"zh": "ZH-HANS", "zh-TW": "ZH-HANT", "pt": "PT-PT", "en": "EN-US"}


class DeepLTranslator(Translator):
    id = "deepl"
    name = "DeepL"
    supports_auto = True
    max_characters = _CHUNK_LIMIT

    def __init__(self) -> None:
        self._api_key = ""
        self._api_url = _DEFAULT_API_URL
        self._session = requests.Session()
        self._session.headers.update(
            {"User-Agent": _USER_AGENT, "Accept": "application/json"}
        )

    def configure(self, options: dict) -> None:
        self._api_key = str(options.get("api_key", "") or "").strip()
        self._api_url = (
            str(options.get("api_url", "") or "").strip().rstrip("/") or _DEFAULT_API_URL
        )

    def translate(self, request: TranslationRequest) -> TranslationResult:
        text = request.text
        if not text.strip():
            raise ServiceError(tr("errors.empty_text"), kind="unsupported")

        parts: list[str] = []
        detected: str | None = None
        for chunk in chunk_text(text, _CHUNK_LIMIT):
            translated, chunk_detected = self._translate_chunk(
                chunk, request.source, request.target
            )
            parts.append(translated)
            detected = detected or chunk_detected

        return TranslationResult(
            provider_id=self.id,
            provider_name=self.name,
            text="".join(parts),
            detected_source=detected,
        )

    def _translate_chunk(
        self, text: str, source: str, target: str
    ) -> tuple[str, str | None]:
        if self._api_key:
            return self._official(text, source, target)
        return self._web(text, source, target)

    def _official(self, text: str, source: str, target: str) -> tuple[str, str | None]:
        body = {"text": [text], "target_lang": _API_TARGET.get(target, target.upper())}
        if source != AUTO:
            body["source_lang"] = "PT" if source == "pt" else ("ZH" if source.startswith("zh") else source.upper())

        response = self._post(
            f"{self._api_url}/v2/translate",
            body,
            headers={"Authorization": f"DeepL-Auth-Key {self._api_key}"},
        )
        return self._parse(response)

    def _web(self, text: str, source: str, target: str) -> tuple[str, str | None]:
        body = {"text": [text], "target_lang": _WEB_TARGET.get(target, target.lower())}
        if source != AUTO:
            body["source_lang"] = "pt" if source == "pt" else source
        response = self._post(
            _WEB_URL,
            body,
            headers={"Authorization": "None", "Origin": "https://www.deepl.com", "Referer": "https://www.deepl.com/"},
        )
        return self._parse(response)

    def _post(self, url: str, body: dict, headers: dict) -> dict:
        try:
            response = self._session.post(url, json=body, headers=headers, timeout=_TIMEOUT)
        except requests.Timeout as exc:
            raise ServiceError(tr("errors.timeout"), kind="network") from exc
        except requests.RequestException as exc:
            raise ServiceError(tr("errors.network"), kind="network") from exc

        if response.status_code == 429:
            raise ServiceError(tr("errors.rate_limit"), kind="limit")
        if response.status_code in (401, 403):
            raise ServiceError(tr("errors.auth"), kind="auth")
        if response.status_code == 456:
            raise ServiceError(tr("errors.rate_limit"), kind="limit")
        if response.status_code >= 500:
            raise ServiceError(tr("errors.unavailable", status=response.status_code), kind="network")
        if response.status_code >= 400:
            raise ServiceError(tr("errors.rejected", status=response.status_code), kind="error")

        try:
            data = response.json()
        except ValueError as exc:
            raise ServiceError(tr("errors.bad_response"), kind="error") from exc
        if not isinstance(data, dict):
            raise ServiceError(tr("errors.bad_response"), kind="error")
        return data

    @staticmethod
    def _parse(data: dict) -> tuple[str, str | None]:
        translations = data.get("translations")
        if not isinstance(translations, list) or not translations:
            message = data.get("message") or data.get("error")
            if message:
                raise ServiceError(str(message), kind="error")
            raise ServiceError(tr("errors.empty_response"), kind="error")

        first = translations[0]
        if not isinstance(first, dict):
            raise ServiceError(tr("errors.bad_response"), kind="error")
        text = first.get("text")
        if not isinstance(text, str) or not text:
            raise ServiceError(tr("errors.empty_response"), kind="error")
        detected = first.get("detected_source_language")
        return text, detected.lower() if isinstance(detected, str) and detected else None
