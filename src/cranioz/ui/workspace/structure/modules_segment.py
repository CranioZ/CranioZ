"""ModulesSegment — the center zone of the Workspace Top Bar.

Displays the modules of the active clinical Flow as selectable buttons,
followed by a "+" button to add a module.

The segment does not know what a Flow is. It receives (module_id,
display_label) pairs via ``set_modules`` and reflects the selected
module via ``set_selected``. Each user intention emits a signal:

- ``module_selected(module_id)`` — a module button was clicked.
- ``add_module_requested()`` — the "+" button was clicked.

Until Phase 5 delivers ``WorkflowEngine``, the MainWindow feeds a
placeholder list. That is a temporary source, not a contract.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QWidget,
)

from cranioz.infrastructure.i18n import tr
from cranioz.ui.icons.provider import IconProvider


class ModulesSegment(QWidget):
    """Center zone of the Workspace Top Bar."""

    module_selected = Signal(str)
    add_module_requested = Signal()

    def __init__(
        self,
        icon_provider: IconProvider,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._icon_provider = icon_provider
        self.setObjectName("workspace.top_bar.modules_segment")

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)

        self._add_button = QPushButton(self)
        self._add_button.setObjectName("workspace.top_bar.modules_segment.add")
        self._add_button.setFlat(True)
        self._add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_button.setIcon(self._icon_provider.icon("new"))
        self._add_button.setToolTip(tr("workspace.top_bar.add_module", "Add module"))
        self._add_button.setAccessibleName(tr("workspace.top_bar.add_module", "Add module"))
        self._add_button.setFixedWidth(28)
        self._add_button.clicked.connect(self.add_module_requested)
        self._layout.addWidget(self._add_button)

        self._module_buttons: dict[str, QPushButton] = {}
        self._selected_id: str | None = None

    # ----- Public API -----------------------------------------------

    def set_modules(self, modules: tuple[tuple[str, str], ...]) -> None:
        """Rebuild the segment from (module_id, display_label) pairs.

        The current selection is preserved when the selected module is
        still present. Otherwise the selection is cleared.
        """
        # Remove existing module buttons (keep the "+" button at the end).
        for button in self._module_buttons.values():
            self._layout.removeWidget(button)
            button.setParent(None)
            button.deleteLater()
        self._module_buttons.clear()

        previous = self._selected_id
        self._selected_id = None

        for module_id, label in modules:
            button = QPushButton(label, self)
            button.setObjectName(f"workspace.top_bar.modules_segment.module.{module_id}")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda _checked=False, mid=module_id: self._on_module_clicked(mid)
            )
            # Insert before the "+" button so it stays at the end.
            self._layout.insertWidget(self._layout.count() - 1, button)
            self._module_buttons[module_id] = button

        if previous is not None and previous in self._module_buttons:
            self.set_selected(previous)

    def set_selected(self, module_id: str | None) -> None:
        """Mark a module as selected.

        The selection is mutually exclusive: selecting one button
        unchecks all others. ``None`` clears the selection.
        """
        if module_id is not None and module_id not in self._module_buttons:
            raise KeyError(f"unknown module_id: {module_id!r}")
        self._selected_id = module_id
        for mid, button in self._module_buttons.items():
            button.setChecked(mid == module_id)

    def selected_module_id(self) -> str | None:
        return self._selected_id

    def module_ids(self) -> tuple[str, ...]:
        return tuple(self._module_buttons.keys())

    # ----- Internals ------------------------------------------------

    def _on_module_clicked(self, module_id: str) -> None:
        # setCheckable(True) already toggled the button. If the user
        # clicked the currently-selected module, Qt unchecks it; we
        # interpret that as "deselect" and keep it consistent.
        button = self._module_buttons[module_id]
        if not button.isChecked():
            self.set_selected(None)
            return
        self.set_selected(module_id)
        self.module_selected.emit(module_id)
