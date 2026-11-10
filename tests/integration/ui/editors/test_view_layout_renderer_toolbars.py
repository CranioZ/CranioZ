"""Verify that ViewLayoutRenderer materializes View-level Toolbars.

Per ADR-0013 §2.6, each View's Toolbars are rendered around the
View's content_widget(). The tests build a fake View that declares
two Toolbars (one LEFT, one RIGHT) and assert that:
- Both Toolbars appear inside the container.
- The View's content is present.
- The Toolbars are not present in the AreaLayoutRenderer's output
  (proving the separation).
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QLabel, QWidget
from pytestqt.qtbot import QtBot
from tests.conftest import make_icon_provider, make_theme_service

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.editors.view import View
from cranioz.ui.editors.view_layout_renderer import ViewLayoutRenderer
from cranioz.ui.editors.view_layout_spec import ViewLayoutSpec
from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.toolbars.base import Toolbar
from cranioz.ui.toolbars.specification import (
    ToolbarOrientation,
    ToolbarPosition,
    ToolbarSpec,
    ToolbarVisibilityMode,
)
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.area_layout_renderer import (
    AreaLayoutRenderer,
)
from cranioz.ui.workspace.areas.placement import Placement

# ---------------------------------------------------------------------
# Fake Views
# ---------------------------------------------------------------------


class FakeView(View):
    """A View that declares two Toolbars (LEFT tools, RIGHT display)."""

    def __init__(self, view_id: str) -> None:
        super().__init__(view_id=view_id, view_type="fake")
        self._content: QLabel | None = None

    def content_widget(self) -> QWidget:
        if self._content is None:
            self._content = QLabel(f"content of {self.view_id}")
            self._content.setObjectName(f"fake_view.{self.view_id}.content")
        return self._content

    def toolbar_specs(self) -> list[ToolbarSpec]:
        return [
            ToolbarSpec(
                toolbar_id=f"toolbar.{self.view_id}.tools",
                title="Tools",
                orientation=ToolbarOrientation.VERTICAL,
                position=ToolbarPosition.LEFT,
                tool_ids=("tool.log",),
                visibility_mode=ToolbarVisibilityMode.ACTIVE_ONLY,
            )
        ]

    def control_panel_specs(self) -> list[ToolbarSpec]:
        return [
            ToolbarSpec(
                toolbar_id=f"toolbar.{self.view_id}.display",
                title="Display",
                orientation=ToolbarOrientation.VERTICAL,
                position=ToolbarPosition.RIGHT,
                tool_ids=("tool.toggle",),
                visibility_mode=ToolbarVisibilityMode.ACTIVE_ONLY,
            )
        ]

    def dispose(self) -> None:
        if self._content is not None:
            self._content.setParent(None)
            self._content.deleteLater()
            self._content = None


class BareView(View):
    """A View that declares no Toolbars (uses the default empty lists)."""

    def __init__(self, view_id: str) -> None:
        super().__init__(view_id=view_id, view_type="bare")
        self._content: QLabel | None = None

    def content_widget(self) -> QWidget:
        if self._content is None:
            self._content = QLabel(f"content of {self.view_id}")
            self._content.setObjectName(f"bare_view.{self.view_id}.content")
        return self._content

    def dispose(self) -> None:
        if self._content is not None:
            self._content.setParent(None)
            self._content.deleteLater()
            self._content = None


# ---------------------------------------------------------------------
# Fake Editor (module level, not inside a test function)
# ---------------------------------------------------------------------


class _ContainerEditor(Editor):
    """Minimal Editor whose content_widget() returns a pre-built QWidget.

    Used by the separation test to place a View container (with its
    Toolbars) inside an Area, then prove that the AreaLayoutRenderer
    does not add Toolbars of its own.
    """

    def __init__(self, container: QWidget) -> None:
        super().__init__(editor_id="editor.container", title="Container")
        self._container = container

    def content_widget(self) -> QWidget:
        return self._container


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------


@pytest.fixture
def theme_service(qapp) -> ThemeService:
    return make_theme_service()


@pytest.fixture
def icon_provider(theme_service: ThemeService) -> IconProvider:
    return make_icon_provider(theme_service)


@pytest.fixture
def tool_registry(tool_registry: ToolRegistry) -> ToolRegistry:
    """The shared fixture already registers tool.log and tool.toggle."""
    return tool_registry


@pytest.fixture
def renderer(
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    icon_provider: IconProvider,
) -> ViewLayoutRenderer:
    return ViewLayoutRenderer(
        tool_registry=tool_registry,
        theme_service=theme_service,
        icon_provider=icon_provider,
    )


# ---------------------------------------------------------------------
# ViewLayoutRenderer — materialization
# ---------------------------------------------------------------------


def test_view_container_contains_both_toolbars(
    qtbot: QtBot,
    renderer: ViewLayoutRenderer,
) -> None:
    """ADR-0013 §2.6: both LEFT and RIGHT Toolbars are materialized."""
    view = FakeView("view.test")
    spec = ViewLayoutSpec.leaf("view.test")

    container = renderer.render(spec, {"view.test": view})
    qtbot.addWidget(container)

    toolbars = container.findChildren(Toolbar)
    assert len(toolbars) == 2


def test_view_container_left_toolbar_position(
    qtbot: QtBot,
    renderer: ViewLayoutRenderer,
) -> None:
    """The LEFT Toolbar is rendered before the content in the H layout."""
    view = FakeView("view.test")
    spec = ViewLayoutSpec.leaf("view.test")

    container = renderer.render(spec, {"view.test": view})
    qtbot.addWidget(container)

    left_toolbar = next(
        tb
        for tb in container.findChildren(Toolbar)
        if tb.spec.toolbar_id == "toolbar.view.test.tools"
    )
    right_toolbar = next(
        tb
        for tb in container.findChildren(Toolbar)
        if tb.spec.toolbar_id == "toolbar.view.test.display"
    )

    outer_layout = container.layout()
    assert outer_layout is not None

    # In the outer QHBoxLayout: LEFT toolbar, then the inner container, then RIGHT toolbar.
    assert outer_layout.indexOf(left_toolbar) == 0
    assert outer_layout.indexOf(right_toolbar) == outer_layout.count() - 1
    assert outer_layout.indexOf(left_toolbar) < outer_layout.indexOf(right_toolbar)


def test_view_container_content_is_present(
    qtbot: QtBot,
    renderer: ViewLayoutRenderer,
) -> None:
    """The View's content_widget() is placed inside the container."""
    view = FakeView("view.test")
    spec = ViewLayoutSpec.leaf("view.test")

    container = renderer.render(spec, {"view.test": view})
    qtbot.addWidget(container)

    content = view.content_widget()
    assert container.isAncestorOf(content)


def test_view_without_toolbars_has_no_toolbar_children(
    qtbot: QtBot,
    renderer: ViewLayoutRenderer,
) -> None:
    """A View that declares no Toolbars produces a container without Toolbars."""
    view = BareView("view.bare")
    spec = ViewLayoutSpec.leaf("view.bare")

    container = renderer.render(spec, {"view.bare": view})
    qtbot.addWidget(container)

    assert container.findChildren(Toolbar) == []


def test_view_container_is_cached_by_view_id(
    qtbot: QtBot,
    renderer: ViewLayoutRenderer,
) -> None:
    """Rendering the same View twice reuses the same container instance."""
    view = FakeView("view.test")
    spec = ViewLayoutSpec.leaf("view.test")

    container_a = renderer.render(spec, {"view.test": view})
    container_b = renderer.render(spec, {"view.test": view})
    qtbot.addWidget(container_a)

    assert container_a is container_b


def test_clear_cache_disposes_view_containers(
    qtbot: QtBot,
    renderer: ViewLayoutRenderer,
) -> None:
    """clear_cache() detaches containers from the renderer's cache."""
    view = FakeView("view.test")
    spec = ViewLayoutSpec.leaf("view.test")

    container = renderer.render(spec, {"view.test": view})
    qtbot.addWidget(container)

    renderer.clear_cache()

    # Rendering again must produce a new container, not the cached one.
    new_container = renderer.render(spec, {"view.test": view})
    qtbot.addWidget(new_container)
    assert new_container is not container
    view.dispose()


# ---------------------------------------------------------------------
# Separation from AreaLayoutRenderer
# ---------------------------------------------------------------------


def test_area_layout_renderer_does_not_create_view_toolbars(
    qtbot: QtBot,
    renderer: ViewLayoutRenderer,
) -> None:
    """Toolbars materialized by ViewLayoutRenderer are NOT at the Area level.

    We render a View through the ViewLayoutRenderer (getting a container
    with Toolbars inside), then verify that the Area-level renderer's
    output contains no Toolbar widget of its own. This proves the
    responsibility split described in ADR-0013 §2.7.
    """
    # Build the View container (which contains the Toolbars).
    view = FakeView("view.test")
    spec = ViewLayoutSpec.leaf("view.test")
    view_container = renderer.render(spec, {"view.test": view})
    # NOTE: do NOT register view_container with qtbot. It is owned by the
    # renderer (cached by view_id) and, transitively, by the AreaWidget.
    # Registering it would make qtbot try to close() it during teardown,
    # after the renderer's cache was discarded and the C++ object was
    # already deleted, raising RuntimeError.
    assert len(view_container.findChildren(Toolbar)) == 2

    # Editor whose content_widget() is the View container.
    editor = _ContainerEditor(view_container)
    area = Area(
        area_id="area.test",
        title="Test",
        placement=Placement.CENTRAL,
    )
    area.add_editor(editor)

    content_widgets: dict[str, QWidget] = {}
    area_widget = AreaLayoutRenderer().render(area, content_widgets)
    qtbot.addWidget(area_widget)

    # The Area-level renderer wraps the Editor's content but does NOT
    # create Toolbars of its own. The two Toolbars present in the tree
    # come exclusively from the View container we passed in.
    toolbars = area_widget.findChildren(Toolbar)
    assert len(toolbars) == 2
    assert all(
        tb.spec.toolbar_id in {"toolbar.view.test.tools", "toolbar.view.test.display"}
        for tb in toolbars
    )

    view.dispose()
