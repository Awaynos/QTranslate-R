"""Проверка орфографии в поле ввода."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication  # noqa: E402

from qtranslate_r.platform.spellcheck import checker  # noqa: E402
from qtranslate_r.ui.spellcheck import SpellTextEdit  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv)
    if not checker.supported("en"):
        print("SKIP: Windows spell checking for en-US is not installed")
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
