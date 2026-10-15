"""Словарь Wiktionary через официальный MediaWiki REST API."""

from __future__ import annotations

import html
import re

from ...domain.errors import ServiceError
from ...domain.models import DictionaryEntry
from ...localization import tr
from ..base import Dictionary
from ._http import http_get

_HOSTS = {
    "en", "de", "fr", "es", "it", "nl", "pl", "pt", "sv", "fi", "da", "no",
    "cs", "hu", "tr", "el", "ja", "ko", "zh", "vi", "id", "ar", "he",
}

_TAG = re.compile(r"<[^>]+>")
_MAX_DEFINITIONS = 8


def _clean(text: str) -> str:
    return html.unescape(_TAG.sub("", text)).strip()


class WiktionaryDictionary(Dictionary):
    id = "wiktionary"
    name = "Wiktionary"

    def lookup(self, word: str, language: str, target_language: str) -> list[DictionaryEntry]:
        word = word.strip()
        if not word:
            raise ServiceError(tr("errors.empty_text"), kind="unsupported")

        base = (language or "en").split("-")[0]
        hosts = [base, "en"] if base in _HOSTS and base != "en" else ["en"]

        data = None
        last_error: ServiceError | None = None
        for host in hosts:
            try:
                data = http_get(
                    f"https://{host}.wiktionary.org/api/rest_v1/page/definition/{word}",
                    {},
                ).json()
                break
            except ServiceError as exc:
                last_error = exc
            except ValueError as exc:
                last_error = ServiceError(tr("errors.bad_response"), kind="error")
                _ = exc

        if data is None:
            raise last_error or ServiceError(tr("errors.network"), kind="network")

        return self._parse(word, language, data)

    @staticmethod
    def _parse(word: str, language: str, data: object) -> list[DictionaryEntry]:
        if not isinstance(data, dict) or not data:
            return []

        base = (language or "en").split("-")[0]
        blocks = data.get(base) or data.get(language)
        if not blocks:
            blocks = next(iter(data.values()))

        entries: list[DictionaryEntry] = []
        for block in blocks if isinstance(blocks, list) else []:
            definitions = [
                _clean(item.get("definition", ""))
                for item in block.get("definitions", [])
                if isinstance(item, dict)
            ]
            definitions = [d for d in definitions if d][:_MAX_DEFINITIONS]
            if definitions:
                entries.append(
                    DictionaryEntry(
                        word=word,
                        source="Wiktionary",
                        language=language,
                        part_of_speech=str(block.get("partOfSpeech", "")),
                        definitions=definitions,
                    )
                )
        return entries
