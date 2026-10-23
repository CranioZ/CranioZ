"""FlowRow — one flow rendered as a horizontal row of steps.

Renders a single flow as:

    [ Nome ]  |  Step1  →  Step2  →  Step3

The entire row is clickable. Clicking selects the flow (emits
``selected(flow_id)``); clicking again deselects it (emits
``selected(None)``). Only one flow is selected at a time in the
``FlowList``; the ``FlowRow`` handles its own visual "checked" state
and the list handles mutual exclusion.

The row does not know about the ``FlowList`` or the ``HomePage``. It
emits a signal; the caller decides what to do.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QWidget,
)

from cranioz.application.flows.definition import FlowDefinition


class FlowRow(QFrame):
    """A clickable row rendering a single flow and its steps."""

    selected = Signal(object)  # str | None (flow_id)

    def __init__(
        self,
        flow: FlowDefinition,
        *,
        translate: Callable[[str], str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName(f"home_page.flow_list.flow.{flow.flow_id}")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self._flow = flow
        self._translate = translate
        self._checked = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        name = QLabel(self._translate(flow.name_key))
        name.setObjectName(f"home_page.flow_list.flow.{flow.flow_id}.name")
        name_font = name.font()
        name_font.setBold(True)
        name_font.setPointSize(11)
        name.setFont(name_font)
        layout.addWidget(name)

        # Separator between name and steps.
        layout.addWidget(_make_separator())

        # Steps, with arrows between them.
        for i, step in enumerate(flow.steps):
            if i > 0:
                arrow = QLabel("→")
                arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
                arrow.setStyleSheet("color: #888; padding: 0 2px;")
                layout.addWidget(arrow)
            step_widget = _make_step_widget(self._translate(step.name_key))
            layout.addWidget(step_widget)

        layout.addStretch(1)

        self._apply_style(checked=False)

    # ----- Public API -----------------------------------------------

    @property
    def flow_id(self) -> str:
        return self._flow.flow_id

    def is_checked(self) -> bool:
        return self._checked

    def set_checked(self, checked: bool) -> None:
        if self._checked == checked:
            return
        self._checked = checked
        self._apply_style(checked=checked)

    # ----- Qt events -----------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self._checked:
            self.set_checked(False)
            self.selected.emit(None)
        else:
            self.set_checked(True)
            self.selected.emit(self._flow.flow_id)

    # ----- Internals -----------------------------------------------

    def _apply_style(self, *, checked: bool) -> None:
        background = "#dff0d8" if checked else "#3a3a3a"
        border = "#27ae60" if checked else "#555"
        self.setStyleSheet(
            f"QFrame#{self.objectName()} {{"
            f"  background-color: {background};"
            f"  border: 1px solid {border};"
            f"  border-radius: 4px;"
            f"}}"
        )


# ----- Internals ----------------------------------------------------


def _make_step_widget(label: str) -> QWidget:
    """A small bordered label representing one step."""
    widget = QLabel(label)
    widget.setObjectName("home_page.flow_list.step")
    widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
    widget.setStyleSheet(
        "QLabel#home_page_flow_list_step {"
        "  padding: 4px 8px;"
        "  border: 1px solid #888;"
        "  border-radius: 3px;"
        "  background-color: #4a4a4a;"
        "  color: #ddd;"
        "}"
    )
    return widget


def _make_separator() -> QFrame:
    """A vertical line between the flow name and the steps."""
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.VLine)
    sep.setFrameShadow(QFrame.Shadow.Sunken)
    sep.setStyleSheet("color: #666;")
    return sep
