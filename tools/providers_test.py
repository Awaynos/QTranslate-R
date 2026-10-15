"""Проверка всех переводчиков: явный язык и автоопределение."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qtranslate_r.core.setup import build_registry  # noqa: E402
from qtranslate_r.core.translation import TranslationService  # noqa: E402

ALL = ["google", "yandex", "reverso", "mymemory", "libretranslate"]


def show(title: str, results) -> None:
    print(title)
    for result in results:
        tag = "OK" if result.ok else "ERR"
        body = result.text or result.error
        print(f"  [{tag}] {result.provider_name}: {body}")


def main() -> int:
    service = TranslationService(build_registry())

    show("en -> ru, все переводчики:", service.translate("Hello, world!", "en", "ru", ALL))
    show("auto -> ru (google + yandex):", service.translate("Guten Morgen", "auto", "ru", ["google", "yandex"]))
    show("ru -> en (yandex + reverso):", service.translate("Доброе утро", "ru", "en", ["yandex", "reverso"]))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
