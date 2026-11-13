"""Editor ABC.

An Editor is a functional unit hosted by an Area. It provides a specific
interaction experience. It does not know where it is placed; the Area
hosts it.

An Editor may host one or more Views (Axial, Coronal, Sagittal, 3D, ...).
Views are internal to the Editor and are organized in a View Layout Tree
(ADR-0013). The Editor coordinates its Views, manages its Toolbars, and
handles the user's interaction with the underlying data.

This module defines the contract only. Concrete Editors may use Qt for
materialization, but the contract itself does not *inherit* from Qt.
The one exception is ``_EditorSignals``, a private QObject that carries
the ``active_view_changed`` signal. It is instantiated by
``Editor.__init__`` and is not part of the public ABC surface; the
contract still exposes ``active_view_changed`` and ``set_active_view``
as plain attributes/methods. Because ``_EditorSignals`` is a QObject,
constructing an Editor requires an existing ``QApplication`` — the same
requirement the existing ``_MPRSignals`` in ``MPRView`` already imposes.

See ADR-0013 §2.3, §2.6 for the View / Editor distinction and the
``ToolbarVisibilityMode.ACTIVE_ONLY`` policy that this signal feeds.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QObject, Signal

from cranioz.ui.tools.registry.tool_definition import ToolContext

if TYPE_CHECKING:
    from cranioz.ui.editors.editor_context import EditorContext
    from cranioz.ui.editors.view import View
    from cranioz.ui.editors.view_layout_spec import ViewLayoutSpec
    from cranioz.ui.toolbars.specification import ToolbarSpec

_logger = logging.getLogger(__name__)


class _EditorSignals(QObject):
    """Qt signal carrier for an Editor.

    The ``Editor`` is an ABC and does not inherit from ``QObject``.
    Emitting Qt signals requires a ``QObject``; this class provides
    one, privately, so that the ABC contract stays free of a direct
    Qt inheritance.

    The signal carries ``str | None``. ``None`` means "no View is
    active". The signal type is ``object`` because ``Signal(str)``
    rejects ``None`` in PySide6; the documented contract is
    ``str | None`` (see ``Editor.set_active_view``).
    """

    active_view_changed = Signal(object)  # payload: str | None


class Editor(ABC):
    """Abstract Editor contract."""

    editor_id: str
    title: str

    #: The id of the View that is currently active within this
    #: Editor, or ``None`` when no View is active. Updated through
    #: ``set_active_view`` and reflected in ``active_view_changed``.
    active_view_id: str | None

    def __init__(self, editor_id: str, title: str) -> None:
        self.editor_id = editor_id
        self.title = title
        self.active_view_id = None
        self._signals = _EditorSignals()
        self.active_view_changed = self._signals.active_view_changed

    # Lifecycle -----------------------------------------------------

    def initialize(self, context: EditorContext) -> None:
        """Called once at insertion. Heavy resources are set up here."""
        return None

    def activate(self) -> None:
        """Called when the Editor becomes the active one in its Area."""
        return None

    def deactivate(self) -> None:
        """Called when the Editor stops being active. Must not dispose."""
        return None

    def dispose(self) -> None:
        """Called when the Editor is removed and its resources released.

        Disposes every View hosted by this Editor, then the Editor's
        own resources. Concrete Editors that override this method must
        call ``super().dispose()`` to ensure the Views are disposed.

        After disposal, ``active_view_id`` is reset to ``None``. The
        ``active_view_changed`` signal is NOT emitted during disposal:
        the ViewLayoutRenderer and other consumers may already be in
        teardown, and emitting a signal to them at that point is a
        source of subtle bugs. Consumers that need to react to a
        disposed Editor react to the Editor lifecycle, not to this
        signal.
        """
        for view in self.views():
            view.dispose()
        self.active_view_id = None

    # Active View (ADR-0013 §2.6) -----------------------------------

    def set_active_view(self, view_id: str | None) -> None:
        """Set the active View of this Editor.

        Rules:

        - ``None`` clears the active View. If a View was active, the
          signal is emitted with ``None``.
        - ``view_id`` that is already active is a no-op (no signal).
        - ``view_id`` that is not among ``self.views()`` is rejected:
          a ``WARNING`` is logged, ``active_view_id`` is unchanged, and
          no signal is emitted. This is a contract violation by the
          caller (typically the ``ViewLayoutRenderer`` or a test), and
          must be visible (PRINCIPLES.md §17 — errors are information).
        - A valid, different ``view_id`` updates ``active_view_id``
          and emits ``active_view_changed`` with the new id.

        The Editor does not materialize Toolbars or change their
        visibility itself: it emits the signal, and the
        ``ViewLayoutRenderer`` applies the ``ACTIVE_ONLY`` policy
        (ADR-0013 §2.6).
        """
        if view_id is not None:
            known = {v.view_id for v in self.views()}
            if view_id not in known:
                _logger.warning(
                    "Editor %r: set_active_view(%r) ignored; view_id is not "
                    "among the Editor's Views %r",
                    self.editor_id,
                    view_id,
                    sorted(known),
                )
                return

        if self.active_view_id == view_id:
            return

        self.active_view_id = view_id
        self.active_view_changed.emit(view_id)

    # Content -------------------------------------------------------

    @abstractmethod
    def content_widget(self) -> Any:
        """Return the widget that represents the Editor's content.

        When the Editor hosts Views, the content widget is the
        container that arranges the Views according to
        ``view_layout()``. When the Editor has no Views, the content
        widget is the Editor's own widget (e.g., a Properties panel,
        a Console, etc.).
        """
        raise NotImplementedError

    # Views (ADR-0013) ----------------------------------------------

    def views(self) -> tuple[View, ...]:
        """Return the Views hosted by this Editor.

        Empty by default. Editors that host Views (e.g., the
        TomographyEditor) override this method to return them in the
        order they appear in the layout.

        The Editor owns the Views. It is responsible for disposing
        them (see ``dispose()``).
        """
        return ()

    def view_layout(self) -> ViewLayoutSpec | None:
        """Return the layout of the Views, or None for a single View.

        The layout is a ``ViewLayoutSpec`` (nested split tree), the
        same N-ary model used for the Area Layout Tree and the
        Editor Layout Tree. The LayoutRenderer materializes it.

        Editors with zero or one View return None; the single View
        (if any) occupies the whole content area.
        """
        return None

    # Toolbars ------------------------------------------------------

    def toolbar_specs(self) -> list[ToolbarSpec]:
        """Declare the Editor's internal Toolbars. Empty by default.

        Each ToolbarSpec declares its orientation (HORIZONTAL or
        VERTICAL) and its position (LEFT, RIGHT, TOP, BOTTOM) inside
        the Editor. See ADR-0013 §2.6.
        """
        return []

    def tool_context(self) -> ToolContext:
        """Return the ToolContext used to materialize this Editor's Toolbars.

        The Editor owns its ToolContext; the AreaWidget and the Toolbar
        widget only consume it. Editors that need a richer context
        (selection, scene query, command dispatcher) override this method
        and return an instance with the appropriate services.

        The default implementation returns an empty ``ToolContext``,
        which is correct for Editors that declare no Toolbar or whose
        Tools are context-independent.
        """
        return ToolContext()

    # Persistence ---------------------------------------------------

    def persistent_state(self) -> dict[str, Any]:
        """Return the Editor's persistable presentation state."""
        return {}

    def restore_state(self, state: dict[str, Any]) -> None:
        """Restore a previously saved presentation state."""
        return None