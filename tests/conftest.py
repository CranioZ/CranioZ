"""Shared pytest fixtures for CranioZ tests."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtWidgets import QApplication

# VTK 9 reports every failed wglMakeCurrent as an error. During tests,
# VTK render windows are created and destroyed rapidly, which triggers
# these spurious reports. They do not affect test outcomes; silence them.
# Keep the variable settable from the shell for debugging.
os.environ.setdefault("VTK_REPORT_OPENGL_ERRORS", "0")

try:
    from vtkmodules.qt.QVTKRenderWindowInteractor import (
        QVTKRenderWindowInteractor,
    )

    _HAS_VTK = True
except ImportError:  # pragma: no cover - VTK is optional
    QVTKRenderWindowInteractor = None  # type: ignore[assignment,misc]
    _HAS_VTK = False

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

_logger = logging.getLogger(__name__)

# ----- Qt ------------------------------------------------------------


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """Session-scoped QApplication with a VTK-friendly surface format.

    The surface format and the shared-context attribute are applied
    *before* the QApplication is instantiated. Applying them after is a
    no-op (Qt freezes the format at construction time), which is what
    produced the ``code 2004`` (unsupported operation) reports.
    """
    app = QApplication.instance()
    if isinstance(app, QApplication):
        return app

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    fmt = QSurfaceFormat()
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)
    fmt.setVersion(3, 2)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)

    return QApplication([])


# ----- VTK cleanup ---------------------------------------------------


@pytest.fixture(autouse=True)
def _finalize_vtk_interactors() -> None:
    """Finalize every live QVTKRenderWindowInteractor after each test.

    Without this, the VTK render window is destroyed by Qt after the
    OpenGL context is already gone, producing a flood of
    ``wglMakeCurrent failed ... code 6`` messages. Finalizing before
    Qt's teardown releases the context cleanly.
    """
    yield
    if not _HAS_VTK:
        return

    for widget in QApplication.allWidgets():
        if isinstance(widget, QVTKRenderWindowInteractor):
            try:
                widget.Finalize()
            except Exception:
                # Finalize can raise if the widget was already torn down
                # by Qt. That is expected during teardown; log at debug
                # so failures remain diagnosable without polluting output.
                _logger.debug(
                    "VTK Finalize failed for %r",
                    widget,
                    exc_info=True,
                )


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
