"""Integration tests for the MainWindow Top Bar (Phase 2, Section 10.10)."""

from __future__ import annotations

import pytest
from tests.conftest import make_icon_provider, make_theme_service

from cranioz.application.event_bus import EventBus
from cranioz.application.project.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from cranioz.application.project.project_access_policy import (
    AllowAllProjectAccessPolicy,
)
from cranioz.application.project.project_manager import ProjectManager
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.ui.editors.editor_registry import EditorRegistry
from cranioz.ui.main_window import MainWindow
from cranioz.ui.theme.tokens import ThemeMode
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.placement import Placement
from cranioz.ui.workspace.specs.area_spec import AreaSpec
from cranioz.ui.workspace.specs.editor_layout_spec import (
    EditorLayoutSpec,
)
from cranioz.ui.workspace.specs.module_ui_spec import ModuleUISpec
from cranioz.ui.workspace.structure import (
    ExtrasSegment,
    HomeSegment,
    ModulesSegment,
)
from cranioz.ui.workspace.workspace import Workspace
from cranioz.ui.workspace.workspace_spec import (
    PLACEHOLDER_EDITOR_CLASS,
    PLACEHOLDER_EDITOR_ID,
)


def _build_workspace_with_full_spec(qtbot) -> Workspace:
    """Build a Workspace loaded with a four-Area spec.

    Each Area hosts the placeholder Editor, so none is empty. The
    Workspace is shown and given a real size so that the
    ``compute_region_bounds`` call in the tests returns non-zero
    geometry.

    The Workspace hides Left, Right and Bottom by default (the
    prototype shows only the Central Area on first load). The helper
    shows them explicitly so the tests below start from a layout
    where all four Areas are visible.
    """
    repository = InMemoryProjectRepository()
    manager = ProjectManager(
        repository=repository,
        event_bus=EventBus(),
        access_policy=AllowAllProjectAccessPolicy(),
    )
    project_id = ProjectId("p-test")
    manager.create_project(
        "test-actor",
        project_id=project_id,
        project_name="Test",
        patient_id=PatientId("pat-test"),
        patient_display_name="Test",
        clinical_procedure="test",
    )
    context = manager.open_project("test-actor", project_id)

    editor_registry = EditorRegistry()
    editor_registry.register(PLACEHOLDER_EDITOR_ID, PLACEHOLDER_EDITOR_CLASS)

    theme_service = make_theme_service(ThemeMode.DARK)
    icon_provider = make_icon_provider(theme_service)

    workspace = Workspace(
        editor_registry=editor_registry,
        tool_registry=ToolRegistry(),
        theme_service=theme_service,
        icon_provider=icon_provider,
        project_context=context,
    )
    qtbot.addWidget(workspace)
    workspace.resize(800, 600)
    workspace.show()
    qtbot.wait(50)

    spec = ModuleUISpec(
        areas=(
            AreaSpec(
                area_id="area.left",
                title="Left",
                placement=Placement.LEFT,
                editor_layout=EditorLayoutSpec.leaf(PLACEHOLDER_EDITOR_ID),
            ),
            AreaSpec(
                area_id="area.central",
                title="Central",
                placement=Placement.CENTRAL,
                editor_layout=EditorLayoutSpec.leaf(PLACEHOLDER_EDITOR_ID),
            ),
            AreaSpec(
                area_id="area.right",
                title="Right",
                placement=Placement.RIGHT,
                editor_layout=EditorLayoutSpec.leaf(PLACEHOLDER_EDITOR_ID),
            ),
            AreaSpec(
                area_id="area.bottom",
                title="Bottom",
                placement=Placement.BOTTOM,
                editor_layout=EditorLayoutSpec.leaf(PLACEHOLDER_EDITOR_ID),
            ),
        ),
    )
    workspace.load_spec(spec)
    qtbot.wait(50)

    # The Workspace hides lateral Areas by default; show them so the
    # test starts from a fully-visible layout.
    for placement in (Placement.LEFT, Placement.RIGHT, Placement.BOTTOM):
        workspace.set_area_visible(placement, True)
    qtbot.wait(50)

    return workspace


# ----- Top Bar segments injection -----------------------------------


@pytest.mark.qt
@pytest.mark.integration
def test_top_bar_segments_are_injected(
    main_window_with_open_project: MainWindow,
) -> None:
    window = main_window_with_open_project
    workspace = window.current_workspace()
    assert workspace is not None

    overlay = workspace.top_overlay()
    assert overlay.left_segment().findChild(HomeSegment) is not None
    assert overlay.center_segment().findChild(ModulesSegment) is not None
    assert overlay.right_segment().findChild(ExtrasSegment) is not None


# ----- Area toggles from the Top Bar --------------------------------


@pytest.mark.qt
@pytest.mark.integration
def test_home_toggle_left_hides_and_shows_area(
    main_window_with_open_project: MainWindow,
    qtbot,
) -> None:
    window = main_window_with_open_project
    workspace = window.current_workspace()
    assert workspace is not None

    state = workspace.layout_state()
    home = workspace.top_overlay().left_segment().findChild(HomeSegment)
    assert home is not None

    # Left starts hidden (the prototype shows only the Central Area
    # on first load; the Top Bar toggles the lateral Areas on).
    assert state.is_visible(Placement.LEFT) is False

    home.toggle_area_left_requested.emit()
    qtbot.wait(50)
    assert state.is_visible(Placement.LEFT) is True

    home.toggle_area_left_requested.emit()
    qtbot.wait(50)
    assert state.is_visible(Placement.LEFT) is False


@pytest.mark.qt
@pytest.mark.integration
def test_extras_toggle_bottom_and_right(
    main_window_with_open_project: MainWindow,
    qtbot,
) -> None:
    window = main_window_with_open_project
    workspace = window.current_workspace()
    assert workspace is not None

    state = workspace.layout_state()
    extras = workspace.top_overlay().right_segment().findChild(ExtrasSegment)
    assert extras is not None

    # Bottom and Right start hidden, like Left.
    assert state.is_visible(Placement.BOTTOM) is False
    assert state.is_visible(Placement.RIGHT) is False

    extras.toggle_area_bottom_requested.emit()
    qtbot.wait(50)
    assert state.is_visible(Placement.BOTTOM) is True
    extras.toggle_area_bottom_requested.emit()
    qtbot.wait(50)
    assert state.is_visible(Placement.BOTTOM) is False

    extras.toggle_area_right_requested.emit()
    qtbot.wait(50)
    assert state.is_visible(Placement.RIGHT) is True
    extras.toggle_area_right_requested.emit()
    qtbot.wait(50)
    assert state.is_visible(Placement.RIGHT) is False


# ----- Hidden Areas are excluded from Region bounds -----------------


@pytest.mark.qt
@pytest.mark.integration
def test_hidden_area_is_excluded_from_region_bounds(qtbot) -> None:
    """Hiding an Area removes it from the Region bounds.

    This is what the ``Area.visible`` filter in
    ``LayoutRenderer.compute_region_bounds`` and in
    ``Workspace._regions_from_bounds`` protects. Without them, the
    TopOverlay would be positioned over a Region that includes the
    hidden Area.
    """
    workspace = _build_workspace_with_full_spec(qtbot)

    # All four Areas are visible (the helper shows them explicitly).
    bounds_before = workspace._layout_renderer.compute_region_bounds(workspace)  # noqa: SLF001
    assert Placement.LEFT in bounds_before
    assert Placement.CENTRAL in bounds_before
    assert Placement.RIGHT in bounds_before
    assert Placement.BOTTOM in bounds_before

    # Hide the Left Area.
    workspace.set_area_visible(Placement.LEFT, False)
    qtbot.wait(50)

    # The Left Region is gone from the bounds.
    bounds_after = workspace._layout_renderer.compute_region_bounds(workspace)  # noqa: SLF001
    assert Placement.LEFT not in bounds_after
    assert Placement.CENTRAL in bounds_after
    assert Placement.RIGHT in bounds_after
    assert Placement.BOTTOM in bounds_after

    # Show it again: the Left Region reappears.
    workspace.set_area_visible(Placement.LEFT, True)
    qtbot.wait(50)

    bounds_restored = workspace._layout_renderer.compute_region_bounds(workspace)  # noqa: SLF001
    assert Placement.LEFT in bounds_restored


# ----- Toggling Areas from the Top Bar ------------------------------


@pytest.mark.qt
@pytest.mark.integration
def test_toggling_area_left_shows_and_hides_it(
    main_window_with_open_project: MainWindow,
    qtbot,
) -> None:
    """The Left toggle shows/hides the Left Area and reflows the layout."""
    window = main_window_with_open_project
    workspace = window.current_workspace()
    assert workspace is not None

    state = workspace.layout_state()
    home = workspace.top_overlay().left_segment().findChild(HomeSegment)
    assert home is not None

    # Left starts hidden.
    assert state.is_visible(Placement.LEFT) is False
    left_area = next(
        (a for a in workspace.areas() if a.placement is Placement.LEFT),
        None,
    )
    assert left_area is not None
    assert left_area.visible is False

    # Toggle on: Left becomes visible and gets real geometry.
    home.toggle_area_left_requested.emit()
    qtbot.wait(50)
    assert state.is_visible(Placement.LEFT) is True
    assert left_area.visible is True
    left_widget = workspace._layout_renderer.cached_area_widget(  # noqa: SLF001
        left_area.area_id
    )
    assert left_widget is not None
    assert not left_widget.isHidden()
    assert left_widget.width() > 0

    # Toggle off: Left hides again.
    home.toggle_area_left_requested.emit()
    qtbot.wait(50)
    assert state.is_visible(Placement.LEFT) is False
    assert left_area.visible is False
