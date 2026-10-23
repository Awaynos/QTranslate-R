"""Диалог настроек с боковым меню разделов."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ...config.settings import Settings
from ...domain.language import all_languages
from ...hotkeys import ACTIONS, binding, scope
from ...localization import available_languages, tr
from ..sizing import lock_button_widths

_THEMES = ("metal", "turquoise", "bronze", "light")


class HotkeyEdit(QLineEdit):
    """Поле записи комбинации: клик — и нажмите нужные клавиши."""

    def __init__(self, sequence: str = "") -> None:
        super().__init__()
        self.setReadOnly(True)
        self.setPlaceholderText(tr("hotkey.press"))
        self.setText(sequence)
        self.setMinimumWidth(170)
        self._recording = False

    def mousePressEvent(self, event) -> None:  # noqa: N802 — метод Qt
        self._recording = True
        self.clear()
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802 — метод Qt
        if not self._recording:
            super().keyPressEvent(event)
            return

        key = event.key()
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return
        if key == Qt.Key.Key_Escape:
            self._recording = False
            self.clear()
            return

        modifiers = event.modifiers()
        parts = []
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            parts.append("Ctrl")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            parts.append("Shift")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            parts.append("Alt")
        if modifiers & Qt.KeyboardModifier.MetaModifier:
            parts.append("Meta")

        key_text = QKeySequence(key).toString()
        if not key_text:
            return
        self.setText("+".join(parts + [key_text]))
        self._recording = False


class SettingsDialog(QDialog):
    def __init__(
        self,
        settings: Settings,
        tts_options: list[tuple[str, str]] | None = None,
        dictionary_options: list[tuple[str, str]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("settings.title"))
        self.resize(840, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        content = QHBoxLayout()
        content.setSpacing(14)

        self._sections = QListWidget()
        self._sections.setFixedWidth(210)
        for key in (
            "settings.general",
            "settings.appearance",
            "settings.translation",
            "settings.services_section",
            "settings.keyboard",
        ):
            self._sections.addItem(tr(key))
        self._sections.currentRowChanged.connect(self._on_section)
        content.addWidget(self._sections)

        self._pages = QStackedWidget()
        self._pages.addWidget(self._build_general(settings))
        self._pages.addWidget(self._build_appearance(settings))
        self._pages.addWidget(self._build_translation(settings))
        self._pages.addWidget(self._build_services(settings, tts_options, dictionary_options))
        self._pages.addWidget(self._build_keyboard(settings))
        content.addWidget(self._pages, 1)

        layout.addLayout(content, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        save = QPushButton(tr("settings.save"))
        save.setObjectName("Primary")
        save.clicked.connect(self.accept)
        cancel = QPushButton(tr("settings.cancel"))
        cancel.clicked.connect(self.reject)
        buttons.addWidget(save)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)

        self._sections.setCurrentRow(0)
        lock_button_widths(self)


    def _page(self, title: str) -> tuple[QWidget, QFormLayout]:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(4, 0, 0, 0)
        outer.setSpacing(10)

        header = QLabel(tr(title))
        header.setObjectName("AppTitle")
        outer.addWidget(header)

        form = QFormLayout()
        form.setSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        outer.addLayout(form)
        outer.addStretch(1)
        return page, form

    def _build_general(self, settings: Settings) -> QWidget:
        page, form = self._page("settings.general")

        self._language = QComboBox()
        self._language.addItem(tr("settings.language.system"), "")
        for code in available_languages():
            self._language.addItem(code[:1].upper() + code[1:], code)
        index = self._language.findData(settings.interface_language)
        if index >= 0:
            self._language.setCurrentIndex(index)
        form.addRow(tr("settings.language"), self._language)

        self._quick_translate = QCheckBox(tr("settings.quick_translate"))
        self._quick_translate.setChecked(bool(settings.quick_translate_enabled))
        form.addRow("", self._quick_translate)

        self._translate_on_type = QCheckBox(tr("settings.translate_on_type"))
        self._translate_on_type.setChecked(bool(settings.translate_on_type))
        form.addRow("", self._translate_on_type)

        self._native = QComboBox()
        self._native.addItem(tr("settings.not_set"), "")
        for language in all_languages(include_auto=False):
            self._native.addItem(language.name, language.code)
        self._set(self._native, settings.native_language)
        form.addRow(tr("settings.native_language"), self._native)

        self._second = QComboBox()
        self._second.addItem(tr("settings.not_set"), "")
        for language in all_languages(include_auto=False):
            self._second.addItem(language.name, language.code)
        self._set(self._second, settings.second_language)
        form.addRow(tr("settings.second_language"), self._second)

        return page

    def _build_appearance(self, settings: Settings) -> QWidget:
        page, form = self._page("settings.appearance")

        self._theme = QComboBox()
        for theme in _THEMES:
            self._theme.addItem(tr(f"settings.theme.{theme}"), theme)
        index = self._theme.findData(settings.theme)
        if index >= 0:
            self._theme.setCurrentIndex(index)
        form.addRow(tr("settings.theme"), self._theme)

        self._font_size = QSpinBox()
        self._font_size.setRange(10, 24)
        self._font_size.setValue(int(settings.font_size))
        form.addRow(tr("settings.font_size"), self._font_size)

        return page

    def _build_translation(self, settings: Settings) -> QWidget:
        page, form = self._page("settings.translation")

        self._max_chars = QSpinBox()
        self._max_chars.setRange(500, 20000)
        self._max_chars.setSingleStep(500)
        self._max_chars.setValue(int(settings.max_chars))
        form.addRow(tr("settings.max_chars"), self._max_chars)

        return page

    def _build_services(
        self,
        settings: Settings,
        tts_options: list[tuple[str, str]] | None,
        dictionary_options: list[tuple[str, str]] | None,
    ) -> QWidget:
        page, form = self._page("settings.services_section")

        self._tts = QComboBox()
        for service_id, name in tts_options or []:
            self._tts.addItem(name, service_id)
        self._set(self._tts, settings.tts_provider)
        form.addRow(tr("settings.tts"), self._tts)

        self._dictionary = QComboBox()
        for service_id, name in dictionary_options or []:
            self._dictionary.addItem(name, service_id)
        self._set(self._dictionary, settings.dictionary_provider)
        form.addRow(tr("settings.dictionary"), self._dictionary)

        self._csv_path = QLineEdit(settings.csv_path)
        self._csv_path.setPlaceholderText(tr("settings.optional"))
        form.addRow(tr("settings.csv_path"), self._csv_path)

        self._csv_term = QSpinBox()
        self._csv_term.setRange(0, 20)
        self._csv_term.setValue(int(settings.csv_term_column))
        form.addRow(tr("settings.csv_term"), self._csv_term)

        self._csv_definition = QSpinBox()
        self._csv_definition.setRange(0, 20)
        self._csv_definition.setValue(int(settings.csv_definition_column))
        form.addRow(tr("settings.csv_definition"), self._csv_definition)

        self._mymemory_email = QLineEdit(settings.mymemory_email)
        self._mymemory_email.setPlaceholderText(tr("settings.optional"))
        form.addRow(tr("settings.mymemory_email"), self._mymemory_email)

        self._libre_url = QLineEdit(settings.libretranslate_url)
        form.addRow(tr("settings.libre_url"), self._libre_url)

        self._libre_key = QLineEdit(settings.libretranslate_api_key)
        self._libre_key.setPlaceholderText(tr("settings.optional"))
        form.addRow(tr("settings.libre_key"), self._libre_key)

        return page

    def _build_keyboard(self, settings: Settings) -> QWidget:
        page, form = self._page("settings.keyboard")

        self._hotkey_edits: dict[str, HotkeyEdit] = {}
        self._hotkey_scopes: dict[str, QComboBox] = {}

        for action in ACTIONS:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(8)

            edit = HotkeyEdit(binding(settings, action.id))
            row.addWidget(edit, 1)

            scope_combo = QComboBox()
            scope_combo.addItem(tr("settings.scope.local"), "local")
            scope_combo.addItem(tr("settings.scope.global"), "global")
            scope_combo.setFixedWidth(130)
            self._set(scope_combo, scope(settings, action.id))
            row.addWidget(scope_combo)

            form.addRow(tr(action.label_key), self._row(row))
            self._hotkey_edits[action.id] = edit
            self._hotkey_scopes[action.id] = scope_combo

        return page

    @staticmethod
    def _row(layout: QHBoxLayout) -> QWidget:
        widget = QWidget()
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget

    @staticmethod
    def _set(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _on_section(self, row: int) -> None:
        self._pages.setCurrentIndex(max(0, row))


    def values(self) -> dict:
        return {
            "interface_language": self._language.currentData() or "",
            "theme": self._theme.currentData() or "metal",
            "font_size": self._font_size.value(),
            "max_chars": self._max_chars.value(),
            "translate_on_type": self._translate_on_type.isChecked(),
            "quick_translate_enabled": self._quick_translate.isChecked(),
            "native_language": self._native.currentData() or "",
            "second_language": self._second.currentData() or "",
            "tts_provider": self._tts.currentData() or "system-tts",
            "dictionary_provider": self._dictionary.currentData() or "wiktionary",
            "csv_path": self._csv_path.text().strip(),
            "csv_term_column": self._csv_term.value(),
            "csv_definition_column": self._csv_definition.value(),
            "mymemory_email": self._mymemory_email.text().strip(),
            "libretranslate_url": self._libre_url.text().strip(),
            "libretranslate_api_key": self._libre_key.text().strip(),
            "hotkeys": {action: edit.text().strip() for action, edit in self._hotkey_edits.items()},
            "hotkey_scopes": {
                action: combo.currentData() for action, combo in self._hotkey_scopes.items()
            },
        }
