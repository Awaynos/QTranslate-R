"""Проверка авто-пары «Родной-Второй»: направление выбирается определением языка."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qtranslate_r.core.translation import TranslationService  # noqa: E402
from qtranslate_r.domain.language import AUTO_PAIR  # noqa: E402
from qtranslate_r.domain.models import TranslationResult  # noqa: E402
from qtranslate_r.services.base import Translator  # noqa: E402
from qtranslate_r.services.registry import ServiceRegistry  # noqa: E402


class FakeDetector(Translator):
    """Определяет язык по метке в тексте: 'ru:...' или 'en:...'."""

    id = "fake"
    name = "Fake"

    def translate(self, request):  # noqa: ANN001
        detected = "ru" if request.text.startswith("ru:") else "en"
        return TranslationResult(
            self.id,
            self.name,
            text=request.target,
            detected_source=detected if request.source == "auto" else None,
        )


def run(text: str) -> str:
    registry = ServiceRegistry()
    registry.register(FakeDetector())
    service = TranslationService(registry)
    results = service.translate(
        text, "auto", AUTO_PAIR, ["fake"], native="ru", second="en"
    )
    return results[0].text


def main() -> int:
    cases = {
        "ru:привет": "en",
        "en:hello": "ru",
    }
    ok = True
    for text, expected in cases.items():
        actual = run(text)
        mark = "OK" if actual == expected else "ПРОВАЛ"
        print(f"{text!r}: {actual} (ожидалось {expected}) — {mark}")
        ok = ok and actual == expected
    print("OK" if ok else "ПРОВАЛ")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
