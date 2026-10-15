"""Нарезка длинного текста на части."""

from __future__ import annotations

import re

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?。！？\n])")


def chunk_text(text: str, limit: int) -> list[str]:
    """Разбить текст на части не длиннее limit, по предложениям (или словам)."""
    if limit <= 0 or len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    for sentence in _SENTENCE_SPLIT.split(text):
        if not sentence:
            continue
        if len(sentence) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_by_words(sentence, limit))
            continue
        if len(current) + len(sentence) > limit and current:
            chunks.append(current)
            current = sentence
        else:
            current += sentence
    if current:
        chunks.append(current)
    return [c for c in chunks if c]


def _split_by_words(text: str, limit: int) -> list[str]:
    parts: list[str] = []
    current = ""
    for word in text.split(" "):
        candidate = f"{current} {word}".strip()
        if len(candidate) > limit and current:
            parts.append(current)
            current = word
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts
