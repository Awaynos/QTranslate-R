"""Yandex Translate через мобильный эндпоинт (без ключа)."""

from __future__ import annotations

import threading
import uuid

from ...domain.errors import ServiceError
from ...domain.models import TranslationRequest, TranslationResult
from ...localization import tr
from ..base import Translator
from ._http import http_get, http_post_form

_BASE = "https://translate.yandex.net/api/v1/tr.json"


class YandexTranslator(Translator):
    id = "yandex"
    name = "Yandex"
    supports_auto = False

    def __init__(self) -> None:
        self._sid: str | None = None
        self._lock = threading.Lock()

    def translate(self, request: TranslationRequest) -> TranslationResult:
        text = request.text
        if not text.strip():
            raise ServiceError(tr("errors.empty_text"), kind="unsupported")

        try:
            translated = self._translate(text, request.source, request.target)
        except ServiceError as exc:
            # Сессия могла протухнуть — пробуем ещё раз с новой.
            if exc.kind in ("auth", "error"):
                with self._lock:
                    self._sid = None
                translated = self._translate(text, request.source, request.target)
            else:
                raise

        return TranslationResult(
            provider_id=self.id,
            provider_name=self.name,
            text=translated,
        )

    def _translate(self, text: str, source: str, target: str) -> str:
        sid = self._session()
        response = http_post_form(
            f"{_BASE}/translate",
            {"text": text, "lang": f"{source}-{target}"},
            params={"id": f"{sid}-0-0", "srv": "android", "format": "text"},
        )
        data = response.json()

        if data.get("code") != 200:
            message = data.get("message") or tr("errors.rejected", status=data.get("code"))
            raise ServiceError(str(message), kind="error")

        parts = data.get("text") or []
        if not parts:
            raise ServiceError(tr("errors.empty_response"), kind="error")
        return " ".join(str(part) for part in parts)

    def _session(self) -> str:
        with self._lock:
            if self._sid is None:
                sid = uuid.uuid4().hex
                http_get(f"{_BASE}/getLangs", {"sid": sid, "ui": "ru", "srv": "android"})
                self._sid = sid
            return self._sid
