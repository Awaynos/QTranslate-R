"""История переводов (JSON рядом с приложением)."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class HistoryEntry:
    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    provider_id: str
    provider_name: str
    timestamp: float = field(default_factory=time.time)

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        return cls(
            source_text=str(data.get("source_text", "")),
            translated_text=str(data.get("translated_text", "")),
            source_language=str(data.get("source_language", "")),
            target_language=str(data.get("target_language", "")),
            provider_id=str(data.get("provider_id", "")),
            provider_name=str(data.get("provider_name", "")),
            timestamp=float(data.get("timestamp", 0.0)),
        )


class HistoryStore:
    """Новые записи — в начале списка."""

    def __init__(self, path: Path, limit: int = 500) -> None:
        self._path = path
        self._limit = limit
        self._entries: list[HistoryEntry] = []
        self.load()

    @property
    def entries(self) -> list[HistoryEntry]:
        return list(self._entries)

    def is_empty(self) -> bool:
        return not self._entries

    def add(self, entry: HistoryEntry) -> None:
        self._entries.insert(0, entry)
        if len(self._entries) > self._limit:
            del self._entries[self._limit :]
        self.save()

    def clear(self) -> None:
        self._entries.clear()
        self.save()

    def load(self) -> None:
        if not self._path.is_file():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if isinstance(raw, list):
            self._entries = [HistoryEntry.from_dict(item) for item in raw if isinstance(item, dict)]

    def save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            payload = [asdict(entry) for entry in self._entries]
            self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            # История не критична.
            pass
