"""Диалог перевода документа."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...core.documents import DocumentTranslator, output_extension, supported_extensions
from ...core.setup import translator_choices
from ...core.translation import TranslationService
from ...domain.language import all_languages
from ...localization import tr
from ...services.registry import ServiceRegistry
from ..sizing import lock_button_widths
from ..workers import DocumentWorker


class DocumentDialog(QDialog):
    def __init__(
        self,
        *,
        service: TranslationService,
        registry: ServiceRegistry,
        source: str,
        target: str,
        provider_id: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._registry = registry
        self._pool = QThreadPool.globalInstance()
        self._worker: DocumentWorker | None = None

        self.setWindowTitle(tr("document.title"))
        self.resize(560, 380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self._input = QLineEdit()
        self._input.setPlaceholderText(tr("document.choose_file"))
        input_row = QHBoxLayout()
        input_row.addWidget(self._input, 1)
        input_button = QPushButton(tr("document.browse"))
        input_button.clicked.connect(self._choose_input)
        input_row.addWidget(input_button)
        form.addRow(tr("document.file"), self._row(input_row))

        self._output = QLineEdit()
        self._output.setPlaceholderText(tr("document.choose_output"))
        output_row = QHBoxLayout()
        output_row.addWidget(self._output, 1)
        output_button = QPushButton(tr("document.browse"))
        output_button.clicked.connect(self._choose_output)
        output_row.addWidget(output_button)
        form.addRow(tr("document.result"), self._row(output_row))

        self._source = QComboBox()
        for language in all_languages(include_auto=True):
            self._source.addItem(language.name, language.code)
        self._select(self._source, source)
        form.addRow(tr("document.from"), self._source)

        self._target = QComboBox()
        for language in all_languages(include_auto=False):
            self._target.addItem(language.name, language.code)
        self._select(self._target, target)
        form.addRow(tr("document.to"), self._target)

        self._provider = QComboBox()
        for service_id, name in translator_choices(registry):
            self._provider.addItem(name, service_id)
        self._select(self._provider, provider_id)
        form.addRow(tr("document.provider"), self._provider)

        layout.addLayout(form)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        layout.addWidget(self._progress)

        self._status = QLabel(
            tr("document.supported", formats=", ".join(supported_extensions()))
        )
        self._status.setObjectName("CardMeta")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)
        layout.addStretch(1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self._start_button = QPushButton(tr("document.translate"))
        self._start_button.setObjectName("Primary")
        self._start_button.clicked.connect(self._start)
        buttons.addWidget(self._start_button)

        self._close_button = QPushButton(tr("document.close"))
        self._close_button.clicked.connect(self._on_close)
        buttons.addWidget(self._close_button)
        layout.addLayout(buttons)
        lock_button_widths(self)


    @staticmethod
    def _row(layout: QHBoxLayout) -> QWidget:
        widget = QWidget()
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget

    @staticmethod
    def _select(combo: QComboBox, code: str) -> None:
        index = combo.findData(code)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _choose_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr("document.choose_file"), "", tr("document.filter"))
        if not path:
            return
        self._input.setText(path)
        if not self._output.text().strip():
            source = Path(path)
            self._output.setText(
                str(source.with_name(f"{source.stem}_translated{output_extension(source.suffix)}"))
            )

    def _choose_output(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, tr("document.choose_output"), self._output.text(), tr("document.filter")
        )
        if path:
            self._output.setText(path)


    def _start(self) -> None:
        input_path = Path(self._input.text().strip())
        output_path = Path(self._output.text().strip())
        if not input_path.is_file():
            self._status.setText(tr("document.choose_existing"))
            return
        if not output_path.name:
            self._status.setText(tr("document.set_output"))
            return

        translator = DocumentTranslator(self._service, self._provider.currentData())
        worker = DocumentWorker(
            translator,
            input_path,
            output_path,
            self._source.currentData(),
            self._target.currentData(),
        )
        worker.signals.progress.connect(self._on_progress)
        worker.signals.finished.connect(self._on_finished)
        worker.signals.failed.connect(self._on_failed)
        worker.signals.cancelled.connect(self._on_cancelled)

        self._worker = worker
        self._set_running(True)
        self._status.setText(tr("document.translating"))
        self._pool.start(worker)

    def _on_progress(self, done: int, total: int, stage: str) -> None:
        self._progress.setValue(int(done / total * 100) if total else 0)
        self._status.setText(
            tr("document.progress", stage=tr(f"stage.{stage}"), done=done, total=total)
        )

    def _on_finished(self, path: str) -> None:
        self._set_running(False)
        self._progress.setValue(100)
        self._status.setText(tr("document.done", path=path))

    def _on_failed(self, message: str) -> None:
        self._set_running(False)
        self._status.setText(tr("document.error", message=message))

    def _on_cancelled(self) -> None:
        self._set_running(False)
        self._status.setText(tr("document.cancelled"))

    def _set_running(self, running: bool) -> None:
        self._start_button.setEnabled(not running)
        self._close_button.setText(tr("document.cancel") if running else tr("document.close"))

    def _on_close(self) -> None:
        if self._worker is not None and not self._start_button.isEnabled():
            self._worker.cancel()
            return
        self.reject()
