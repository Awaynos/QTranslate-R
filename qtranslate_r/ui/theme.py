"""Темы оформления: палитры, таблица стилей и палитра Qt."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

PALETTES: dict[str, dict[str, str]] = {
    "metal": {
        "bg": "#202020",
        "surface": "#2a2a2a",
        "surface_alt": "#333333",
        "border": "#3d3d3d",
        "border_light": "#4e4e4e",
        "divider": "#2c2c2c",
        "text": "#d4d4d4",
        "muted": "#909090",
        "accent": "#b6b6b6",
        "accent_hover": "#c6c6c6",
        "accent_text": "#1c1c1c",
        "danger": "#c06a62",
        "btn_top": "#3b3b3b",
        "btn_bottom": "#303030",
        "btn_hover_top": "#454545",
        "btn_hover_bottom": "#393939",
        "btn_pressed_top": "#292929",
        "btn_pressed_bottom": "#353535",
        "act_top": "#cccccc",
        "act_bottom": "#a6a6a6",
        "act_hover_top": "#dadada",
        "act_hover_bottom": "#b4b4b4",
        "act_pressed_top": "#9a9a9a",
        "act_pressed_bottom": "#b2b2b2",
        "act_text": "#1c1c1c",
        "header_top": "#2f2f2f",
        "header_bottom": "#242424",
        "seg_on_top": "#b6b6b6",
        "seg_on_bottom": "#9c9c9c",
        "focus": "#b6b6b6",
    },
    "turquoise": {
        "bg": "#122023",
        "surface": "#182b30",
        "surface_alt": "#1e353b",
        "border": "#284650",
        "border_light": "#365d68",
        "divider": "#1c343a",
        "text": "#d7e8e6",
        "muted": "#82a6a3",
        "accent": "#31bcae",
        "accent_hover": "#3fd0c1",
        "accent_text": "#04211f",
        "danger": "#dc7268",
        "btn_top": "#1f3a41",
        "btn_bottom": "#182d33",
        "btn_hover_top": "#254450",
        "btn_hover_bottom": "#1c343a",
        "btn_pressed_top": "#122327",
        "btn_pressed_bottom": "#1b3238",
        "act_top": "#2fbdaf",
        "act_bottom": "#219c90",
        "act_hover_top": "#3fd0c1",
        "act_hover_bottom": "#28a89b",
        "act_pressed_top": "#1c857a",
        "act_pressed_bottom": "#26a094",
        "act_text": "#04211f",
        "header_top": "#1e353b",
        "header_bottom": "#152528",
        "seg_on_top": "#31bcae",
        "seg_on_bottom": "#289e92",
        "focus": "#31bcae",
    },
    "bronze": {
        "bg": "#211d19",
        "surface": "#2c261f",
        "surface_alt": "#352e26",
        "border": "#463a2e",
        "border_light": "#5a4a39",
        "divider": "#2a231c",
        "text": "#e7ded3",
        "muted": "#a79584",
        "accent": "#bd8f52",
        "accent_hover": "#cb9c5d",
        "accent_text": "#241a0d",
        "danger": "#d97164",
        "btn_top": "#3d3429",
        "btn_bottom": "#2f281f",
        "btn_hover_top": "#473c2f",
        "btn_hover_bottom": "#382f26",
        "btn_pressed_top": "#262019",
        "btn_pressed_bottom": "#332b23",
        "act_top": "#bd8f52",
        "act_bottom": "#9a7440",
        "act_hover_top": "#cb9c5d",
        "act_hover_bottom": "#a87d46",
        "act_pressed_top": "#856334",
        "act_pressed_bottom": "#a17945",
        "act_text": "#241a0d",
        "header_top": "#332c24",
        "header_bottom": "#252019",
        "seg_on_top": "#bd8f52",
        "seg_on_bottom": "#9d7642",
        "focus": "#bd8f52",
    },
    "light": {
        "bg": "#e9ebee",
        "surface": "#f6f7f9",
        "surface_alt": "#ffffff",
        "border": "#c4cad2",
        "border_light": "#dde2e8",
        "divider": "#d7dbe1",
        "text": "#1f2429",
        "muted": "#667085",
        "accent": "#1b8f85",
        "accent_hover": "#22a396",
        "accent_text": "#ffffff",
        "danger": "#bf4036",
        "btn_top": "#ffffff",
        "btn_bottom": "#e8ebef",
        "btn_hover_top": "#ffffff",
        "btn_hover_bottom": "#eef1f4",
        "btn_pressed_top": "#dde1e6",
        "btn_pressed_bottom": "#eaecef",
        "act_top": "#1f9e92",
        "act_bottom": "#177c73",
        "act_hover_top": "#26b3a6",
        "act_hover_bottom": "#1b8a80",
        "act_pressed_top": "#136a62",
        "act_pressed_bottom": "#19867c",
        "act_text": "#ffffff",
        "header_top": "#ffffff",
        "header_bottom": "#e7eaee",
        "seg_on_top": "#1b8f85",
        "seg_on_bottom": "#167c74",
        "focus": "#1b8f85",
    },
}

_QSS = """
* { font-family: "Segoe UI", "Inter", "Noto Sans", sans-serif; outline: none; }
QMainWindow, QDialog, #Root { background: %(bg)s; }
QWidget { color: %(text)s; }
QLabel { background: transparent; }

QLabel#AppTitle { font-size: 15px; font-weight: 700; }
QLabel#AppVersion { color: %(muted)s; font-size: 10px; font-weight: 300; }
QLabel#PageTitle { font-size: 16px; font-weight: 700; }
QLabel#AppSubtitle { color: %(muted)s; font-size: 11px; }
QLabel#SectionLabel { color: %(muted)s; font-size: 10px; font-weight: 600; }
QLabel#EmptyState { color: %(muted)s; font-size: 13px; }
QLabel#CardTitle { font-weight: 600; font-size: 12px; }
QLabel#CardMeta { color: %(muted)s; font-size: 11px; }
QLabel#CardBody { font-size: 14px; }
QLabel#CardError { color: %(danger)s; font-size: 12px; }
QLabel#Detected { color: %(accent)s; font-size: 11px; }
QLabel#Counter { color: %(muted)s; font-size: 10px; }
QLabel#Usage { color: %(muted)s; font-size: 11px; }
QLabel#PanelTitle { font-weight: 600; font-size: 12px; }

QFrame#Card { background: %(surface)s; border: 1px solid %(border)s; border-radius: 4px; }
QFrame#Header {
    border: none; border-bottom: 1px solid %(divider)s;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(header_top)s, stop:1 %(header_bottom)s);
}
QFrame#Bar {
    border: none; border-bottom: 1px solid %(divider)s;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(header_top)s, stop:1 %(header_bottom)s);
}
QFrame#Toolbar { background: transparent; border: none; }

QComboBox {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(btn_top)s, stop:1 %(btn_bottom)s);
    border: 1px solid %(border)s; border-top-color: %(border_light)s;
    border-radius: 3px; padding: 4px 24px 4px 8px; min-height: 18px;
}
QComboBox:hover { border-color: %(border_light)s; }
QComboBox:focus { border-color: %(focus)s; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox::down-arrow {
    image: none; width: 0; height: 0; margin-right: 7px;
    border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 4px solid %(muted)s;
}
QComboBox QAbstractItemView {
    background: %(surface)s; border: 1px solid %(border)s;
    selection-background-color: %(accent)s; selection-color: %(accent_text)s;
    padding: 2px; outline: none;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(btn_top)s, stop:1 %(btn_bottom)s);
    border: 1px solid %(border)s; border-top-color: %(border_light)s;
    border-radius: 3px; padding: 5px 12px; color: %(text)s;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(btn_hover_top)s, stop:1 %(btn_hover_bottom)s);
    border-color: %(border_light)s;
}
QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(btn_pressed_top)s, stop:1 %(btn_pressed_bottom)s);
    padding-top: 6px; padding-bottom: 4px;
}
QPushButton:disabled { color: %(muted)s; }

QPushButton#Primary {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(act_top)s, stop:1 %(act_bottom)s);
    border: 1px solid %(act_bottom)s; border-top-color: %(act_hover_top)s;
    color: %(act_text)s; font-weight: 600; padding: 6px 18px;
}
QPushButton#Primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(act_hover_top)s, stop:1 %(act_hover_bottom)s);
}
QPushButton#Primary:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(act_pressed_top)s, stop:1 %(act_pressed_bottom)s);
    padding-top: 7px; padding-bottom: 5px;
}
QPushButton#Primary:disabled { color: %(muted)s; border-color: %(border)s; }

QPushButton#Ghost { background: transparent; border: 1px solid transparent; padding: 5px 8px; font-size: 14px; }
QPushButton#Ghost:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(btn_hover_top)s, stop:1 %(btn_hover_bottom)s);
    border-color: %(border)s;
}
QPushButton#Ghost:pressed { background: %(btn_pressed_top)s; }

QPushButton#Icon {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(btn_top)s, stop:1 %(btn_bottom)s);
    border: 1px solid %(border)s; border-top-color: %(border_light)s;
    border-radius: 3px; padding: 3px 7px; font-size: 13px;
}
QPushButton#Icon:hover { border-color: %(border_light)s; }
QPushButton#Icon:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(btn_pressed_top)s, stop:1 %(btn_pressed_bottom)s);
}

QPushButton#Chip {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(btn_top)s, stop:1 %(btn_bottom)s);
    border: 1px solid %(border)s; border-top-color: %(border_light)s;
    border-radius: 3px; padding: 4px 12px; color: %(muted)s;
}
QPushButton#Chip:hover { border-color: %(border_light)s; color: %(text)s; }
QPushButton#Chip:checked {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(btn_hover_top)s, stop:1 %(btn_hover_bottom)s);
    border-color: %(accent)s; color: %(accent)s;
}

QPushButton#Segment {
    background: transparent; border: 1px solid transparent; border-radius: 3px;
    padding: 5px 14px; color: %(muted)s;
}
QPushButton#Segment:hover { color: %(text)s; border-color: %(border)s; }
QPushButton#Segment:checked {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(btn_hover_top)s, stop:1 %(btn_hover_bottom)s);
    border: 1px solid %(border_light)s; border-bottom: 2px solid %(accent)s;
    color: %(text)s;
}

QPushButton#Copy {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(btn_top)s, stop:1 %(btn_bottom)s);
    border: 1px solid %(border)s; border-radius: 3px; padding: 3px 9px;
    color: %(muted)s; font-size: 11px;
}
QPushButton#Copy:hover { border-color: %(border_light)s; color: %(text)s; }

QPushButton#Window {
    background: transparent; border: 1px solid transparent; border-radius: 3px;
    padding: 4px 10px; font-size: 13px; color: %(muted)s;
}
QPushButton#Window:hover { background: %(btn_hover_top)s; color: %(text)s; border-color: %(border)s; }
QPushButton#WindowClose:hover { background: %(danger)s; color: #ffffff; border-color: %(danger)s; }

QPlainTextEdit, QTextEdit {
    background: %(surface)s; border: 1px solid %(border)s; border-radius: 3px; padding: 7px;
    selection-background-color: %(accent)s; selection-color: %(accent_text)s;
}
QPlainTextEdit:focus, QTextEdit:focus { border-color: %(focus)s; }

QLineEdit, QSpinBox {
    background: %(surface_alt)s; border: 1px solid %(border)s; border-radius: 3px; padding: 5px 8px;
}
QLineEdit:focus, QSpinBox:focus { border-color: %(focus)s; }

QCheckBox { spacing: 8px; }
QCheckBox::indicator {
    width: 15px; height: 15px; border: 1px solid %(border)s; border-radius: 3px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(btn_top)s, stop:1 %(btn_bottom)s);
}
QCheckBox::indicator:checked { background: %(accent)s; border-color: %(accent)s; }

QProgressBar {
    background: %(surface_alt)s; border: 1px solid %(border)s; border-radius: 3px;
    height: 16px; text-align: center; color: %(text)s; font-size: 11px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(seg_on_top)s, stop:1 %(seg_on_bottom)s);
}

QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }

QSplitter { background: transparent; }
QSplitter::handle { background: transparent; }
QSplitter::handle:vertical {
    height: 7px; border: none; border-top: 1px dotted %(divider)s; border-bottom: 1px dotted %(divider)s;
}
QSplitter::handle:horizontal {
    width: 7px; border: none; border-left: 1px dotted %(divider)s; border-right: 1px dotted %(divider)s;
}
QSplitter::handle:hover { background: %(surface_alt)s; }

QMenu { background: %(surface)s; border: 1px solid %(border)s; padding: 4px; }
QMenu::item { padding: 5px 24px 5px 22px; border-radius: 3px; }
QMenu::item:selected { background: %(accent)s; color: %(accent_text)s; }
QMenu::separator { height: 1px; background: %(border)s; margin: 4px 6px; }

QScrollBar:vertical { background: transparent; width: 9px; margin: 2px; }
QScrollBar::handle:vertical { background: %(border)s; border-radius: 2px; min-height: 28px; }
QScrollBar::handle:vertical:hover { background: %(border_light)s; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal { height: 9px; }
QScrollBar::handle:horizontal { background: %(border)s; border-radius: 2px; }

QStatusBar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(header_top)s, stop:1 %(header_bottom)s);
    border-top: 1px solid %(divider)s; color: %(muted)s;
}
QStatusBar::item { border: none; }

QListWidget { background: %(surface)s; border: 1px solid %(border)s; border-radius: 3px; padding: 3px; }
QListWidget::item { padding: 7px 8px; border-radius: 3px; }
QListWidget::item:selected { background: %(accent)s; color: %(accent_text)s; }

QToolTip { background: %(surface)s; color: %(text)s; border: 1px solid %(border)s; padding: 3px; }
"""


def palette(theme: str) -> dict[str, str]:
    return PALETTES.get(theme, PALETTES["metal"])


def build_qss(theme: str) -> str:
    return _QSS % palette(theme)


def build_palette(theme: str) -> QPalette:
    """Палитра Qt из темы — чтобы нигде не проступали системные цвета."""
    colors = palette(theme)
    result = QPalette()
    window = QColor(colors["bg"])
    surface = QColor(colors["surface"])
    surface_alt = QColor(colors["surface_alt"])
    text = QColor(colors["text"])
    muted = QColor(colors["muted"])
    accent = QColor(colors["accent"])
    accent_text = QColor(colors["accent_text"])

    result.setColor(QPalette.ColorRole.Window, window)
    result.setColor(QPalette.ColorRole.WindowText, text)
    result.setColor(QPalette.ColorRole.Base, surface)
    result.setColor(QPalette.ColorRole.AlternateBase, surface_alt)
    result.setColor(QPalette.ColorRole.Text, text)
    result.setColor(QPalette.ColorRole.PlaceholderText, muted)
    result.setColor(QPalette.ColorRole.Button, surface_alt)
    result.setColor(QPalette.ColorRole.ButtonText, text)
    result.setColor(QPalette.ColorRole.BrightText, QColor(colors["danger"]))
    result.setColor(QPalette.ColorRole.Highlight, accent)
    result.setColor(QPalette.ColorRole.HighlightedText, accent_text)
    result.setColor(QPalette.ColorRole.ToolTipBase, surface)
    result.setColor(QPalette.ColorRole.ToolTipText, text)
    result.setColor(QPalette.ColorRole.Link, accent)
    result.setColor(QPalette.ColorRole.LinkVisited, accent)
    return result


def apply_theme(app: QApplication, theme: str) -> None:
    app.setStyleSheet(build_qss(theme))
    app.setPalette(build_palette(theme))
