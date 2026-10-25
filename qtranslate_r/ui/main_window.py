"""Главное окно."""

from __future__ import annotations

import ctypes
import os
import sys
import tempfile
from ctypes import wintypes
from pathlib import Path

from PySide6.QtCore import QByteArray, QEvent, QPoint, QRect, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import (
    QCursor,
    QFont,
    QGuiApplication,
    QIcon,
    QKeySequence,
    QPixmap,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from .. import __app_name__, __version__
from ..config.settings import Settings
from ..config.paths import app_icon_file
from ..core.history import HistoryEntry, HistoryStore
from ..core.setup import (
    configure_registry,
    dictionary_choices,
    dictionary_service,
    translator_choices,
    tts_choices,
)
from ..core.translation import TranslationService
from ..domain.language import AUTO, AUTO_PAIR, language_name, pair_label
from ..domain.models import DictionaryEntry, TranslationResult
from ..hotkeys import ACTIONS, binding, combination, scope, virtual_key
from ..localization import tr
from ..platform.hotkey import GlobalHotkey
from ..services.registry import ServiceRegistry
from ..speech import SpeechController
from .dialogs import DocumentDialog, HistoryDialog, SettingsDialog
from .dictionary_panel import DictionaryPanel
from .icons import icon_size, icon as load_icon, ensure_ico, set_color as set_icon_color
from .loading import InlineLoading
from .ocr_overlay import OcrOverlay, capture_region
from .sizing import lock_button_widths
from .spellcheck import SpellTextEdit
from .theme import apply_theme, palette
from .widgets import LanguageBar, ProviderBar, ResultCard
from .workers import DictionaryWorker, OcrWorker, TranslateWorker

_PANEL_BACKWARD = 0
_PANEL_DICTIONARY = 1

# Нативный ресайз безрамочного окна за края (WM_NCHITTEST).
_WM_NCHITTEST = 0x0084
_RESIZE_MARGIN = 6


class _WinMessage(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt_x", wintypes.LONG),
        ("pt_y", wintypes.LONG),
    ]


class _TitleBar(QFrame):
    """Полоса заголовка безрамочного окна: перетаскивание и двойной клик."""

    def __init__(self, window: "MainWindow") -> None:
        super().__init__(window)
        self._window = window
        self._drag_offset = None

    def mousePressEvent(self, event) -> None:  # noqa: N802 — метод Qt
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 — метод Qt
        if self._drag_offset is None or not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if self._window.isMaximized():
            self._window.showNormal()
            self._drag_offset = event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
        self._window.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 — метод Qt
        self._drag_offset = None

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802 — метод Qt
        self._window.toggle_maximize()


class MainWindow(QMainWindow):
    hotkeysChanged = Signal()

    def __init__(
        self,
        *,
        app: QApplication,
        settings: Settings,
        settings_path,
        registry: ServiceRegistry,
        translation_service: TranslationService,
        history_store: HistoryStore,
        speech: SpeechController,
    ) -> None:
        super().__init__()
        self._app = app
        self._settings = settings
        self._settings_path = settings_path
        self._registry = registry
        self._service = translation_service
        self._history = history_store
        self._speech = speech

        self._pool = QThreadPool.globalInstance()
        self._token = 0
        self._active_worker = None
        self._backward_token = 0
        self._backward_worker = None
        self._dictionary_token = 0
        self._dictionary_worker = None
        self._dictionary_pending: tuple[str, str] = ("", "en")
        self._pending: tuple[str, str, str] = ("", AUTO, "en")
        self._ocr_token = 0
        self._ocr_worker = None
        self._ocr_overlay = None
        self._history_index = 0
        self._last_result_text = ""
        self._shortcuts: list[QShortcut] = []
        self._global_hotkeys: list[GlobalHotkey] = []
        self._icon_buttons: list[tuple[QPushButton, tuple[str, ...]]] = []
        self._tray: QSystemTrayIcon | None = None
        self._splitter = None
        self._thick_frame = False

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(700)
        self._debounce.timeout.connect(lambda: self._start_translation(silent=True))

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(500)
        self._save_timer.timeout.connect(self._persist)

        self.setWindowTitle(f"{__app_name__} {__version__}")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setWindowIcon(QIcon(str(app_icon_file())))
        self.resize(1020, 840)
        self.setMinimumSize(860, 640)

        self._build_ui()
        lock_button_widths(self)
        self._build_tray()
        self._apply_icons()
        self._apply_hotkeys()
        self._restore_state()
        self._apply_spellcheck()
        self._app.aboutToQuit.connect(self._stop_hotkeys)
        self._speech.playingChanged.connect(self._on_speech_state)
        self._speech.errorOccurred.connect(lambda msg: self._status.showMessage(msg, 4000))


    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("Root")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_title_bar())
        root.addWidget(self._build_history_row())
        root.addWidget(self._build_services_row())

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(14, 12, 14, 12)
        body_layout.setSpacing(10)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_input())
        splitter.addWidget(self._build_output())
        splitter.addWidget(self._build_panel())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 2)
        splitter.setSizes([280, 330, 200])
        splitter.splitterMoved.connect(lambda *_: self._save_timer.start())
        self._splitter = splitter
        body_layout.addWidget(splitter, 1)

        body_layout.addWidget(self._build_selectors())
        root.addWidget(body, 1)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._loading = InlineLoading()
        self._status.addPermanentWidget(self._loading)
        self._status.setSizeGripEnabled(False)
        self._status.showMessage(tr("status.ready"))

    def _build_title_bar(self) -> QWidget:
        bar = _TitleBar(self)
        bar.setObjectName("Header")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 6, 6, 6)
        layout.setSpacing(6)

        icon_path = app_icon_file()
        if icon_path.is_file():
            logo = QLabel()
            logo.setPixmap(
                QPixmap(str(icon_path)).scaled(
                    22,
                    22,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            layout.addWidget(logo)

        title = QLabel(__app_name__)
        title.setObjectName("AppTitle")
        layout.addWidget(title)

        version = QLabel(__version__)
        version.setObjectName("AppVersion")
        layout.addWidget(version)
        layout.addStretch(1)

        minimize = QPushButton("\u2013")
        minimize.setObjectName("Window")
        minimize.setToolTip(tr("window.minimize"))
        minimize.clicked.connect(self.showMinimized)
        self._attach_icon(minimize, "minus")
        layout.addWidget(minimize)

        self._maximize_button = QPushButton("\u25a1")
        self._maximize_button.setObjectName("Window")
        self._maximize_button.setToolTip(tr("window.maximize"))
        self._maximize_button.clicked.connect(self.toggle_maximize)
        self._attach_icon(self._maximize_button, "square")
        layout.addWidget(self._maximize_button)

        close = QPushButton("\u2715")
        close.setObjectName("WindowClose")
        close.setToolTip(tr("window.close"))
        close.clicked.connect(self.close)
        self._attach_icon(close, "x")
        layout.addWidget(close)

        return bar

    def toggle_maximize(self) -> None:
        if self.isMaximized():
            self.showNormal()
            if self._maximize_button.icon().isNull():
                self._maximize_button.setText("\u25a1")
            self._maximize_button.setToolTip(tr("window.maximize"))
        else:
            self.showMaximized()
            if self._maximize_button.icon().isNull():
                self._maximize_button.setText("\u2750")
            self._maximize_button.setToolTip(tr("window.restore"))


    def _build_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self._tray = QSystemTrayIcon(QIcon(str(app_icon_file())), self)
        self._tray.setToolTip(f"{__app_name__} {__version__}")

        menu = QMenu(self)
        show_action = menu.addAction(tr("tray.show"))
        show_action.triggered.connect(self._restore_from_tray)
        settings_action = menu.addAction(tr("header.settings"))
        settings_action.triggered.connect(self._open_settings)
        menu.addSeparator()
        quit_action = menu.addAction(tr("tray.exit"))
        quit_action.triggered.connect(self._quit)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _on_tray_activated(self, reason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._restore_from_tray()

    def _restore_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _hide_to_tray(self) -> None:
        if self._tray is None:
            return
        self.hide()
        self._tray.showMessage(
            __app_name__,
            tr("tray.minimized"),
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    def _quit(self) -> None:
        self._settings.window_geometry = bytes(self.saveGeometry().toBase64()).decode()
        self._persist()
        application = QApplication.instance()
        if application is not None:
            application.quit()

    def changeEvent(self, event) -> None:  # noqa: N802 — метод Qt
        if event.type() == QEvent.Type.WindowStateChange and self.isMinimized():
            QTimer.singleShot(0, self._hide_to_tray)
        super().changeEvent(event)

    def showEvent(self, event) -> None:  # noqa: N802 — метод Qt
        super().showEvent(event)
        self._enable_native_resize()
        self._apply_window_icon()

    def _apply_window_icon(self) -> None:
        """Значок окна и панели задач — наш .ico, а не питоновский."""
        if sys.platform != "win32":
            return
        ico = ensure_ico()
        if ico is None:
            return
        try:
            user32 = ctypes.windll.user32
            lr_loadfromfile = 0x0010
            image_icon = 1
            wm_seticon = 0x0080
            icon_small = 0
            icon_big = 1

            hwnd = wintypes.HWND(int(self.winId()))
            big = user32.LoadImageW(None, str(ico), image_icon, 32, 32, lr_loadfromfile)
            small = user32.LoadImageW(None, str(ico), image_icon, 16, 16, lr_loadfromfile)
            if big:
                user32.SendMessageW(hwnd, wm_seticon, icon_big, big)
            if small:
                user32.SendMessageW(hwnd, wm_seticon, icon_small, small)
        except (AttributeError, OSError, TypeError):
            pass

    def _enable_native_resize(self) -> None:
        """Безрамочному окну нужен стиль WS_THICKFRAME, иначе система не тянет за края."""
        if sys.platform != "win32" or self._thick_frame:
            return
        try:
            user32 = ctypes.windll.user32
            user32.GetWindowLongPtrW.restype = ctypes.c_longlong
            user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
            user32.SetWindowLongPtrW.restype = ctypes.c_longlong
            user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_longlong]

            gwl_style = -16
            ws_thickframe = 0x00040000
            ws_minimizebox = 0x00020000
            ws_maximizebox = 0x00010000

            hwnd = wintypes.HWND(int(self.winId()))
            style = user32.GetWindowLongPtrW(hwnd, gwl_style)
            user32.SetWindowLongPtrW(
                hwnd,
                gwl_style,
                style | ws_thickframe | ws_minimizebox | ws_maximizebox,
            )
            self._thick_frame = True
        except (AttributeError, OSError, TypeError):
            self._thick_frame = False

    def nativeEvent(self, event_type, message):  # noqa: N802 — метод Qt
        """Безрамочное окно: ресайз за края силами Windows."""
        if sys.platform == "win32" and not self.isMaximized():
            try:
                msg = ctypes.cast(int(message), ctypes.POINTER(_WinMessage)).contents
            except (TypeError, ValueError):
                return super().nativeEvent(event_type, message)

            if msg.message == _WM_NCHITTEST:
                x = ctypes.c_short(msg.lParam & 0xFFFF).value
                y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
                point = self.mapFromGlobal(QPoint(x, y))
                left = point.x() < _RESIZE_MARGIN
                right = point.x() > self.width() - _RESIZE_MARGIN
                top = point.y() < _RESIZE_MARGIN
                bottom = point.y() > self.height() - _RESIZE_MARGIN

                if top and left:
                    return True, 13  # HTTOPLEFT
                if top and right:
                    return True, 14  # HTTOPRIGHT
                if bottom and left:
                    return True, 16  # HTBOTTOMLEFT
                if bottom and right:
                    return True, 17  # HTBOTTOMRIGHT
                if left:
                    return True, 10  # HTLEFT
                if right:
                    return True, 11  # HTRIGHT
                if top:
                    return True, 12  # HTTOP
                if bottom:
                    return True, 15  # HTBOTTOM

        return super().nativeEvent(event_type, message)

    def _build_history_row(self) -> QWidget:
        row = QFrame()
        row.setObjectName("Bar")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        self._back_button = self._icon_button("\u2190", tr("header.back"), "arrow-left")
        self._back_button.clicked.connect(self._history_back)
        layout.addWidget(self._back_button)

        self._forward_button = self._icon_button("\u2192", tr("header.forward"), "arrow-right")
        self._forward_button.clicked.connect(self._history_forward)
        layout.addWidget(self._forward_button)

        self._usage = QLabel()
        self._usage.setObjectName("Usage")
        layout.addWidget(self._usage)
        layout.addStretch(1)

        theme_button = self._ghost_button("\u25d0", tr("header.theme"), ("swatch-book", "sun", "palette"))
        theme_button.clicked.connect(self._show_theme_menu)
        self._theme_button = theme_button
        layout.addWidget(theme_button)

        document_button = self._ghost_button("\U0001f4c4", tr("header.document"), "file-text")
        document_button.clicked.connect(self._open_document)
        layout.addWidget(document_button)

        history_button = self._ghost_button("\U0001f551", tr("header.history"), ("history", "rotate-ccw-clock", "clock"))
        history_button.clicked.connect(self._open_history)
        layout.addWidget(history_button)

        settings_button = self._ghost_button("\u2699", tr("header.settings"), "settings")
        settings_button.clicked.connect(self._open_settings)
        layout.addWidget(settings_button)

        return row

    def _build_services_row(self) -> QWidget:
        row = QFrame()
        row.setObjectName("Bar")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(10)

        label = QLabel(tr("section.services"))
        label.setObjectName("SectionLabel")
        layout.addWidget(label)

        self._provider_bar = ProviderBar(
            translator_choices(self._registry), list(self._settings.enabled_providers)
        )
        self._provider_bar.changed.connect(self._on_providers_changed)
        layout.addWidget(self._provider_bar, 1)
        return row

    def _ghost_button(self, text: str, tooltip: str, icon_name: str = "") -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("Ghost")
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedWidth(34)
        self._attach_icon(button, icon_name)
        return button

    def _icon_button(self, text: str, tooltip: str, icon_name: str = "") -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("Icon")
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedWidth(32)
        self._attach_icon(button, icon_name)
        return button

    def _attach_icon(self, button: QPushButton, names) -> None:
        if not names:
            return
        if isinstance(names, str):
            names = (names,)
        self._icon_buttons.append((button, names))
        loaded = load_icon(names)
        if loaded is not None:
            button.setText("")
            button.setIcon(loaded)
            button.setIconSize(icon_size())

    def _apply_icons(self) -> None:
        set_icon_color(palette(self._settings.theme)["text"])
        for button, names in self._icon_buttons:
            loaded = load_icon(names)
            if loaded is not None:
                button.setIcon(loaded)

    def _build_input(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        top = QHBoxLayout()
        label = QLabel(tr("section.input"))
        label.setObjectName("SectionLabel")
        top.addWidget(label)
        top.addStretch(1)
        self._counter = QLabel()
        self._counter.setObjectName("Counter")
        top.addWidget(self._counter)
        layout.addLayout(top)

        editors = QHBoxLayout()
        editors.setSpacing(8)
        self._input = SpellTextEdit()
        self._input.setPlaceholderText(tr("input.placeholder"))
        self._input.setTabChangesFocus(True)
        self._input.textChanged.connect(self._on_text_changed)
        editors.addWidget(self._input, 1)

        side = QVBoxLayout()
        side.setSpacing(6)
        copy_input = self._icon_button("\U0001f4cb", tr("button.copy_input"), ("clipboard-copy", "clipboard"))
        copy_input.clicked.connect(self._copy_input)
        side.addWidget(copy_input)
        clear_input = self._icon_button("\U0001f5d1", tr("button.clear_input"), ("trash-2", "trash"))
        clear_input.clicked.connect(self._clear_input)
        side.addWidget(clear_input)
        side.addStretch(1)
        editors.addLayout(side)
        layout.addLayout(editors, 1)

        languages = QHBoxLayout()
        languages.setSpacing(8)
        clear_button = self._icon_button("\U0001f5d1", tr("button.clear"), ("trash-2", "trash"))
        clear_button.clicked.connect(self._clear)
        languages.addWidget(clear_button)

        self._language_bar = LanguageBar()
        self._language_bar.swapRequested.connect(self._language_bar.swap)
        self._language_bar.source_combo.currentIndexChanged.connect(self._on_languages_changed)
        self._language_bar.target_combo.currentIndexChanged.connect(self._on_languages_changed)
        languages.addWidget(self._language_bar, 1)

        self._translate_button = QPushButton(tr("button.translate"))
        self._translate_button.setObjectName("Primary")
        self._translate_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._translate_button.clicked.connect(lambda: self._start_translation())
        languages.addWidget(self._translate_button)
        layout.addLayout(languages)

        return container

    def _build_output(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel(tr("section.results"))
        label.setObjectName("SectionLabel")
        layout.addWidget(label)

        row = QHBoxLayout()
        row.setSpacing(8)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        holder = QWidget()
        self._results_layout = QVBoxLayout(holder)
        self._results_layout.setContentsMargins(2, 2, 2, 2)
        self._results_layout.setSpacing(10)
        self._scroll.setWidget(holder)
        row.addWidget(self._scroll, 1)

        side = QVBoxLayout()
        side.setSpacing(6)
        self._copy_button = self._icon_button("\U0001f4cb", tr("button.copy"), ("copy", "files"))
        self._copy_button.clicked.connect(self._copy_result)
        side.addWidget(self._copy_button)
        self._speak_button = self._icon_button("\U0001f50a", tr("button.speak"), ("volume-2", "volume"))
        self._speak_button.clicked.connect(self._toggle_speech)
        side.addWidget(self._speak_button)
        side.addStretch(1)
        row.addLayout(side)

        layout.addLayout(row, 1)
        return container

    def _build_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        segmented = QFrame()
        segmented.setObjectName("Segmented")
        segment_layout = QHBoxLayout(segmented)
        segment_layout.setContentsMargins(3, 3, 3, 3)
        segment_layout.setSpacing(3)

        self._backward_button = QPushButton(tr("panel.backward"))
        self._backward_button.setObjectName("Segment")
        self._backward_button.setCheckable(True)
        self._backward_button.setChecked(True)
        self._backward_button.clicked.connect(lambda: self._select_panel(_PANEL_BACKWARD))
        segment_layout.addWidget(self._backward_button)

        self._dictionary_button = QPushButton(tr("panel.dictionary"))
        self._dictionary_button.setObjectName("Segment")
        self._dictionary_button.setCheckable(True)
        self._dictionary_button.clicked.connect(lambda: self._select_panel(_PANEL_DICTIONARY))
        segment_layout.addWidget(self._dictionary_button)
        segment_layout.addStretch(1)

        top = QHBoxLayout()
        top.addWidget(segmented)
        layout.addLayout(top)

        self._panel_stack = QStackedWidget()

        backward_holder = QWidget()
        backward_layout = QVBoxLayout(backward_holder)
        backward_layout.setContentsMargins(0, 0, 0, 0)
        self._backward_scroll = QScrollArea()
        self._backward_scroll.setWidgetResizable(True)
        inner = QWidget()
        self._backward_layout = QVBoxLayout(inner)
        self._backward_layout.setContentsMargins(2, 2, 2, 2)
        self._backward_layout.setSpacing(8)
        self._backward_scroll.setWidget(inner)
        backward_layout.addWidget(self._backward_scroll)
        self._panel_stack.addWidget(backward_holder)

        self._dictionary_panel = DictionaryPanel()
        self._panel_stack.addWidget(self._dictionary_panel)

        layout.addWidget(self._panel_stack, 1)
        return container

    def _build_selectors(self) -> QWidget:
        row = QFrame()
        row.setObjectName("Toolbar")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self._primary_combo = self._selector(
            layout, tr("button.translate"), translator_choices(self._registry)
        )
        self._dictionary_combo = self._selector(
            layout, tr("settings.dictionary"), dictionary_choices(self._registry)
        )
        self._tts_combo = self._selector(
            layout, tr("settings.tts"), tts_choices(self._registry)
        )
        layout.addStretch(1)

        self._primary_combo.currentIndexChanged.connect(self._on_primary_changed)
        self._dictionary_combo.currentIndexChanged.connect(self._on_selector_changed)
        self._tts_combo.currentIndexChanged.connect(self._on_selector_changed)
        return row

    @staticmethod
    def _selector(layout: QHBoxLayout, title: str, options: list[tuple[str, str]]) -> QComboBox:
        box = QVBoxLayout()
        box.setSpacing(2)
        label = QLabel(title)
        label.setObjectName("SectionLabel")
        box.addWidget(label)
        combo = QComboBox()
        for value, name in options:
            combo.addItem(name, value)
        combo.setMinimumWidth(190)
        box.addWidget(combo)
        layout.addLayout(box)
        return combo

    def _hotkey_slots(self) -> dict:
        return {
            "translate": lambda: self._start_translation(),
            "copy_result": self._copy_result,
            "clear_input": self._clear_input,
            "swap_languages": self._language_bar.swap,
            "speak": self._toggle_speech,
            "dictionary": self._toggle_dictionary,
            "document": self._open_document,
            "ocr": self._start_ocr,
            "history": self._open_history,
            "settings": self._open_settings,
        }

    def _stop_hotkeys(self) -> None:
        for shortcut in self._shortcuts:
            shortcut.setEnabled(False)
            shortcut.deleteLater()
        self._shortcuts.clear()
        for hotkey in self._global_hotkeys:
            hotkey.stop()
        self._global_hotkeys.clear()

    def _apply_hotkeys(self) -> None:
        self._stop_hotkeys()

        slots = self._hotkey_slots()
        hotkey_id = 0x5200
        for action in ACTIONS:
            if action.id == "quick_translate":
                continue  # им занимается контроллер быстрого перевода
            slot = slots.get(action.id)
            sequence = binding(self._settings, action.id)
            if slot is None or not sequence:
                continue

            if scope(self._settings, action.id) == "global":
                parsed = combination(sequence)
                vk = virtual_key(parsed[0]) if parsed else None
                if parsed is None or vk is None:
                    continue
                _, ctrl, shift, alt, win = parsed
                hotkey_id += 1
                hotkey = GlobalHotkey(
                    vk, ctrl=ctrl, shift=shift, alt=alt, win=win, hotkey_id=hotkey_id
                )
                hotkey.activated.connect(slot)
                hotkey.start()
                self._global_hotkeys.append(hotkey)
                continue

            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(slot)
            self._shortcuts.append(shortcut)

        self.hotkeysChanged.emit()

    def _restore_state(self) -> None:
        self._language_bar.set_pair(
            self._settings.native_language, self._settings.second_language
        )
        self._language_bar.set_languages(
            self._settings.source_language, self._settings.target_language
        )
        self._select(self._primary_combo, self._settings.primary_provider)
        self._select(self._dictionary_combo, self._settings.dictionary_provider)
        self._select(self._tts_combo, self._settings.tts_provider)
        if self._settings.window_geometry:
            try:
                self.restoreGeometry(QByteArray.fromBase64(self._settings.window_geometry.encode()))
            except (ValueError, TypeError):
                pass
        if self._settings.splitter_sizes:
            try:
                self._splitter.setSizes([int(value) for value in self._settings.splitter_sizes])
            except (TypeError, ValueError):
                pass
        index = _PANEL_DICTIONARY if self._settings.panel_index == _PANEL_DICTIONARY else _PANEL_BACKWARD
        self._panel_stack.setCurrentIndex(index)
        self._backward_button.setChecked(index == _PANEL_BACKWARD)
        self._dictionary_button.setChecked(index == _PANEL_DICTIONARY)
        self._update_counter()
        self._update_usage()
        self._show_placeholder(tr("results.placeholder"))
        self._show_backward_placeholder()


    def _primary_provider(self) -> str:
        enabled = self._provider_bar.enabled_ids()
        preferred = self._settings.primary_provider
        if preferred in enabled:
            return preferred
        return enabled[0] if enabled else (preferred or "google")

    def _start_translation(self, silent: bool = False) -> None:
        text = self._input.toPlainText().strip()
        if not text:
            if not silent:
                self._status.showMessage(tr("status.enter_text"), 3000)
            return

        provider_ids = self._provider_bar.enabled_ids()
        if not provider_ids:
            self._status.showMessage(tr("status.no_services"), 4000)
            return

        if len(text) > self._settings.max_chars:
            text = text[: self._settings.max_chars]
            self._input.blockSignals(True)
            self._input.setPlainText(text)
            self._input.blockSignals(False)
            self._status.showMessage(tr("status.truncated", limit=self._settings.max_chars), 4000)

        source = self._language_bar.source()
        target = self._language_bar.target()
        self._pending = (text, source, target)

        self._token += 1
        self._set_busy(True)
        self._status.showMessage(tr("status.translating"))

        worker = TranslateWorker(
            self._service,
            self._token,
            text,
            source,
            target,
            provider_ids,
            native=self._settings.native_language or None,
            second=self._settings.second_language or None,
        )
        worker.signals.finished.connect(self._on_results)
        worker.signals.failed.connect(self._on_failed)
        self._active_worker = worker
        self._pool.start(worker)

    def _on_results(self, token: int, results: list[TranslationResult]) -> None:
        if token != self._token:
            return
        self._set_busy(False)
        self._render_results(results)

        successful = [r for r in results if r.ok]
        if not successful:
            self._status.showMessage(tr("status.no_translation"), 6000)
            return

        best = successful[0]
        self._last_result_text = best.text
        source_text, source, target = self._pending
        effective_source = best.detected_source or source
        effective_target = self._effective_target(effective_source, target)
        self._history.add(
            HistoryEntry(
                source_text=source_text,
                translated_text=best.text,
                source_language=effective_source,
                target_language=effective_target,
                provider_id=best.provider_id,
                provider_name=best.provider_name,
            )
        )
        self._history_index = 0
        self._status.showMessage(
            tr("status.done", ok=len(successful), total=len(results), provider=best.provider_name),
            6000,
        )
        self._update_usage(effective_source, effective_target)
        self._refresh_backward()

    def _effective_target(self, source_language: str, target: str) -> str:
        """Для авто-пары выбираем второй или родной язык по определённому источнику."""
        if target != AUTO_PAIR:
            return target
        native = self._settings.native_language
        second = self._settings.second_language
        return second if source_language == native else native

    def _on_failed(self, token: int, message: str) -> None:
        if token != self._token:
            return
        self._set_busy(False)
        self._status.showMessage(tr("status.error", message=message), 6000)

    def _set_busy(self, busy: bool) -> None:
        self._translate_button.setEnabled(not busy)
        self._translate_button.setText(tr("button.translating") if busy else tr("button.translate"))
        self._loading.set_loading(busy)

    def _copy_input(self) -> None:
        text = self._input.toPlainText()
        if text:
            self._app.clipboard().setText(text)
            self._status.showMessage(tr("status.copied"), 2000)

    def _copy_result(self) -> None:
        for index in range(self._results_layout.count()):
            widget = self._results_layout.itemAt(index).widget()
            if isinstance(widget, ResultCard) and widget.result.ok:
                self._app.clipboard().setText(widget.result.text)
                self._status.showMessage(tr("status.copied"), 3000)
                return
        self._status.showMessage(tr("status.nothing_to_copy"), 3000)

    def _clear_input(self) -> None:
        self._input.clear()

    def _clear(self) -> None:
        self._input.clear()
        self._show_placeholder(tr("results.placeholder"))
        self._show_backward_placeholder()
        self._last_result_text = ""
        self._status.showMessage(tr("status.cleared"), 2000)

    def _on_text_changed(self) -> None:
        self._update_counter()
        if self._settings.translate_on_type:
            self._debounce.start()

    def _apply_spellcheck(self) -> None:
        source = self._language_bar.source()
        if source == AUTO:
            self._input.set_spellcheck(False, "")
            return
        self._input.set_spellcheck(self._settings.spellcheck_enabled, source)

    def _on_languages_changed(self) -> None:
        self._apply_spellcheck()
        self._update_usage()
        self._persist()

    def _start_ocr(self) -> None:
        if self._ocr_overlay is not None:
            return
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if screen is None:
            return
        overlay = OcrOverlay(screen)
        overlay.selected.connect(lambda rect: self._capture_ocr(screen, rect))
        overlay.cancelled.connect(self._close_ocr_overlay)
        self._ocr_overlay = overlay
        overlay.start()

    def _close_ocr_overlay(self) -> None:
        overlay = self._ocr_overlay
        self._ocr_overlay = None
        if overlay is not None:
            overlay.hide()
            overlay.deleteLater()

    def _capture_ocr(self, screen, rect: QRect) -> None:
        self._close_ocr_overlay()
        QTimer.singleShot(120, lambda: self._recognize_region(screen, rect))

    def _recognize_region(self, screen, rect: QRect) -> None:
        image = capture_region(screen, rect)
        if image.isNull():
            self._status.showMessage(tr("ocr.failed", message=tr("errors.bad_response")), 4000)
            return

        handle, name = tempfile.mkstemp(suffix=".png")
        os.close(handle)
        path = Path(name)
        if not image.save(str(path), "PNG"):
            path.unlink(missing_ok=True)
            self._status.showMessage(tr("ocr.failed", message=tr("errors.bad_response")), 4000)
            return

        source = self._language_bar.source()
        if source == AUTO:
            source = self._settings.native_language

        self._ocr_token += 1
        worker = OcrWorker(self._ocr_token, path, source)
        worker.signals.finished.connect(self._on_ocr_done)
        worker.signals.failed.connect(self._on_ocr_failed)
        self._ocr_worker = worker
        self._status.showMessage(tr("ocr.recognizing"))
        self._pool.start(worker)

    def _on_ocr_done(self, token: int, text: str, language: str) -> None:
        if token != self._ocr_token:
            return
        self._ocr_worker = None
        text = text.strip()
        if not text:
            self._status.showMessage(tr("ocr.empty"), 4000)
            return
        self._restore_from_tray()
        self._input.setPlainText(text)
        self._start_translation()

    def _on_ocr_failed(self, token: int, message: str) -> None:
        if token != self._ocr_token:
            return
        self._ocr_worker = None
        self._status.showMessage(message, 6000)

    def _on_providers_changed(self) -> None:
        self._update_usage()
        self._persist()

    def _on_primary_changed(self) -> None:
        self._settings.primary_provider = self._primary_combo.currentData() or ""
        self._update_usage()
        self._persist()

    def _on_selector_changed(self) -> None:
        self._settings.dictionary_provider = self._dictionary_combo.currentData() or ""
        self._settings.tts_provider = self._tts_combo.currentData() or ""
        self._persist()

    def _update_counter(self) -> None:
        self._counter.setText(
            tr("input.counter", count=len(self._input.toPlainText()), limit=self._settings.max_chars)
        )

    def _update_usage(self, detected: str | None = None, target: str | None = None) -> None:
        provider_id = self._primary_provider()
        service = self._registry.get(provider_id)
        provider_name = service.name if service is not None else "—"
        source = self._language_bar.source()
        if source == AUTO:
            source = detected or "auto"

        target = target or self._language_bar.target()
        if target == AUTO_PAIR and self._settings.native_language and self._settings.second_language:
            target_text = pair_label(self._settings.native_language, self._settings.second_language)
        else:
            target_text = language_name(target)

        self._usage.setText(
            tr(
                "usage.text",
                provider=provider_name,
                source=language_name(source),
                target=target_text,
            )
        )


    def _toggle_speech(self) -> None:
        if self._speech.is_playing():
            self._speech.stop()
            return
        text, language = self._speech_target()
        if not text:
            self._status.showMessage(tr("status.nothing_to_speak"), 3000)
            return
        self._speech.speak(text, language)

    def _speech_target(self) -> tuple[str, str]:
        target = self._language_bar.target()
        if self._last_result_text:
            return self._last_result_text, target
        source = self._language_bar.source()
        return self._input.toPlainText().strip(), source if source != AUTO else "en"

    def _on_speech_state(self, playing: bool) -> None:
        if self._speak_button.icon().isNull():
            self._speak_button.setText("\u23f9" if playing else "\U0001f50a")


    def _select_panel(self, index: int) -> None:
        index = _PANEL_DICTIONARY if index == _PANEL_DICTIONARY else _PANEL_BACKWARD
        self._panel_stack.setCurrentIndex(index)
        self._backward_button.setChecked(index == _PANEL_BACKWARD)
        self._dictionary_button.setChecked(index == _PANEL_DICTIONARY)
        self._settings.panel_index = index
        if index == _PANEL_BACKWARD:
            self._refresh_backward()
        elif index == _PANEL_DICTIONARY:
            self._lookup_dictionary()

    def _refresh_backward(self) -> None:
        if self._panel_stack.currentIndex() != _PANEL_BACKWARD:
            return
        if not self._last_result_text:
            self._show_backward_placeholder()
            return

        source = self._language_bar.source()
        if source == AUTO:
            source = "en"
        self._show_backward_message(tr("panel.backward_loading"))

        self._backward_token += 1
        worker = TranslateWorker(
            self._service,
            self._backward_token,
            self._last_result_text,
            self._language_bar.target(),
            source,
            [self._primary_provider()],
        )
        worker.signals.finished.connect(self._on_backward)
        worker.signals.failed.connect(lambda *_: self._show_backward_message(tr("popup.failed")))
        self._backward_worker = worker
        self._pool.start(worker)

    def _on_backward(self, token: int, results: list[TranslationResult]) -> None:
        if token != self._backward_token:
            return
        best = next((result for result in results if result.ok), None)
        if best is None:
            message = results[0].error if results else tr("popup.failed")
            self._show_backward_message(message or tr("popup.failed"))
            return
        self._render_backward(best)

    def _show_backward_placeholder(self) -> None:
        self._clear_backward()
        label = QLabel(tr("panel.backward_placeholder"))
        label.setObjectName("EmptyState")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._backward_layout.addStretch(1)
        self._backward_layout.addWidget(label)
        self._backward_layout.addStretch(1)

    def _show_backward_message(self, text: str) -> None:
        self._clear_backward()
        label = QLabel(text)
        label.setObjectName("CardMeta")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._backward_layout.addStretch(1)
        self._backward_layout.addWidget(label)
        self._backward_layout.addStretch(1)

    def _render_backward(self, result: TranslationResult) -> None:
        self._clear_backward()
        self._backward_layout.addWidget(ResultCard(result))
        self._backward_layout.addStretch(1)

    def _clear_backward(self) -> None:
        while self._backward_layout.count():
            item = self._backward_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()


    def _toggle_dictionary(self) -> None:
        if (
            self._panel_stack.currentIndex() == _PANEL_DICTIONARY
            and self._dictionary_panel.isVisible()
        ):
            self._select_panel(_PANEL_BACKWARD)
            return
        self._select_panel(_PANEL_DICTIONARY)

    def _lookup_dictionary(self) -> None:
        word, language = self._dictionary_target()
        if not word:
            self._dictionary_panel.show_error(tr("dict.select_word"))
            return
        service = dictionary_service(self._registry, self._settings.dictionary_provider)
        if service is None:
            self._dictionary_panel.show_error(tr("dict.no_service"))
            return

        self._dictionary_pending = (word, language)
        self._dictionary_token += 1
        self._dictionary_panel.show_loading(word, language)

        worker = DictionaryWorker(
            service, self._dictionary_token, word, language, self._language_bar.target()
        )
        worker.signals.finished.connect(self._on_dictionary_results)
        worker.signals.failed.connect(self._on_dictionary_failed)
        self._dictionary_worker = worker
        self._pool.start(worker)

    def _dictionary_target(self) -> tuple[str, str]:
        selected = self._input.textCursor().selectedText().strip()
        if selected:
            return selected.split()[0], self._resolved_source_language()

        text = self._input.toPlainText().strip()
        if not text:
            text = self._last_result_text
        if not text:
            return "", "en"
        return text.split()[0].strip(".,!?;:()[]\"'«»"), self._resolved_source_language()

    def _resolved_source_language(self) -> str:
        source = self._language_bar.source()
        if source != AUTO:
            return source
        for index in range(self._results_layout.count()):
            widget = self._results_layout.itemAt(index).widget()
            if isinstance(widget, ResultCard) and widget.result.detected_source:
                return widget.result.detected_source
        return "en"

    def _on_dictionary_results(self, token: int, entries: list[DictionaryEntry]) -> None:
        if token != self._dictionary_token:
            return
        word, language = self._dictionary_pending
        entries = list(entries)
        self._dictionary_panel.show_entries(word, language, entries)
        self._status.showMessage(
            tr("status.dictionary_found", count=len(entries))
            if entries
            else tr("status.dictionary_empty"),
            4000,
        )

    def _on_dictionary_failed(self, token: int, message: str) -> None:
        if token != self._dictionary_token:
            return
        self._dictionary_panel.show_error(message)


    def _render_results(self, results: list[TranslationResult]) -> None:
        self._clear_results()
        if not results:
            self._results_layout.addStretch(1)
            return
        for result in results:
            self._results_layout.addWidget(ResultCard(result))
        self._results_layout.addStretch(1)

    def _show_placeholder(self, text: str) -> None:
        self._clear_results()
        label = QLabel(text)
        label.setObjectName("EmptyState")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        self._results_layout.addStretch(1)
        self._results_layout.addWidget(label)
        self._results_layout.addStretch(1)

    def _clear_results(self) -> None:
        while self._results_layout.count():
            item = self._results_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()


    def _history_back(self) -> None:
        entries = self._history.entries
        if self._history_index + 1 >= len(entries):
            self._status.showMessage(tr("status.nothing_to_copy"), 2000)
            return
        self._history_index += 1
        self._restore_entry(entries[self._history_index])

    def _history_forward(self) -> None:
        if self._history_index <= 0:
            return
        self._history_index -= 1
        if self._history_index == 0 and self._history.entries:
            self._restore_entry(self._history.entries[0])
            return
        self._restore_entry(self._history.entries[self._history_index])

    def _restore_entry(self, entry: HistoryEntry) -> None:
        self._input.setPlainText(entry.source_text)
        self._language_bar.set_languages(entry.source_language or AUTO, entry.target_language or "en")
        self._last_result_text = entry.translated_text
        self._render_results(
            [
                TranslationResult(
                    provider_id=entry.provider_id,
                    provider_name=entry.provider_name,
                    text=entry.translated_text,
                )
            ]
        )
        self._refresh_backward()
        self._status.showMessage(tr("status.history_restored"), 4000)


    def _open_history(self) -> None:
        dialog = HistoryDialog(self._history, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        entry = dialog.selected_entry()
        if entry is not None:
            self._restore_entry(entry)

    def _open_document(self) -> None:
        provider_ids = self._provider_bar.enabled_ids()
        if not provider_ids:
            self._status.showMessage(tr("status.no_services"), 4000)
            return
        dialog = DocumentDialog(
            service=self._service,
            registry=self._registry,
            source=self._language_bar.source(),
            target=self._language_bar.target(),
            provider_id=self._primary_provider(),
            parent=self,
        )
        dialog.exec()

    def _open_settings(self) -> None:
        dialog = SettingsDialog(
            self._settings,
            tts_choices(self._registry),
            dictionary_choices(self._registry),
            self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        language_changed = values.get("interface_language") != self._settings.interface_language
        for key, value in values.items():
            setattr(self._settings, key, value)
        self._apply_settings()
        if language_changed:
            self._status.showMessage(tr("status.language_restart"), 6000)

    def _apply_settings(self) -> None:
        apply_theme(self._app, self._settings.theme)
        self._apply_icons()
        self._app.setFont(QFont("Segoe UI", int(self._settings.font_size)))
        configure_registry(self._registry, self._settings)
        self._language_bar.set_pair(
            self._settings.native_language, self._settings.second_language
        )
        self._select(self._dictionary_combo, self._settings.dictionary_provider)
        self._select(self._tts_combo, self._settings.tts_provider)
        self._apply_spellcheck()
        self._update_counter()
        self._apply_hotkeys()
        self._persist()

    def _build_theme_menu(self) -> QMenu:
        menu = QMenu(self)
        for theme in ("metal", "turquoise", "bronze", "light"):
            action = menu.addAction(tr(f"settings.theme.{theme}"))
            action.setCheckable(True)
            action.setChecked(self._settings.theme == theme)
            action.triggered.connect(lambda _checked=False, name=theme: self._set_theme(name))
        return menu

    def _show_theme_menu(self) -> None:
        menu = self._build_theme_menu()
        menu.exec(self._theme_button.mapToGlobal(self._theme_button.rect().bottomLeft()))

    def _set_theme(self, theme: str) -> None:
        self._settings.theme = theme
        apply_theme(self._app, theme)
        self._apply_icons()
        self._persist()
        self._status.showMessage(tr(f"settings.theme.{theme}"), 2000)

    @staticmethod
    def _select(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)


    def _persist(self) -> None:
        self._settings.source_language = self._language_bar.source()
        self._settings.target_language = self._language_bar.target()
        self._settings.enabled_providers = self._provider_bar.enabled_ids()
        self._settings.primary_provider = self._primary_combo.currentData() or ""
        self._settings.dictionary_provider = self._dictionary_combo.currentData() or ""
        self._settings.tts_provider = self._tts_combo.currentData() or ""
        if self._splitter is not None:
            self._settings.splitter_sizes = list(self._splitter.sizes())
        self._settings.save(self._settings_path)

    def closeEvent(self, event) -> None:  # noqa: N802 — метод Qt
        self._settings.window_geometry = bytes(self.saveGeometry().toBase64()).decode()
        self._persist()
        super().closeEvent(event)
