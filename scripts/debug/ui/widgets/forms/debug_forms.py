"""Visual debug harness for L.0 and L.0.2 form widgets.

Run with::

    .venv\\Scripts\\python.exe scripts/debug/ui/widgets/forms/debug_forms.py

This is a manual inspection tool, not a test. It renders L.0 widgets and
L.0.2 Delivery A widgets side by side, with controls to toggle:

- theme (dark / light)
- language placeholder (visual only; real i18n requires catalog entries)

The script does not depend on the ThemeService for the L.0 widgets (they
do not accept one). It applies the compiled QSS globally via ThemeCompiler
so the widgets inherit the theme through the global stylesheet, mirroring
production behavior. L.0.2 widgets that accept an ``IconProvider`` receive
a ``UnicodeIconProvider`` backed by the same ``ThemeService`` so their
icons follow the active theme.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import QDate, Qt, QTimer
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
from cranioz.ui.icons.unicode import UnicodeIconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.theme.tokens import ThemeMode, ThemeName
from cranioz.ui.widgets.advanced import ProgressBar, SearchField
from cranioz.ui.widgets.forms import (
    DateField,
    FilePicker,
    FilePickerMode,
    FormCombo,
    FormField,
    FormRow,
    SignaturePreview,
)
from cranioz.ui.widgets.lists import DragHandle
from cranioz.ui.widgets.navigation import (
    EyeToggleButton,
    VisibilityToggle,
)


def _make_signature_pixmap() -> QPixmap:
    """A simple non-empty pixmap so SignaturePreview has something to show."""
    pix = QPixmap(320, 120)
    pix.fill(Qt.GlobalColor.white)
    return pix


class DebugWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CranioZ — L.0 / L.0.2 Form Widgets Visual Debug")
        self.resize(960, 900)

        self._theme_service = ThemeService(
            settings=InMemorySettingsService(),
            default_mode=ThemeMode.DARK,
        )
        self._icon_provider = UnicodeIconProvider(theme_service=self._theme_service)

        # --- L.0 widgets under test --------------------------------
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

        # --- L.0.2 Delivery A widgets ------------------------------
        self._date_field = DateField(
            label="Appointment date",
            date=QDate.currentDate(),
        )

        self._row_left = FormField(label="City")
        self._row_left.placeholder = "e.g. São Paulo"
        self._row_right = FormField(label="State")
        self._row_right.placeholder = "e.g. SP"
        self._form_row = FormRow()
        self._form_row.add_field(self._row_left, stretch=2)
        self._form_row.add_field(self._row_right, stretch=1)

        self._drag_handle_with_icon = DragHandle(
            icon_provider=self._icon_provider
        )
        self._drag_handle_plain = DragHandle()

        self._eye_toggle = EyeToggleButton(self._icon_provider)

        self._visibility_toggle = VisibilityToggle("Show Agenda tab")

        self._search_field = SearchField(
            self._icon_provider,
            placeholder="Search patients…",
        )
        self._search_status = QLabel("Search: —")
        self._search_field.search_requested.connect(
            lambda text: self._search_status.setText(f"Search: {text or '—'}")
        )

        self._progress_bar = ProgressBar()
        self._progress_bar.setValue(35)
        self._progress_bar_label = QLabel("Progress: 35% (determinate)")
        self._progress_mode_combo = QComboBox()
        self._progress_mode_combo.addItem("Determinate", False)
        self._progress_mode_combo.addItem("Indeterminate", True)
        self._progress_mode_combo.currentIndexChanged.connect(
            self._on_progress_mode_changed
        )
        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(250)
        self._progress_timer.timeout.connect(self._advance_progress)
        self._progress_timer.start()

        # --- shared controls ---------------------------------------
        self._theme_combo = QComboBox()
        self._theme_combo.addItem("Dark", ThemeName.DARK)
        self._theme_combo.addItem("Light", ThemeName.LIGHT)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)

        toggle_signature_button = QPushButton("Toggle empty ↔ filled")
        toggle_signature_button.clicked.connect(self._toggle_signature)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Theme:"))
        controls.addWidget(self._theme_combo)
        controls.addStretch(1)
        controls.addWidget(toggle_signature_button)

        # --- L.0 section -------------------------------------------
        l0_left = QVBoxLayout()
        l0_left.addWidget(QLabel("— L.0: FormField / FormCombo / FilePicker —"))
        l0_left.addWidget(self._form_field)
        l0_left.addWidget(self._form_combo)
        l0_left.addWidget(self._file_picker_open)
        l0_left.addWidget(self._file_picker_dir)
        l0_left.addStretch(1)

        l0_right = QVBoxLayout()
        l0_right.addWidget(QLabel("— L.0: SignaturePreview —"))
        l0_right.addWidget(QLabel("Empty state:"))
        l0_right.addWidget(self._signature_empty)
        l0_right.addWidget(QLabel("Filled state:"))
        l0_right.addWidget(self._signature_filled)
        l0_right.addStretch(1)

        l0_body = QHBoxLayout()
        l0_body.addLayout(l0_left, 1)
        l0_body.addLayout(l0_right, 1)

        # --- L.0.2 Delivery A section ------------------------------
        d_a_left = QVBoxLayout()
        d_a_left.addWidget(QLabel("— L.0.2 A: DateField / FormRow —"))
        d_a_left.addWidget(self._date_field)
        d_a_left.addWidget(self._form_row)
        d_a_left.addWidget(QLabel("— L.0.2 A: DragHandle —"))
        drag_row = QHBoxLayout()
        drag_row.addWidget(self._drag_handle_with_icon)
        drag_row.addWidget(QLabel("with icon provider"))
        drag_row.addSpacing(16)
        drag_row.addWidget(self._drag_handle_plain)
        drag_row.addWidget(QLabel("without provider (text fallback)"))
        drag_row.addStretch(1)
        d_a_left.addLayout(drag_row)
        d_a_left.addWidget(QLabel("— L.0.2 A: EyeToggleButton —"))
        eye_row = QHBoxLayout()
        eye_row.addWidget(self._eye_toggle)
        eye_row.addWidget(
            QLabel("toggle to flip icon and accessibleName")
        )
        eye_row.addStretch(1)
        d_a_left.addLayout(eye_row)
        d_a_left.addWidget(QLabel("— L.0.2 A: VisibilityToggle —"))
        d_a_left.addWidget(self._visibility_toggle)
        d_a_left.addStretch(1)

        d_a_right = QVBoxLayout()
        d_a_right.addWidget(QLabel("— L.0.2 A: SearchField —"))
        d_a_right.addWidget(self._search_field)
        d_a_right.addWidget(self._search_status)
        d_a_right.addWidget(QLabel("— L.0.2 A: ProgressBar —"))
        progress_controls = QHBoxLayout()
        progress_controls.addWidget(QLabel("Mode:"))
        progress_controls.addWidget(self._progress_mode_combo)
        progress_controls.addStretch(1)
        d_a_right.addLayout(progress_controls)
        d_a_right.addWidget(self._progress_bar)
        d_a_right.addWidget(self._progress_bar_label)
        d_a_right.addStretch(1)

        d_a_body = QHBoxLayout()
        d_a_body.addLayout(d_a_left, 1)
        d_a_body.addLayout(d_a_right, 1)

        # --- root --------------------------------------------------
        root = QVBoxLayout(self)
        root.addLayout(controls)
        root.addWidget(QLabel("L.0 — System form widgets"))
        root.addLayout(l0_body)
        root.addSpacing(12)
        root.addWidget(QLabel("L.0.2 — Delivery A widgets"))
        root.addLayout(d_a_body)

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

    def _on_progress_mode_changed(self) -> None:
        indeterminate = self._progress_mode_combo.currentData()
        self._progress_bar.set_indeterminate(bool(indeterminate))
        if indeterminate:
            self._progress_bar_label.setText("Progress: indeterminate")
        else:
            self._advance_progress()

    def _advance_progress(self) -> None:
        if self._progress_bar.indeterminate:
            return
        value = (self._progress_bar.value() + 5) % 101
        self._progress_bar.setValue(value)
        self._progress_bar_label.setText(f"Progress: {value}% (determinate)")


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = DebugWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())