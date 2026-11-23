"""FilePicker: path display + browse button."""

from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QEvent, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class FilePickerMode(Enum):
    """The dialog type opened by FilePicker."""

    OPEN_FILE = "open_file"
    OPEN_DIRECTORY = "open_directory"
    SAVE_FILE = "save_file"


class FilePicker(QWidget):
    """Label + read-only path field + browse button.

    Consumers interact through ``label``, ``path``, ``set_path``, ``clear``
    and the ``path_changed`` signal. The internal browse button is an
    implementation detail.
    """

    path_changed = Signal(str)

    def __init__(
        self,
        label: str = "",
        mode: FilePickerMode = FilePickerMode.OPEN_FILE,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._mode = mode

        self._label = QLabel(label, self)
        self._label.setObjectName("CraniozFilePickerLabel")

        self._path_edit = QLineEdit(self)
        self._path_edit.setObjectName("CraniozFilePickerPath")
        self._path_edit.setReadOnly(True)

        self._browse_button = QToolButton(self)
        self._browse_button.setObjectName("CraniozFilePickerBrowse")
        self._browse_button.setProperty("class", "secondary")
        self._browse_button.setText("…")
        self._browse_button.setToolTip(self.tr("Browse…"))
        self._browse_button.setFixedWidth(32)
        self._browse_button.clicked.connect(self._on_browse)

        path_row = QHBoxLayout()
        path_row.setContentsMargins(0, 0, 0, 0)
        path_row.setSpacing(4)
        path_row.addWidget(self._path_edit, 1)
        path_row.addWidget(self._browse_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self._label)
        layout.addLayout(path_row)

        self.setAccessibleName(label or "File picker")

    # ---- internals ---------------------------------------------------
    def _on_browse(self) -> None:
        current = self._path_edit.text()
        if self._mode is FilePickerMode.OPEN_DIRECTORY:
            path = QFileDialog.getExistingDirectory(self, self.tr("Select folder"), current)
        elif self._mode is FilePickerMode.SAVE_FILE:
            path, _ = QFileDialog.getSaveFileName(self, self.tr("Save file"), current)
        else:
            path, _ = QFileDialog.getOpenFileName(self, self.tr("Open file"), current)
        if path:
            self.set_path(path)

    # ---- properties --------------------------------------------------
    @property
    def mode(self) -> FilePickerMode:
        return self._mode

    @property
    def path(self) -> str:
        return self._path_edit.text()

    @path.setter
    def path(self, value: str) -> None:
        self.set_path(value)

    @property
    def label(self) -> str:
        return self._label.text()

    @label.setter
    def label(self, value: str) -> None:
        self._label.setText(value)
        self.setAccessibleName(value or "File picker")

    # ---- public methods ---------------------------------------------
    def set_path(self, path: str) -> None:
        if path == self._path_edit.text():
            return
        self._path_edit.setText(path)
        self.path_changed.emit(path)

    def clear(self) -> None:
        self.set_path("")

    # ---- i18n --------------------------------------------------------
    def changeEvent(self, event: QEvent) -> None:  # noqa: N802
        if event.type() == QEvent.Type.LanguageChange:
            self._browse_button.setToolTip(self.tr("Browse…"))
            self.setAccessibleName(self._label.text() or "File picker")
        super().changeEvent(event)
