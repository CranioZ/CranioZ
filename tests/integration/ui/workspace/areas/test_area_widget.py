"""Integration tests for AreaWidget.

The AreaWidget is the first widget in CranioZ that materializes the
contents of a single Area: the Editors' content widgets (and, inside
each Editor, the View Layout Tree with its View-level Toolbars).

Per ADR-0013, multiple Editors are organized in a QSplitter (the
Editor Layout Tree), not a QTabWidget.

Per ADR-0013 §2.6, Toolbars are declared and materialized by the
ViewLayoutRenderer inside each Editor, not by the AreaWidget. The
DummyEditor used in these tests declares ToolbarSpecs but does not
materialize them itself, so the AreaWidget contains no Toolbar.
These tests therefore assert that no Toolbar appears at the Area
level; the Toolbar materialization is covered by
test_view_layout_renderer_toolbars.py.

These tests use qtbot: an AreaWidget is a real QWidget, and the
Editors it hosts (DummyEditor) return a QLabel as content. A
QApplication is therefore required.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QLabel, QSplitter, QTabWidget, QWidget
from tests.conftest import make_icon_provider, make_theme_service

from cranioz.ui.editors.builtin.test_editor import DummyEditor
from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.theme.tokens import ThemeMode
from cranioz.ui.toolbars.base import Toolbar
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.areas.area import Area
from cranioz.ui.workspace.areas.area_widget import AreaWidget
from cranioz.ui.workspace.areas.placement import Placement

# ----- Local helpers ------------------------------------------------


def _area(
    area_id: str = "area.central",
    title: str = "Central",
    placement: Placement = Placement.CENTRAL,
) -> Area:
    return Area(area_id=area_id, title=title, placement=placement)


def _add_editor(
    area: Area,
    editor_id: str,
    title: str | None = None,
    toolbar_orientation=None,
) -> DummyEditor:
    """Create a DummyEditor, add it to the Area, and return it.

    The DummyEditor declares one ToolbarSpec with tool.log and
    tool.toggle. The AreaWidget does not materialize it (ADR-0013
    §2.6); the DummyEditor does not use a ViewLayoutRenderer, so the
    Toolbar remains a declaration only.
    """
    kwargs = {"editor_id": editor_id, "title": title or editor_id}
    if toolbar_orientation is not None:
        kwargs["toolbar_orientation"] = toolbar_orientation
    editor = DummyEditor(**kwargs)
    area.add_editor(editor)
    return editor


# ----- Fixtures local to this module --------------------------------


@pytest.fixture
def tool_registry() -> ToolRegistry:
    """A ToolRegistry with LogTool and ToggleTool registered."""
    registry = ToolRegistry()
    registry.register("tool.log", LogTool)
    registry.register("tool.toggle", ToggleTool)
    return registry


@pytest.fixture
def theme_service() -> ThemeService:
    """Default ThemeService (dark theme)."""
    return make_theme_service(ThemeMode.DARK)


@pytest.fixture
def icon_provider(theme_service: ThemeService) -> IconProvider:
    """IconProvider bound to the same ThemeService the widgets use."""
    return make_icon_provider(theme_service)


# ----- Empty Area ---------------------------------------------------


def test_area_widget_creates_placeholder_when_empty(
    qtbot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    icon_provider: IconProvider,
) -> None:
    area = _area()
    widget = AreaWidget(area, tool_registry, theme_service, icon_provider=icon_provider)
    qtbot.addWidget(widget)

    labels = widget.findChildren(QLabel)
    assert len(labels) == 1
    assert "empty" in labels[0].text().lower()


def test_area_widget_placeholder_includes_area_title(
    qtbot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    icon_provider: IconProvider,
) -> None:
    area = _area(title="Central")
    widget = AreaWidget(area, tool_registry, theme_service, icon_provider=icon_provider)
    qtbot.addWidget(widget)

    labels = widget.findChildren(QLabel)
    assert len(labels) == 1
    assert "Central" in labels[0].text()


def test_area_widget_empty_has_no_splitter(
    qtbot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    icon_provider: IconProvider,
) -> None:
    area = _area()
    widget = AreaWidget(area, tool_registry, theme_service, icon_provider=icon_provider)
    qtbot.addWidget(widget)

    assert widget.findChild(QSplitter) is None


# ----- Single-Editor Area -------------------------------------------


def test_area_widget_no_splitter_with_one_editor(
    qtbot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    icon_provider: IconProvider,
) -> None:
    area = _area()
    _add_editor(area, "editor.patient")

    widget = AreaWidget(area, tool_registry, theme_service, icon_provider=icon_provider)
    qtbot.addWidget(widget)

    # A single Editor is rendered directly (no QSplitter).
    assert widget.findChild(QSplitter) is None


def test_area_widget_renders_content_widget_of_single_editor(
    qtbot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    icon_provider: IconProvider,
) -> None:
    area = _area()
    editor = _add_editor(area, "editor.patient")

    widget = AreaWidget(area, tool_registry, theme_service, icon_provider=icon_provider)
    qtbot.addWidget(widget)

    content = editor.content_widget()
    assert content is not None
    assert widget.isAncestorOf(content)


def test_area_widget_does_not_materialize_toolbars_of_single_editor(
    qtbot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    icon_provider: IconProvider,
) -> None:
    """ADR-0013 §2.6: Toolbars are materialized by the Editor, not the Area.

    The DummyEditor declares one ToolbarSpec but does not use a
    ViewLayoutRenderer, so the Toolbar is not materialized anywhere.
    The AreaWidget must not create Toolbars of its own.
    """
    area = _area()
    _add_editor(area, "editor.patient")

    widget = AreaWidget(area, tool_registry, theme_service, icon_provider=icon_provider)
    qtbot.addWidget(widget)

    assert widget.findChildren(Toolbar) == []


def test_area_widget_editor_container_has_no_toolbar_children(
    qtbot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    icon_provider: IconProvider,
) -> None:
    """The Editor container exists (named) but has no Toolbar inside it.

    Per ADR-0013 §2.6, Toolbars live inside the Editor's View Layout
    Tree, not inside the Area-level Editor container. The container's
    only child is the Editor's ``content_widget()``.
    """
    area = _area()
    editor = _add_editor(area, "editor.a")

    widget = AreaWidget(area, tool_registry, theme_service, icon_provider=icon_provider)
    qtbot.addWidget(widget)

    container = widget.findChild(
        QWidget,
        f"area_widget.{area.area_id}.editor.{editor.editor_id}",
    )
    assert container is not None
    assert container.isAncestorOf(editor.content_widget())

    # No Toolbar was materialized by the AreaWidget.
    assert container.findChildren(Toolbar) == []


# ----- Multi-Editor Area --------------------------------------------


def test_area_widget_uses_qsplitter_for_multiple_editors(
    qtbot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    icon_provider: IconProvider,
) -> None:
    """Multiple Editors are rendered in a QSplitter, not QTabWidget (ADR-0013)."""
    area = _area()
    _add_editor(area, "editor.a", title="Alpha")
    _add_editor(area, "editor.b", title="Beta")

    widget = AreaWidget(area, tool_registry, theme_service, icon_provider=icon_provider)
    qtbot.addWidget(widget)

    splitter = widget.findChild(QSplitter)
    assert splitter is not None
    assert splitter.count() == 2


def test_area_widget_no_tabwidget_with_multiple_editors(
    qtbot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    icon_provider: IconProvider,
) -> None:
    """Tabs are removed; the split tree is the organization (ADR-0013)."""

    area = _area()
    _add_editor(area, "editor.a")
    _add_editor(area, "editor.b")

    widget = AreaWidget(area, tool_registry, theme_service, icon_provider=icon_provider)
    qtbot.addWidget(widget)

    assert widget.findChild(QTabWidget) is None


def test_area_widget_multiple_editors_content_present(
    qtbot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    icon_provider: IconProvider,
) -> None:
    area = _area()
    editor_a = _add_editor(area, "editor.a")
    editor_b = _add_editor(area, "editor.b")

    widget = AreaWidget(area, tool_registry, theme_service, icon_provider=icon_provider)
    qtbot.addWidget(widget)

    assert widget.isAncestorOf(editor_a.content_widget())
    assert widget.isAncestorOf(editor_b.content_widget())


# ----- Metadata -----------------------------------------------------


def test_area_widget_exposes_area_id(
    qtbot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    icon_provider: IconProvider,
) -> None:
    area = _area(area_id="area.left", title="Left", placement=Placement.LEFT)
    widget = AreaWidget(area, tool_registry, theme_service, icon_provider=icon_provider)
    qtbot.addWidget(widget)

    assert widget.area_id == "area.left"


# ----- Refresh ------------------------------------------------------


def test_area_widget_refresh_rebuilds_from_area(
    qtbot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    icon_provider: IconProvider,
) -> None:
    """refresh() reflects changes to the Area model."""
    area = _area()
    widget = AreaWidget(area, tool_registry, theme_service, icon_provider=icon_provider)
    qtbot.addWidget(widget)

    labels_before = widget.findChildren(QLabel)
    assert len(labels_before) == 1
    assert "empty" in labels_before[0].text().lower()

    editor = _add_editor(area, "editor.patient")
    widget.refresh()

    labels_after = widget.findChildren(QLabel)
    assert len(labels_after) == 1
    assert "empty" not in labels_after[0].text().lower()
    assert widget.isAncestorOf(editor.content_widget())

    # ADR-0013 §2.6: the AreaWidget does not materialize Toolbars.
    assert widget.findChildren(Toolbar) == []


def test_area_widget_refresh_idempotent(
    qtbot,
    tool_registry: ToolRegistry,
    theme_service: ThemeService,
    icon_provider: IconProvider,
) -> None:
    """Calling refresh() twice with no model change produces the same structure."""
    area = _area()
    _add_editor(area, "editor.patient")

    widget = AreaWidget(area, tool_registry, theme_service, icon_provider=icon_provider)
    qtbot.addWidget(widget)

    toolbars_before = widget.findChildren(Toolbar)
    widget.refresh()
    toolbars_after = widget.findChildren(Toolbar)

    # Neither refresh produced Toolbars; the count is stable at zero.
    assert toolbars_before == toolbars_after == []
