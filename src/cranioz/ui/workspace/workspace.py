"""Workspace.

The Workspace is the runtime environment where clinical work happens.
It is the composition of Areas — containers that host Editors — and
Overlays — floating layers over Regions.

This class is the *facade* of the Workspace subsystem. It ties
together the lower-level components built in earlier pieces:

- LayoutBuilder: turns a ModuleUISpec into domain structures
  (Areas, LayoutTree, populated AreaManager, Editors).
- LayoutRenderer: materializes the LayoutTree into Qt widgets
  (nested QSplitters and AreaWidgets).
- OverlayManager: registers and repositions Overlays by Placement.

Public responsibilities:

- ``load_spec(spec)``: materialize a ModuleUISpec. Rebuilds the
  whole visual tree and repositions every registered Overlay.
- ``clear()``: drop the current composition (Areas, widgets,
  Overlays registrations remain; they can be re-added on the next
  ``load_spec``).
- ``areas()``: return the Areas of the current composition.
- ``overlay_manager``: read-only access for advanced callers.
- ``top_overlay``: the shared Top Bar Overlay, exposed so the
  Workspace host can populate its content.

Non-responsibilities (future pieces):

- Persistence of layout state (Bloco 11).
- Drag-and-drop, floating Areas, multi-monitor (Bloco 14).
- Top Bar content: the three segments are not built here; they
  will be added by a dedicated Top Bar composition.
- Steps Panel: it is a second shared Overlay, to be added when the
  Flow system is implemented (Bloco 9).

Design rules:

- The Workspace is a QWidget. Its single visual child is the root
  widget returned by the LayoutRenderer.
- ``load_spec()`` is idempotent in the sense that calling it again
  replaces the previous composition. It always calls ``clear()``
  first.
- The Workspace owns the AreaManager produced by the build result.
  It does not copy it: the same manager is used throughout the
  lifecycle of the composition.
- The Workspace owns the LayoutRenderer instance. The renderer
  caches widget instances; the Workspace is responsible for
  clearing that cache when the composition is replaced.
- The TopOverlay is registered in the OverlayManager on every
  ``load_spec()``. Registration is idempotent, so re-registering
  the same instance on subsequent calls is safe.
"""

from __future__ import annotations

from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QVBoxLayout, QWidget

from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.area_manager import AreaManager
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.layout.layout_builder import (
    BuildResult,
    LayoutBuilder,
)
from cranioz.ui.workspace.layout.layout_renderer import LayoutRenderer
from cranioz.ui.workspace.overlays.overlay_manager import OverlayManager
from cranioz.ui.workspace.overlays.region import Bounds, Region
from cranioz.ui.workspace.overlays.top_overlay import TopOverlay
from cranioz.ui.workspace.specs.module_ui_spec import ModuleUISpec


class WorkspaceError(RuntimeError):
    """Raised when the Workspace is used in an invalid state."""


class Workspace(QWidget):
    """The Workspace facade.

    Hosts the current composition, owns the LayoutRenderer and the
    OverlayManager, and exposes ``load_spec()`` as the single entry
    point for building a new layout.
    """

    def __init__(
        self,
        editor_registry: EditorRegistry,
        tool_registry: ToolRegistry,
        theme_service: ThemeService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("workspace")

        self._editor_registry = editor_registry
        self._tool_registry = tool_registry
        self._theme_service = theme_service

        self._layout_builder = LayoutBuilder(editor_registry)
        self._layout_renderer = LayoutRenderer(tool_registry, theme_service)
        self._overlay_manager = OverlayManager()
        self._top_overlay = TopOverlay(parent=self)

        # Current composition. None until load_spec() is called.
        self._build_result: BuildResult | None = None
        self._root_widget: QWidget | None = None

        # The Workspace has a single child: the root widget produced
        # by the LayoutRenderer. A QVBoxLayout keeps it filling the
        # Workspace.
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        # The TopOverlay is registered from the start so that callers
        # can access it via ``top_overlay()`` even before the first
        # ``load_spec()``. Its widget is a child of the Workspace;
        # the OverlayManager does not add it to the layout.
        self._overlay_manager.register(self._top_overlay)
        self._top_overlay.widget().setParent(self)

    # ----- Public API -----------------------------------------------

    def load_spec(self, spec: ModuleUISpec) -> None:
        """Materialize the given ModuleUISpec.

        Replaces any previous composition. After this call:

        - ``areas()`` returns the Areas of the new composition.
        - The visual tree reflects the new LayoutTree.
        - Every registered Overlay has been repositioned.
        """
        # Drop any previous composition.
        self.clear()

        # Build the domain structures.
        result = self._layout_builder.build(spec)
        self._build_result = result

        # Render the LayoutTree.
        root = self._layout_renderer.render(result.tree)
        self._root_widget = root
        self._root_layout.addWidget(root)

        # The TopOverlay must be a child of the Workspace so it can
        # float above the root widget. Reassert the parent here in
        # case the previous clear() detached it.
        self._top_overlay.widget().setParent(self)
        self._top_overlay.widget().raise_()

        # Position every Overlay according to the current geometry.
        # At this point the widgets may not yet have been laid out
        # by Qt; the bounds will be recomputed on the first resize.
        # If Qt has already laid them out, the bounds are accurate
        # immediately.
        self._reposition_overlays()

    def clear(self) -> None:
        """Remove the current composition.

        The Workspace keeps its registries and its TopOverlay. Only
        the rendered composition and the areas from the previous
        spec are removed.
        """
        # Detach and destroy the root widget and everything under it.
        if self._root_widget is not None:
            self._root_layout.removeWidget(self._root_widget)
            self._root_widget.setParent(None)
            self._root_widget.deleteLater()
            self._root_widget = None

        # Clear the renderer's widget cache so the next render()
        # creates fresh widgets.
        self._layout_renderer.clear_cache()

        # Forget the previous build result.
        self._build_result = None

    def areas(self) -> tuple[Area, ...]:
        """Return the Areas of the current composition.

        Returns an empty tuple when no spec has been loaded.
        """
        if self._build_result is None:
            return ()
        return self._build_result.areas

    def area_manager(self) -> AreaManager | None:
        """Return the AreaManager of the current composition.

        Returns None when no spec has been loaded.
        """
        if self._build_result is None:
            return None
        return self._build_result.area_manager

    def overlay_manager(self) -> OverlayManager:
        """Return the OverlayManager.

        The manager is stable across ``load_spec()`` calls: the
        Workspace owns a single instance.
        """
        return self._overlay_manager

    def top_overlay(self) -> TopOverlay:
        """Return the shared Top Bar Overlay."""
        return self._top_overlay

    def is_loaded(self) -> bool:
        """Return True if a composition has been loaded."""
        return self._build_result is not None

    # ----- Qt events ------------------------------------------------

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        """Reposition Overlays when the Workspace is resized.

        The AreaWidgets are resized by the QSplitters they live in.
        As soon as the widgets' geometries change, the Region bounds
        change as well. This handler recomputes the bounds and asks
        the OverlayManager to reposition every Overlay.
        """
        super().resizeEvent(event)
        self._reposition_overlays()

    # ----- Internals ------------------------------------------------

    def _reposition_overlays(self) -> None:
        """Compute the current Region bounds and reposition Overlays.

        The bounds are derived from the current geometry of the
        AreaWidgets cached by the LayoutRenderer. If the widgets
        have not been laid out yet, their geometries are zero-sized
        rectangles; the Overlays are repositioned to zero-sized
        bounds, which is a valid intermediate state. The next
        resizeEvent will produce the correct bounds.
        """
        bounds_by_placement = self._layout_renderer.compute_region_bounds()
        regions = self._regions_from_bounds(bounds_by_placement)
        self._overlay_manager.reposition_all(regions)

    def _regions_from_bounds(
        self,
        bounds_by_placement: dict[Placement, Bounds],
    ) -> tuple[Region, ...]:
        """Build Regions from the current AreaManager and bounds.

        Every Placement that has both Areas in the current
        composition and bounds computed by the renderer produces a
        Region. The Region carries the Areas from the AreaManager
        so that downstream consumers (Overlays, future layout I/O)
        can inspect which Areas belong to which Region.
        """
        manager = self.area_manager()
        if manager is None:
            return ()

        regions: list[Region] = []
        for placement, bounds in bounds_by_placement.items():
            areas = tuple(area for area in manager.areas() if area.placement is placement)
            if not areas:
                continue
            regions.append(
                Region(
                    region_id=placement.value,
                    bounds=bounds,
                    areas=areas,
                    semantic_role=placement,
                )
            )
        return tuple(regions)
