"""Выбор реализации проверки орфографии."""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from .windows.spellcheck import SpellChecker, checker, language_tag
elif sys.platform == "darwin":
    from .macos.spellcheck import SpellChecker, checker, language_tag
else:
    from .linux.spellcheck import SpellChecker, checker, language_tag

__all__ = ["SpellChecker", "checker", "language_tag"]
