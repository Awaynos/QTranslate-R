"""Заглушка проверки орфографии."""

from __future__ import annotations


class SpellChecker:
    def supported(self, code: str) -> bool:
        return False

    def is_misspelled(self, word: str, code: str) -> bool:
        return False

    def suggestions(self, word: str, code: str, limit: int = 5) -> list[str]:
        return []

    def close(self) -> None:
        pass


checker = SpellChecker()


def language_tag(code: str) -> str:
    return code
