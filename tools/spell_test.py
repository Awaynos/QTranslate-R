"""Проверка орфографии: реальный enchant или подмена движка."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication  # noqa: E402

from qtranslate_r.platform.spellcheck import checker  # noqa: E402
from qtranslate_r.ui.spellcheck import SpellTextEdit  # noqa: E402


def fake_test() -> None:
    from qtranslate_r.platform.linux import spellcheck as linux_spellcheck

    class FakeDictionary:
        def check(self, word: str) -> bool:
            return word != "wrld"

        def suggest(self, word: str) -> list[str]:
            return ["world", "would"]

    class FakeEnchant:
        def Dict(self, tag: str) -> FakeDictionary:
            return FakeDictionary()

    original = linux_spellcheck.enchant
    linux_spellcheck.enchant = FakeEnchant()
    try:
        backend = linux_spellcheck.SpellChecker()
        assert backend.supported("en")
        assert backend.is_misspelled("wrld", "en")
        assert not backend.is_misspelled("hello", "en")
        assert backend.suggestions("wrld", "en") == ["world", "would"]
    finally:
        linux_spellcheck.enchant = original
    print("fake enchant: OK")


def main() -> int:
    app = QApplication(sys.argv)
    if not checker.supported("en"):
        print("SKIP: enchant dictionary for en is not installed")
        fake_test()
        print("OK")
        return 0

    edit = SpellTextEdit()
    edit.set_spellcheck(True, "en")
    edit.setPlainText("hello wrld")
    app.processEvents()

    wrong = checker.is_misspelled("wrld", "en")
    correct = checker.is_misspelled("hello", "en")
    print("wrld misspelled:", wrong)
    print("hello misspelled:", correct)
    print("suggestions:", ", ".join(checker.suggestions("wrld", "en", 3)))
    print("OK" if wrong and not correct else "FAIL")
    return 0 if wrong and not correct else 1


if __name__ == "__main__":
    raise SystemExit(main())
