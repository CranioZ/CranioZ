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

Styling is owned by the global QSS emitted by ``ThemeCompiler``. The
row only toggles its ``checked`` property and repolishes itself; it
never calls ``setStyleSheet``. The arrows between steps are rendered
by ``IconProvider`` as small icons.
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
from cranioz.ui.icons.provider import IconProvider


class FlowRow(QFrame):
    """A clickable row rendering a single flow and its steps."""

    selected = Signal(object)  # str | None (flow_id)

    def __init__(
        self,
        flow: FlowDefinition,
        *,
        translate: Callable[[str], str],
        icon_provider: IconProvider,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._icon_provider = icon_provider
        self.setObjectName("home_page_flow_list_flow")
        self.setFrameShape(QFrame.Shape.NoFrame)
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
        name.setObjectName("home_page_flow_list_name")
        name.setProperty("role", "title")
        layout.addWidget(name)

        # Separator between name and steps.
        layout.addWidget(_make_separator())

        # Steps, with icons between them.
        for i, step in enumerate(flow.steps):
            if i > 0:
                arrow = self._make_arrow_label()
                layout.addWidget(arrow)
            step_widget = _make_step_widget(self._translate(step.name_key))
            layout.addWidget(step_widget)

        layout.addStretch(1)

        self.setProperty("checked", "false")
        self._repolish()

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
        self.setProperty("checked", "true" if checked else "false")
        self._repolish()

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

    def _make_arrow_label(self) -> QLabel:
        """Build a small QLabel hosting the forward icon."""
        label = QLabel()
        label.setPixmap(self._icon_provider.icon("forward", size=12).pixmap(12, 12))
        label.setProperty("class", "arrow")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def _repolish(self) -> None:
        """Re-evaluate the stylesheet after the dynamic property changed."""
        style = self.style()
        if style is not None:
            style.unpolish(self)
            style.polish(self)


# ----- Internals ----------------------------------------------------


def _make_step_widget(label: str) -> QWidget:
    """A small bordered label representing one step."""
    widget = QLabel(label)
    widget.setObjectName("home_page_flow_list_step")
    widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return widget


def _make_separator() -> QFrame:
    """A vertical line between the flow name and the steps."""
    sep = QFrame()
    sep.setObjectName("home_page_flow_list_separator")
    sep.setFrameShape(QFrame.Shape.VLine)
    sep.setFrameShadow(QFrame.Shadow.Sunken)
    return sep
