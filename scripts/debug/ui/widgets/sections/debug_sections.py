"""Visual debug harness for the L.0.2 Delivery B widgets only."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from cranioz.infrastructure.settings.in_memory_settings_service import (
    InMemorySettingsService,
)
from cranioz.ui.icons.unicode import UnicodeIconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.theme.tokens import ThemeMode, ThemeName
from cranioz.ui.widgets.navigation import IconSidebar
from cranioz.ui.widgets.sections import CollapsibleSection, DragList


class DeliveryBDebugWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CranioZ - L.0.2 Delivery B")
        self.resize(960, 720)

        self._theme_service = ThemeService(
            settings=InMemorySettingsService(),
            default_mode=ThemeMode.DARK,
        )
        self._icons = UnicodeIconProvider(self._theme_service)

        self._theme_combo = QComboBox()
        self._theme_combo.addItem("Dark", ThemeMode.DARK)
        self._theme_combo.addItem("Light", ThemeMode.LIGHT)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)

        sidebar = IconSidebar(self._icons)
        sidebar.add_item("documents", "open", "Documentos")
        sidebar.add_item("schedule", "home", "Agenda")
        sidebar.add_item("procedures", "module_cephalometry", "Procedimentos")
        sidebar.add_item("budgets", "module_guides", "Orçamentos")
        sidebar.set_active("documents")
        sidebar.setFixedWidth(52)

        sections = DragList()
        sections.add_section(
            "documents",
            self._section(
                "Modelo de documentos",
                self._nested_list(
                    ("orientations", "Orientações"),
                    ("contracts", "Contratos"),
                    ("consent", "Termo de consentimento"),
                ),
            ),
        )
        sections.add_section("schedule", self._section("Agenda"))
        sections.add_section(
            "procedures",
            self._section(
                "Procedimentos",
                self._nested_list(
                    ("odontology", "Odontologia"),
                    ("maxillofacial", "Cirurgia Buco-Maxilo-Facial"),
                ),
            ),
        )
        sections.add_section("budgets", self._section("Orçamentos"))

        order_label = QLabel()
        sections.order_changed.connect(
            lambda keys: order_label.setText(f"Ordem: {' → '.join(keys)}")
        )
        order_label.setText(f"Ordem: {' → '.join(sections.keys())}")

        body = QHBoxLayout()
        body.addWidget(sidebar)
        body.addWidget(sections, 1)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Tema:"))
        controls.addWidget(self._theme_combo)
        controls.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addLayout(body, 1)
        layout.addWidget(order_label)
        self._apply_theme()

    def _section(self, title: str, body: QWidget | None = None) -> CollapsibleSection:
        section = CollapsibleSection(title, draggable=True, icon_provider=self._icons)
        if body is not None:
            section.set_body_widget(body)
        return section

    def _nested_list(self, *items: tuple[str, str]) -> DragList:
        widget = DragList()
        for key, title in items:
            widget.add_section(key, self._section(title))
        return widget

    def _on_theme_changed(self) -> None:
        mode = self._theme_combo.currentData()
        self._theme_service.set_mode(ThemeMode.LIGHT if mode is ThemeName.LIGHT else ThemeMode.DARK)
        self._apply_theme()

    def _apply_theme(self) -> None:
        self._theme_service.compiler().apply(self._theme_service.compiled())


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = DeliveryBDebugWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
