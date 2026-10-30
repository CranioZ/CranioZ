"""Integration tests for AreaWidget.

The AreaWidget is the first widget in CranioZ that materializes the
contents of a single Area: its Editors' Toolbars (inside each Editor)
and their content widgets.

Per ADR-0013, multiple Editors are organized in a QSplitter (the
Editor Layout Tree), not a QTabWidget. The tests below validate this
new behavior, as well as the placement of Toolbars inside the Editor
(ADR-0002).

These tests use qtbot: an AreaWidget is a real QWidget, and the
Editors it hosts (DummyEditor) return a QLabel as content. A
QApplication is therefore required.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QLabel, QSplitter, QTabWidget, QWidget

from cranioz.ui.editors.builtin.test_editor import DummyEditor
from cranioz.ui.theme.service import ThemeName, ThemeService
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
    tool.toggle. This is enough to exercise Toolbar materialization
    inside the AreaWidget.
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
    return ThemeService(theme=ThemeName.DARK)


# ----- Empty Area ---------------------------------------------------


def test_area_widget_creates_placeholder_when_empty(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    area = _area()
    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    labels = widget.findChildren(QLabel)
    assert len(labels) == 1
    assert "empty" in labels[0].text().lower()


def test_area_widget_placeholder_includes_area_title(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    area = _area(title="Central")
    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    labels = widget.findChildren(QLabel)
    assert len(labels) == 1
    assert "Central" in labels[0].text()


def test_area_widget_empty_has_no_splitter(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    area = _area()
    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    assert widget.findChild(QSplitter) is None


# ----- Single-Editor Area -------------------------------------------


def test_area_widget_no_splitter_with_one_editor(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    area = _area()
    _add_editor(area, "editor.patient")

    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    # A single Editor is rendered directly (no QSplitter).
    assert widget.findChild(QSplitter) is None


def test_area_widget_renders_content_widget_of_single_editor(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    area = _area()
    editor = _add_editor(area, "editor.patient")

    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    content = editor.content_widget()
    assert content is not None
    assert widget.isAncestorOf(content)


def test_area_widget_renders_toolbars_of_single_editor(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    area = _area()
    _add_editor(area, "editor.patient")

    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    toolbars = widget.findChildren(Toolbar)
    assert len(toolbars) == 1
    assert set(toolbars[0].tool_ids()) == {"tool.log", "tool.toggle"}


def test_area_widget_toolbar_is_inside_editor_container(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    """Per ADR-0002, the Toolbar is inside the Editor, not beside it."""
    area = _area()
    editor = _add_editor(area, "editor.a")

    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    container = widget.findChild(
        QWidget,
        f"area_widget.{area.area_id}.editor.{editor.editor_id}",
    )
    assert container is not None

    # The Toolbar is a descendant of the Editor container.
    toolbars = container.findChildren(Toolbar)
    assert len(toolbars) == 1


# ----- Multi-Editor Area --------------------------------------------


def test_area_widget_uses_qsplitter_for_multiple_editors(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    """Multiple Editors are rendered in a QSplitter, not QTabWidget (ADR-0013)."""
    area = _area()
    _add_editor(area, "editor.a", title="Alpha")
    _add_editor(area, "editor.b", title="Beta")

    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    splitter = widget.findChild(QSplitter)
    assert splitter is not None
    assert splitter.count() == 2


def test_area_widget_no_tabwidget_with_multiple_editors(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    """Tabs are removed; the split tree is the organization (ADR-0013)."""

    area = _area()
    _add_editor(area, "editor.a")
    _add_editor(area, "editor.b")

    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    assert widget.findChild(QTabWidget) is None


def test_area_widget_multiple_editors_content_present(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    area = _area()
    editor_a = _add_editor(area, "editor.a")
    editor_b = _add_editor(area, "editor.b")

    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    assert widget.isAncestorOf(editor_a.content_widget())
    assert widget.isAncestorOf(editor_b.content_widget())


# ----- Metadata -----------------------------------------------------


def test_area_widget_exposes_area_id(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    area = _area(area_id="area.left", title="Left", placement=Placement.LEFT)
    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    assert widget.area_id == "area.left"


# ----- Refresh ------------------------------------------------------


def test_area_widget_refresh_rebuilds_from_area(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    """refresh() reflects changes to the Area model."""
    area = _area()
    widget = AreaWidget(area, tool_registry, theme_service)
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

    toolbars = widget.findChildren(Toolbar)
    assert len(toolbars) == 1


def test_area_widget_refresh_idempotent(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    """Calling refresh() twice with no model change produces the same structure."""
    area = _area()
    _add_editor(area, "editor.patient")

    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    toolbars_before = widget.findChildren(Toolbar)
    widget.refresh()
    toolbars_after = widget.findChildren(Toolbar)

    assert len(toolbars_before) == len(toolbars_after) == 1
