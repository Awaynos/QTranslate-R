"""Проверка логики ядра без сети и без UI (фейковые сервисы)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qtranslate_r.core.translation import TranslationService  # noqa: E402
from qtranslate_r.domain.models import TranslationResult  # noqa: E402
from qtranslate_r.services.base import Translator  # noqa: E402
from qtranslate_r.services.registry import ServiceRegistry  # noqa: E402


class FakeAuto(Translator):
    id = "auto"
    name = "Auto"

    def translate(self, request):  # noqa: ANN001
        return TranslationResult(
            self.id, self.name,
            text=f"[{request.source}->{request.target}] {request.text}",
            detected_source="de",
        )


class FakeFixed(Translator):
    id = "fixed"
    name = "Fixed"
    supports_auto = False

    def translate(self, request):  # noqa: ANN001
        return TranslationResult(
            self.id, self.name, text=f"[{request.source}->{request.target}] {request.text}"
        )


def load_chunk_text():
    spec = importlib.util.spec_from_file_location(
        "_util", ROOT / "qtranslate_r" / "services" / "providers" / "_util.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.chunk_text


def main() -> int:
    registry = ServiceRegistry()
    registry.register(FakeAuto())
    registry.register(FakeFixed())
    service = TranslationService(registry)

    print("auto + fixed при auto (fixed должен получить 'de'):")
    for result in service.translate("hallo", "auto", "ru", ["auto", "fixed"]):
        print("  ", result.provider_id, "->", result.text or result.error)

    print("только fixed при auto (ожидается ошибка):")
    for result in service.translate("hallo", "auto", "ru", ["fixed"]):
        print("  ", result.provider_id, "->", result.text or result.error)

    chunk_text = load_chunk_text()
    parts = chunk_text("Первое предложение. Второе предложение. Третье предложение.", 25)
    print("нарезка (лимит 25):", parts)
    assert all(len(p) <= 25 for p in parts)

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
