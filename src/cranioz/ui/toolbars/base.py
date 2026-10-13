"""Toolbar widget.

Materializes a ToolbarSpec as a Qt widget. It is internal to an Editor;
the Workspace never hosts one.

Responsibilities:
- Resolve each tool_id declared in the spec against the ToolRegistry.
- Create the concrete Tool instances for each item.
- Display the items in the declared orientation.
- Consume a ThemeService for icon resolution.
- Emit a signal when a Tool is triggered or toggled.

Non-responsibilities:
- The Toolbar does not decide availability or enablement.
  The Tool decides those, based on a ToolContext that the Editor
  provides at materialization time.
- The Toolbar does not mutate the Scene. Tools do, via Commands.
- The Toolbar does not persist state. That is the Editor's job.

This widget is deliberately minimal. It is the first Qt widget in
CranioZ and it exists to validate the contract between:
  ToolbarSpec + ToolRegistry + ThemeService → QWidget
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cranioz.ui.theme.service import ThemeService
from cranioz.ui.toolbars.specification import (
    ToolbarOrientation,
    ToolbarSpec,
)
from cranioz.ui.tools.registry.tool_definition import Tool, ToolContext
from cranioz.ui.tools.registry.tool_registry import ToolRegistry


@dataclass(frozen=True)
class ToolbarItemBinding:
    """A materialized item, linking a ToolbarItem to a Tool instance."""

    tool_id: str
    widget: QWidget
    tool: Tool | None


class Toolbar(QWidget):
    """Qt widget materializing a ToolbarSpec."""

    tool_triggered = Signal(str)  # tool_id
    tool_toggled = Signal(str, bool)  # tool_id, checked

    def __init__(
        self,
        spec: ToolbarSpec,
        registry: ToolRegistry,
        theme: ThemeService,
        context: ToolContext | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._spec = spec
        self._registry = registry
        self._theme = theme
        self._context = context if context is not None else ToolContext()
        self._bindings: list[ToolbarItemBinding] = []

        self.setObjectName(f"toolbar.{spec.toolbar_id}")
        self.setWindowTitle(spec.title)

        self._layout = (
            QHBoxLayout(self)
            if spec.orientation is ToolbarOrientation.HORIZONTAL
            else QVBoxLayout(self)
        )
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(4)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        for tool_id in spec.tool_ids:
            self._append_tool(tool_id)

    # ----- Public API ------------------------------------------------

    @property
    def spec(self) -> ToolbarSpec:
        return self._spec

    def bindings(self) -> tuple[ToolbarItemBinding, ...]:
        """Return the materialized item bindings, in declaration order."""
        return tuple(self._bindings)

    def tool_ids(self) -> tuple[str, ...]:
        return tuple(b.tool_id for b in self._bindings)

    # ----- Internals -------------------------------------------------

    def _append_tool(self, tool_id: str) -> None:
        tool = self._registry.create(tool_id)
        label = tool.label or tool_id
        icon_name = self._theme.icon_name(tool.icon) if tool.icon else None

        # For this first version we render Tools as buttons with their label.
        # Icon resolution is exercised but not yet drawn (no icon loader).
        button = QPushButton(label, self)
        button.setObjectName(f"toolbar.item.{tool_id}")
        button.setToolTip(tool.description or label)
        if icon_name is not None:
            button.setProperty("icon_name", icon_name)

        if self._is_toggle(tool):
            button.setCheckable(True)
            button.toggled.connect(
                lambda checked, tid=tool_id: self._on_toggle(tid, checked)
            )
        else:
            button.clicked.connect(lambda _=False, tid=tool_id: self._on_click(tid))

        self._layout.addWidget(button)
        self._bindings.append(
            ToolbarItemBinding(tool_id=tool_id, widget=button, tool=tool)
        )

    def _is_toggle(self, tool: Tool) -> bool:
        return hasattr(tool, "toggle") and hasattr(tool, "checked")

    def _on_click(self, tool_id: str) -> None:
        binding = self._binding_for(tool_id)
        tool = binding.tool
        if tool is None:
            return
        if not tool.is_available(self._context) or not tool.is_enabled(self._context):
            return
        execute = getattr(tool, "execute", None)
        if callable(execute):
            execute(self._context)
        self.tool_triggered.emit(tool_id)

    def _on_toggle(self, tool_id: str, checked: bool) -> None:
        binding = self._binding_for(tool_id)
        tool = binding.tool
        if tool is None:
            return
        toggle = getattr(tool, "toggle", None)
        if callable(toggle):
            current = toggle()
            # The tool's new state wins.
            checked = bool(current)
        self.tool_toggled.emit(tool_id, checked)

    def _binding_for(self, tool_id: str) -> ToolbarItemBinding:
        for binding in self._bindings:
            if binding.tool_id == tool_id:
                return binding
        raise KeyError(f"tool_id not materialized in this toolbar: {tool_id}")
