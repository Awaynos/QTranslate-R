"""Свой CSV-словарь: глоссарий, аббревиатуры, таблица кодов."""

from __future__ import annotations

import csv
from pathlib import Path

from ...domain.errors import ServiceError
from ...domain.models import DictionaryEntry
from ...localization import tr
from ..base import Dictionary

_ENCODINGS = ("utf-8-sig", "utf-8", "cp1251")
_MAX_DEFINITIONS = 12


class CsvDictionary(Dictionary):
    id = "csv"

    @property
    def name(self) -> str:
        return tr("service.csv")

    def __init__(self) -> None:
        self._path = ""
        self._term_column = 0
        self._definition_column = 1

    def configure(self, options: dict) -> None:
        self._path = str(options.get("path", "") or "").strip()
        self._term_column = int(options.get("term_column", 0) or 0)
        self._definition_column = int(options.get("definition_column", 1) or 1)

    def lookup(self, word: str, language: str, target_language: str) -> list[DictionaryEntry]:
        word = word.strip()
        if not word:
            raise ServiceError(tr("errors.empty_text"), kind="unsupported")
        if not self._path:
            raise ServiceError(tr("errors.csv_not_set"), kind="config")

        path = Path(self._path)
        if not path.is_file():
            raise ServiceError(tr("errors.csv_not_found"), kind="config")

        rows = self._read_rows(path)
        needle = word.casefold()
        definitions = [
            row[self._definition_column].strip()
            for row in rows
            if len(row) > self._definition_column
            and len(row) > self._term_column
            and row[self._term_column].strip().casefold() == needle
            and row[self._definition_column].strip()
        ]

        if not definitions:
            return []
        return [
            DictionaryEntry(
                word=word,
                source="CSV",
                language=language,
                definitions=definitions[:_MAX_DEFINITIONS],
            )
        ]

    @staticmethod
    def _read_rows(path: Path) -> list[list[str]]:
        for encoding in _ENCODINGS:
            try:
                with path.open("r", encoding=encoding, newline="") as file:
                    return [row for row in csv.reader(file)]
            except UnicodeDecodeError:
                continue
            except OSError as exc:
                raise ServiceError(tr("errors.csv_read"), kind="config") from exc
        raise ServiceError(tr("errors.csv_encoding"), kind="config")
