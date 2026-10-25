"""Подсветка орфографических ошибок и подсказки в поле ввода."""

from __future__ import annotations

import re

from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QMenu, QPlainTextEdit

from ..platform.spellcheck import checker

_WORD = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*", re.UNICODE)


class SpellHighlighter(QSyntaxHighlighter):
    def __init__(self, document) -> None:
        super().__init__(document)
        self._language = ""
        self._enabled = False
        self._format = QTextCharFormat()
        self._format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
        self._format.setUnderlineColor(QColor("#e05a5a"))

    def set_language(self, language: str) -> None:
        self._language = language
        self.rehighlight()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:  # noqa: N802 — метод Qt
        if not self._enabled or not self._language or len(text) > 20000:
            return
        for match in _WORD.finditer(text):
            word = match.group()
            if len(word) < 2:
                continue
            if checker.is_misspelled(word, self._language):
                self.setFormat(match.start(), match.end() - match.start(), self._format)


class SpellTextEdit(QPlainTextEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._language = ""
        self._enabled = False
        self._word_cursor = None
        self._highlighter = SpellHighlighter(self.document())

    def set_spellcheck(self, enabled: bool, language: str) -> None:
        self._language = language if enabled and checker.supported(language) else ""
        self._enabled = bool(self._language)
        self._highlighter.set_language(self._language)
        self._highlighter.set_enabled(self._enabled)

    def contextMenuEvent(self, event) -> None:  # noqa: N802 — метод Qt
        menu = self.createStandardContextMenu()
        if self._enabled:
            self._add_suggestions(menu, event.pos())
        menu.exec(event.globalPos())
        menu.deleteLater()

    def _add_suggestions(self, menu: QMenu, position) -> None:
        cursor = self.cursorForPosition(position)
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText().strip()
        if not word or not checker.is_misspelled(word, self._language):
            return

        suggestions = checker.suggestions(word, self._language)
        if not suggestions:
            return

        self._word_cursor = QTextCursor(cursor)
        anchor = menu.actions()[0] if menu.actions() else None
        for index, suggestion in enumerate(suggestions):
            action = menu.addAction(suggestion)
            action.triggered.connect(lambda _checked=False, value=suggestion: self._replace_word(value))
            if anchor is not None:
                menu.removeAction(action)
                menu.insertAction(anchor, action)
        separator = menu.addSeparator()
        if anchor is not None:
            menu.removeAction(separator)
            menu.insertSeparator(anchor)

    def _replace_word(self, value: str) -> None:
        if self._word_cursor is None:
            return
        cursor = QTextCursor(self._word_cursor)
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.insertText(value)
        self.setTextCursor(cursor)
