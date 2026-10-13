"""Integration tests for AreaWidget.

The AreaWidget is the first widget in CranioZ that materializes the
contents of a single Area: its Editors' Toolbars, their content
widgets, and tabs when there are multiple Editors.

These tests use qtbot: an AreaWidget is a real QWidget, and the
Editors it hosts (DummyEditor) return a QLabel as content. A
QApplication is therefore required.

What these tests cover:

- Empty Area: placeholder widget is shown.
- Single-Editor Area: no tabs, content is rendered directly.
- Single-Editor Area: Toolbars are materialized.
- Multi-Editor Area: a QTabWidget is created with the expected tabs.
- Tab position is South (bottom of the Area).
- Tabs are closable.
- The active tab matches the Area's active_editor_id.
- Switching tabs emits active_editor_changed.
- Closing a tab emits editor_close_requested.
- The widget exposes its area_id.
- refresh() rebuilds the widget from the Area model.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QLabel, QTabWidget

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


def test_area_widget_empty_has_no_tabs(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    area = _area()
    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    assert widget.findChild(QTabWidget) is None


# ----- Single-Editor Area -------------------------------------------


def test_area_widget_no_tabs_with_one_editor(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    area = _area()
    _add_editor(area, "editor.patient")

    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    assert widget.findChild(QTabWidget) is None


def test_area_widget_renders_content_widget_of_single_editor(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    area = _area()
    editor = _add_editor(area, "editor.patient")

    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    content = editor.content_widget()
    # The content widget is a QLabel whose text is the editor_id.
    # It must be a descendant of the AreaWidget.
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
    # DummyEditor declares tool.log and tool.toggle.
    assert set(toolbars[0].tool_ids()) == {"tool.log", "tool.toggle"}


# ----- Multi-Editor Area --------------------------------------------


def test_area_widget_tabs_with_multiple_editors(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    area = _area()
    _add_editor(area, "editor.a", title="Alpha")
    _add_editor(area, "editor.b", title="Beta")

    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    tabs = widget.findChild(QTabWidget)
    assert tabs is not None
    assert tabs.count() == 2


def test_area_widget_tab_labels_match_editor_titles(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    area = _area()
    _add_editor(area, "editor.a", title="Alpha")
    _add_editor(area, "editor.b", title="Beta")

    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    tabs = widget.findChild(QTabWidget)
    assert tabs is not None
    assert tabs.tabText(0) == "Alpha"
    assert tabs.tabText(1) == "Beta"


def test_area_widget_tab_position_is_south(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    area = _area()
    _add_editor(area, "editor.a", title="Alpha")
    _add_editor(area, "editor.b", title="Beta")

    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    tabs = widget.findChild(QTabWidget)
    assert tabs is not None
    assert tabs.tabPosition() == QTabWidget.TabPosition.South


def test_area_widget_tabs_are_closable(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    area = _area()
    _add_editor(area, "editor.a", title="Alpha")
    _add_editor(area, "editor.b", title="Beta")

    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    tabs = widget.findChild(QTabWidget)
    assert tabs is not None
    assert tabs.tabsClosable() is True


def test_area_widget_active_tab_matches_active_editor(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    area = _area()
    _add_editor(area, "editor.a", title="Alpha")
    _add_editor(area, "editor.b", title="Beta")
    area.set_active_editor("editor.b")

    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    tabs = widget.findChild(QTabWidget)
    assert tabs is not None
    assert tabs.currentIndex() == 1  # editor.b is at index 1


# ----- Signals ------------------------------------------------------


def test_area_widget_emits_active_editor_changed_on_tab_switch(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    area = _area()
    _add_editor(area, "editor.a", title="Alpha")
    _add_editor(area, "editor.b", title="Beta")

    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    tabs = widget.findChild(QTabWidget)
    assert tabs is not None

    with qtbot.waitSignal(widget.active_editor_changed, timeout=1000) as blocker:
        tabs.setCurrentIndex(1)

    assert blocker.args == ["area.central", "editor.b"]


def test_area_widget_emits_close_requested_on_tab_close(
    qtbot, tool_registry: ToolRegistry, theme_service: ThemeService
) -> None:
    area = _area()
    _add_editor(area, "editor.a", title="Alpha")
    _add_editor(area, "editor.b", title="Beta")

    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    tabs = widget.findChild(QTabWidget)
    assert tabs is not None

    with qtbot.waitSignal(widget.editor_close_requested, timeout=1000) as blocker:
        # Emit the signal as if the user clicked the 'X' on the first tab.
        tabs.tabCloseRequested.emit(0)

    assert blocker.args == ["area.central", "editor.a"]


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
    """refresh() reflects changes to the Area model.

    We start with an empty Area, verify the placeholder is shown,
    then add an Editor and call refresh(). The widget must now show
    the Editor's content and no placeholder.
    """
    area = _area()
    widget = AreaWidget(area, tool_registry, theme_service)
    qtbot.addWidget(widget)

    labels_before = widget.findChildren(QLabel)
    assert len(labels_before) == 1
    assert "empty" in labels_before[0].text().lower()

    editor = _add_editor(area, "editor.patient")
    widget.refresh()

    # After refresh: no placeholder, content present, one toolbar.
    labels_after = widget.findChildren(QLabel)
    # The content widget of DummyEditor is itself a QLabel. We expect
    # exactly one QLabel now (the content), not the placeholder.
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
