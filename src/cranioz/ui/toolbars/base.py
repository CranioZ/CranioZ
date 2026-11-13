"""Toolbar widget.

Materializes a ToolbarSpec as a Qt widget. It is internal to an Editor;
the Workspace never hosts one.

Responsibilities:
- Resolve each tool_id declared in the spec against the ToolRegistry.
- Create the concrete Tool instances for each item.
- Display the items in the declared orientation.
- Consume an IconProvider for icons.
- Emit a signal when a Tool is triggered or toggled.
- Apply the presentation policy declared by the spec:
  * ``ACTIVE_ONLY`` toolbars can be visually de-emphasized via
    ``set_active(False)`` (opacity effect) without hiding the buttons.
  * ``COLLAPSIBLE`` toolbars can be compressed via
    ``set_expanded(False)``, exposing a compact chevron toggle that
    expands them again.

Non-responsibilities:
- The Toolbar does not decide availability or enablement.
  The Tool decides those, based on a ToolContext that the Editor
  provides at materialization time.
- The Toolbar does not mutate the Scene. Tools do, via Commands.
- The Toolbar does not persist state. That is the Editor's job.
- The Toolbar does not decide *when* to call ``set_active`` or
  ``set_expanded``. That decision belongs to the renderer that owns
  the view context (``ViewLayoutRenderer`` / Bloco 4).
- The Toolbar does not hide itself. ``setVisible(False)`` is reserved
  for the owner (the renderer or the Editor), which knows whether
  the toolbar is ``ACTIVE_ONLY``, ``HIDDEN``, ``AUTO_HIDE``, etc.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.toolbars.specification import (
    ToolbarOrientation,
    ToolbarSpec,
    ToolbarVisibilityMode,
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
    expanded_changed = Signal(bool)  # new expanded state

    #: Opacity applied to the toolbar when ``set_active(False)`` is
    #: called on an ``ACTIVE_ONLY`` toolbar. Buttons remain clickable;
    #: only the visual is affected (ADR-0013 §2.6).
    INACTIVE_OPACITY: float = 0.5

    #: Minimum dimension (px) of a collapsed COLLAPSIBLE toolbar. Wide
    #: enough to fit the chevron and the title label without the
    #: buttons.
    _COLLAPSED_WIDTH: int = 28

    def __init__(
        self,
        spec: ToolbarSpec,
        registry: ToolRegistry,
        theme: ThemeService,
        *,
        icon_provider: IconProvider,
        context: ToolContext | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._spec = spec
        self._registry = registry
        self._theme = theme
        self._icon_provider = icon_provider
        self._context = context if context is not None else ToolContext()
        self._bindings: list[ToolbarItemBinding] = []

        # Runtime presentation state. Neither field hides the widget;
        # both are policy-driven and owned by the caller (the renderer).
        self._active = True
        self._expanded = True

        # --- Structural widgets ------------------------------------
        # The root layout is always a QVBoxLayout so the chevron row
        # can sit above the item row regardless of orientation. This
        # is an internal detail; ``orientation`` only affects the
        # item row.
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(4, 4, 4, 4)
        self._root_layout.setSpacing(2)
        self._root_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._item_layout = (
            QHBoxLayout()
            if spec.orientation is ToolbarOrientation.HORIZONTAL
            else QVBoxLayout()
        )
        self._item_layout.setContentsMargins(0, 0, 0, 0)
        self._item_layout.setSpacing(4)
        # Align buttons to the top of a VERTICAL Toolbar (and to the
        # left of a HORIZONTAL Toolbar). Without this, the default
        # alignment centers the buttons vertically, which looks
        # disconnected from the top edge of the View.
        self._item_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._chevron_button: QPushButton | None = None
        self._title_label: QLabel | None = None
        if spec.visibility_mode is ToolbarVisibilityMode.COLLAPSIBLE:
            self._build_chevron_row()

        # Container that holds the item layout. It is hidden when the
        # toolbar is collapsed (COLLAPSIBLE + set_expanded(False)).
        self._items_container = QWidget(self)
        self._items_container.setLayout(self._item_layout)
        self._root_layout.addWidget(self._items_container)

        for tool_id in spec.tool_ids:
            self._append_tool(tool_id)

        self.setObjectName(f"toolbar.{spec.toolbar_id}")
        self.setWindowTitle(spec.title)

    # ----- Public API ------------------------------------------------

    @property
    def spec(self) -> ToolbarSpec:
        return self._spec

    def bindings(self) -> tuple[ToolbarItemBinding, ...]:
        """Return the materialized item bindings, in declaration order."""
        return tuple(self._bindings)

    def tool_ids(self) -> tuple[str, ...]:
        return tuple(b.tool_id for b in self._bindings)

    def is_active(self) -> bool:
        """Return True if the toolbar is currently visually active.

        Only meaningful for ``ACTIVE_ONLY`` toolbars; other modes
        always report ``True`` because ``set_active`` is a no-op for
        them.
        """
        return self._active

    def is_expanded(self) -> bool:
        """Return True if the toolbar is currently expanded.

        Only meaningful for ``COLLAPSIBLE`` toolbars; other modes
        always report ``True`` because ``set_expanded`` is a no-op
        for them.
        """
        return self._expanded

    # ----- Presentation policy (ACTIVE_ONLY / COLLAPSIBLE) ----------

    def set_active(self, active: bool) -> None:
        """Visually de-emphasize (or re-emphasize) the toolbar.

        No-op unless the spec's ``visibility_mode`` is
        ``ACTIVE_ONLY``. When inactivated, a
        ``QGraphicsOpacityEffect`` with ``opacity == INACTIVE_OPACITY``
        is attached to the toolbar. The buttons remain visible and
        clickable; only the visual is affected (ADR-0013 §2.6).

        The toolbar is not hidden. Deciding when to hide it (or
        whether to hide it at all) belongs to the owner (the
        renderer), not to the Toolbar.
        """
        if self._spec.visibility_mode is not ToolbarVisibilityMode.ACTIVE_ONLY:
            return
        if self._active == active:
            return
        self._active = active
        self._apply_opacity_effect()

    def set_expanded(self, expanded: bool) -> None:
        """Expand or collapse the toolbar.

        No-op unless the spec's ``visibility_mode`` is
        ``COLLAPSIBLE``. When collapsed, the item row is hidden, the
        title is shown as a compact label, and the toolbar is sized
        down to ``_COLLAPSED_WIDTH``. When expanded, the title label
        is hidden and the item row is shown again.

        Emits ``expanded_changed`` with the new state on every actual
        transition (i.e. when the state changes). The chevron button
        toggles the state itself; the renderer may also call
        ``set_expanded`` explicitly.
        """
        if self._spec.visibility_mode is not ToolbarVisibilityMode.COLLAPSIBLE:
            return
        if self._expanded == expanded:
            return
        self._expanded = expanded
        self._apply_expanded_state()
        self.expanded_changed.emit(expanded)

    # ----- Internals -------------------------------------------------

    def _build_chevron_row(self) -> None:
        """Create the chevron button and the collapsed title label.

        The chevron is only present for ``COLLAPSIBLE`` toolbars. It
        flips the expanded state on click. The title label is shown
        only while collapsed, giving the compressed toolbar a name.
        """
        chevron = QPushButton("\u25be", self)  # ▾
        chevron.setObjectName(f"toolbar.{self._spec.toolbar_id}.chevron")
        chevron.setFlat(True)
        chevron.setCursor(Qt.CursorShape.PointingHandCursor)
        chevron.setFixedWidth(20)
        chevron.setToolTip(self._spec.title)
        chevron.setAccessibleName(self._spec.title)
        chevron.clicked.connect(self._on_chevron_clicked)

        title = QLabel(self._spec.title, self)
        title.setObjectName(f"toolbar.{self._spec.toolbar_id}.title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        # Only shown while collapsed. Hidden by default because the
        # toolbar starts expanded.
        title.setVisible(False)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(2)
        row.addWidget(chevron)
        row.addWidget(title, stretch=1)
        self._root_layout.addLayout(row)

        self._chevron_button = chevron
        self._title_label = title

    def _on_chevron_clicked(self) -> None:
        self.set_expanded(not self._expanded)

    def _apply_expanded_state(self) -> None:
        """Reflect ``self._expanded`` in the widget tree.

        Collapsed: hide the item container, show the title label,
        update the chevron glyph to ``▸``, shrink the toolbar.
        Expanded: inverse.
        """
        if self._spec.visibility_mode is not ToolbarVisibilityMode.COLLAPSIBLE:
            return
        self._items_container.setVisible(self._expanded)
        if self._title_label is not None:
            self._title_label.setVisible(not self._expanded)
        if self._chevron_button is not None:
            self._chevron_button.setText("\u25be" if self._expanded else "\u25b8")

        if self._expanded:
            self.setMaximumWidth(16777215)  # QWIDGETSIZE_MAX
            self.setMinimumWidth(0)
        else:
            self.setMinimumWidth(self._COLLAPSED_WIDTH)
            self.setMaximumWidth(self._COLLAPSED_WIDTH)

    def _apply_opacity_effect(self) -> None:
        """Attach or remove the ``QGraphicsOpacityEffect``."""
        if self._active:
            self.setGraphicsEffect(None)
        else:
            effect = QGraphicsOpacityEffect(self)
            effect.setOpacity(self.INACTIVE_OPACITY)
            self.setGraphicsEffect(effect)

    def _append_tool(self, tool_id: str) -> None:
        tool = self._registry.create(tool_id)
        label = tool.label or tool_id

        button = QPushButton(label, self)
        button.setObjectName(f"toolbar.item.{tool_id}")
        button.setToolTip(tool.description or label)
        if tool.icon:
            button.setIcon(self._icon_provider.icon(tool.icon))

        if self._is_toggle(tool):
            button.setCheckable(True)
            button.toggled.connect(lambda checked, tid=tool_id: self._on_toggle(tid, checked))
        else:
            button.clicked.connect(lambda _=False, tid=tool_id: self._on_click(tid))

        self._item_layout.addWidget(button)
        self._bindings.append(ToolbarItemBinding(tool_id=tool_id, widget=button, tool=tool))

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
            checked = bool(current)
        self.tool_toggled.emit(tool_id, checked)

    def _binding_for(self, tool_id: str) -> ToolbarItemBinding:
        for binding in self._bindings:
            if binding.tool_id == tool_id:
                return binding
        raise KeyError(f"tool_id not materialized in this toolbar: {tool_id}")