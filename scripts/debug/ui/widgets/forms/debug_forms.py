"""Visual debug harness for L.0 form widgets.

Run with::

    .venv\\Scripts\\python.exe scripts/debug/ui/forms/debug_forms.py

This is a manual inspection tool, not a test. It renders the four L.0
widgets side by side, with controls to toggle:

- theme (dark / light)
- language placeholder (visual only; real i18n requires catalog entries)

The script does not depend on the ThemeService (L.0 widgets do not
accept one). It applies the compiled QSS globally via ThemeCompiler so
the widgets inherit the theme through the global stylesheet, mirroring
production behavior.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cranioz.infrastructure.settings.in_memory_settings_service import (
    InMemorySettingsService,
)
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.theme.tokens import ThemeMode, ThemeName
from cranioz.ui.widgets.forms import (
    FilePicker,
    FilePickerMode,
    FormCombo,
    FormField,
    SignaturePreview,
)


def _make_signature_pixmap() -> QPixmap:
    """A simple non-empty pixmap so SignaturePreview has something to show."""
    pix = QPixmap(320, 120)
    pix.fill(Qt.GlobalColor.white)
    return pix


class DebugWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CranioZ — L.0 Form Widgets Visual Debug")
        self.resize(720, 620)

        self._theme_service = ThemeService(
            settings=InMemorySettingsService(),
            default_mode=ThemeMode.DARK,
        )

        # --- widgets under test -------------------------------------
        self._form_field = FormField(label="Full name")
        self._form_field.placeholder = "e.g. Alice Silva"

        self._form_combo = FormCombo(label="Role")
        self._form_combo.add_items(
            [("Doctor", "doc"), ("Assistant", "asst"), ("Admin", "adm")]
        )

        self._file_picker_open = FilePicker(
            label="Profile picture",
            mode=FilePickerMode.OPEN_FILE,
        )
        self._file_picker_dir = FilePicker(
            label="Working directory",
            mode=FilePickerMode.OPEN_DIRECTORY,
        )

        self._signature_empty = SignaturePreview()

        self._signature_filled = SignaturePreview()
        self._signature_filled.set_signature(_make_signature_pixmap())

        # --- controls ----------------------------------------------
        self._theme_combo = QComboBox()
        self._theme_combo.addItem("Dark", ThemeName.DARK)
        self._theme_combo.addItem("Light", ThemeName.LIGHT)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)

        toggle_signature_button = QPushButton("Toggle empty ↔ filled")
        toggle_signature_button.clicked.connect(self._toggle_signature)

        # --- layout ------------------------------------------------
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Theme:"))
        controls.addWidget(self._theme_combo)
        controls.addStretch(1)
        controls.addWidget(toggle_signature_button)

        left = QVBoxLayout()
        left.addWidget(self._form_field)
        left.addWidget(self._form_combo)
        left.addWidget(self._file_picker_open)
        left.addWidget(self._file_picker_dir)
        left.addStretch(1)

        right = QVBoxLayout()
        right.addWidget(QLabel("Signature — empty state:"))
        right.addWidget(self._signature_empty)
        right.addWidget(QLabel("Signature — filled state:"))
        right.addWidget(self._signature_filled)
        right.addStretch(1)

        body = QHBoxLayout()
        body.addLayout(left, 1)
        body.addLayout(right, 1)

        root = QVBoxLayout(self)
        root.addLayout(controls)
        root.addLayout(body, 1)

        self._apply_theme(self._theme_service.theme())

    # ---- handlers ------------------------------------------------
    def _on_theme_changed(self) -> None:
        theme_name = self._theme_combo.currentData()
        mode = (
            ThemeMode.DARK if theme_name is ThemeName.DARK else ThemeMode.LIGHT
        )
        self._theme_service.set_mode(mode)
        self._apply_theme(self._theme_service.theme())

    def _apply_theme(self, _theme: ThemeName) -> None:
        # Re-apply the compiled QSS. ThemeService.set_mode already calls
        # ThemeCompiler.apply() internally, so this is a no-op the first
        # time and a repaint trigger afterwards.
        self._theme_service.compiler().apply(self._theme_service.compiled())

    def _toggle_signature(self) -> None:
        empty_has = self._signature_empty.has_signature
        filled_has = self._signature_filled.has_signature
        if empty_has or filled_has:
            self._signature_empty.clear()
            self._signature_filled.clear()
        else:
            self._signature_empty.set_signature(_make_signature_pixmap())
            self._signature_filled.set_signature(_make_signature_pixmap())


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = DebugWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())