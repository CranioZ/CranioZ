"""Shared pytest fixtures for CranioZ tests."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from PySide6.QtWidgets import QApplication

from cranioz.ui.editors.builtin.test_editor import DummyEditor
from cranioz.ui.theme.service import ThemeName, ThemeService
from cranioz.ui.toolbars.specification import (
    ToolbarOrientation,
    ToolbarSpec,
    ToolbarVisibilityMode,
)
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry

# ----- Qt ------------------------------------------------------------


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """Session-scoped QApplication.

    Creating multiple QApplication instances breaks Qt, so this fixture
    guarantees a single instance is reused across the entire test session.
    """
    app = QApplication.instance()
    if isinstance(app, QApplication):
        return app
    return QApplication([])


# ----- Theme ---------------------------------------------------------


@pytest.fixture
def theme_service() -> ThemeService:
    """Default ThemeService (dark theme)."""
    return ThemeService(theme=ThemeName.DARK)


# ----- Tools and Registry --------------------------------------------


@pytest.fixture
def tool_registry() -> ToolRegistry:
    """Registry with LogTool and ToggleTool registered."""
    registry = ToolRegistry()
    registry.register("tool.log", LogTool)
    registry.register("tool.toggle", ToggleTool)
    return registry


@pytest.fixture
def make_test_editor() -> Callable[..., DummyEditor]:
    """Factory to build TestEditor instances with a given editor_id."""

    def _factory(
        editor_id: str = "editor.test",
        title: str = "Test Editor",
    ) -> DummyEditor:
        return DummyEditor(editor_id=editor_id, title=title)

    return _factory

# ----- Toolbar spec factory ------------------------------------------


@pytest.fixture
def make_toolbar_spec() -> Callable[..., ToolbarSpec]:
    """Factory to build ToolbarSpec with sensible defaults."""

    def _factory(
        toolbar_id: str = "tb.test",
        title: str = "Test Toolbar",
        orientation: ToolbarOrientation = ToolbarOrientation.HORIZONTAL,
        tool_ids: tuple[str, ...] = (),
        visibility_mode: ToolbarVisibilityMode = ToolbarVisibilityMode.ALWAYS,
    ) -> ToolbarSpec:
        return ToolbarSpec(
            toolbar_id=toolbar_id,
            title=title,
            orientation=orientation,
            tool_ids=tool_ids,
            visibility_mode=visibility_mode,
        )

    return _factory
