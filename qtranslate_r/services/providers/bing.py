"""Bing Translator через публичный эндпоинт со страницы переводчика."""

from __future__ import annotations

import re
import threading
import time

import requests

from ...domain.errors import ServiceError
from ...domain.models import TranslationRequest, TranslationResult
from ...localization import tr
from ..base import Translator
from ._util import chunk_text

_PAGE = "https://www.bing.com/translator"
_ENDPOINT = "https://www.bing.com/ttranslatev3"
_CHUNK_LIMIT = 1000
_TIMEOUT = 20
_AUTH_TTL = 3600
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

_TARGET = {"zh": "zh-Hans", "zh-TW": "zh-Hant", "no": "nb"}


class BingTranslator(Translator):
    id = "bing"
    name = "Bing"
    supports_auto = True
    max_characters = _CHUNK_LIMIT

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": _USER_AGENT,
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "application/json",
            }
        )
        self._ig = ""
        self._iid = ""
        self._key = ""
        self._token = ""
        self._fetched_at = 0.0

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
        with self._lock:
            self._ensure_auth()
            response = self._request(text, source, target)
            if response.status_code == 401:
                self._refresh_auth()
                response = self._request(text, source, target)
            return self._parse(response)

    def _request(self, text: str, source: str, target: str) -> requests.Response:
        data = {
            "text": text,
            "fromLang": "auto-detect" if source == "auto" else _TARGET.get(source, source),
            "to": _TARGET.get(target, target),
            "token": self._token,
            "key": self._key,
            "isAuthv2": "true",
            "tryFetchingGenderDebiasedTranslations": "true",
        }
        try:
            return self._session.post(
                _ENDPOINT,
                params={"isVertical": 1, "IG": self._ig, "IID": self._iid},
                data=data,
                headers={
                    "Referer": _PAGE,
                    "Origin": "https://www.bing.com",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=_TIMEOUT,
            )
        except requests.Timeout as exc:
            raise ServiceError(tr("errors.timeout"), kind="network") from exc
        except requests.RequestException as exc:
            raise ServiceError(tr("errors.network"), kind="network") from exc

    def _ensure_auth(self) -> None:
        if self._token and time.monotonic() - self._fetched_at < _AUTH_TTL:
            return
        self._refresh_auth()

    def _refresh_auth(self) -> None:
        try:
            page = self._session.get(_PAGE, timeout=_TIMEOUT)
        except requests.Timeout as exc:
            raise ServiceError(tr("errors.timeout"), kind="network") from exc
        except requests.RequestException as exc:
            raise ServiceError(tr("errors.network"), kind="network") from exc

        if page.status_code >= 400:
            raise ServiceError(tr("errors.rejected", status=page.status_code), kind="error")

        html = page.text
        ig = re.search(r'IG:"([^"]+)"', html)
        iid = re.search(r'data-iid="([^"]+)"', html)
        helper = re.search(
            r'params_AbusePreventionHelper = \[(\d+),"([^"]+)",\d+\]', html
        )
        muid = re.search(r'"muid"\s*:\s*"([^"]+)"', html)
        if not (ig and helper):
            raise ServiceError(tr("errors.bad_response"), kind="error")

        self._ig = ig.group(1)
        self._iid = iid.group(1) if iid else "translator.5023.1"
        self._key = helper.group(1)
        self._token = helper.group(2)
        self._fetched_at = time.monotonic()
        if muid:
            self._session.cookies.set("MUID", muid.group(1), domain=".bing.com")

    @staticmethod
    def _parse(response: requests.Response) -> tuple[str, str | None]:
        if response.status_code == 429:
            raise ServiceError(tr("errors.rate_limit"), kind="limit")
        if response.status_code in (401, 403):
            raise ServiceError(tr("errors.auth"), kind="auth")
        if response.status_code >= 500:
            raise ServiceError(tr("errors.unavailable", status=response.status_code), kind="network")
        if response.status_code >= 400:
            raise ServiceError(tr("errors.rejected", status=response.status_code), kind="error")

        try:
            data = response.json()
        except ValueError as exc:
            raise ServiceError(tr("errors.bad_response"), kind="error") from exc

        if isinstance(data, dict) and data.get("ShowCaptcha"):
            raise ServiceError(tr("errors.auth"), kind="auth")
        if not isinstance(data, list):
            raise ServiceError(tr("errors.bad_response"), kind="error")

        for item in data:
            if not isinstance(item, dict):
                continue
            translations = item.get("translations")
            detected = item.get("detectedLanguage")
            if not isinstance(translations, list) or not translations:
                continue
            text = "".join(
                part.get("text", "")
                for part in translations
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            )
            if not text:
                continue
            code = detected.get("language") if isinstance(detected, dict) else None
            return text, code if isinstance(code, str) else None

        raise ServiceError(tr("errors.empty_response"), kind="error")
