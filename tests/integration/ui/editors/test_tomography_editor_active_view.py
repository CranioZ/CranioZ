"""Tests for the TomographyEditor active view and Toolbar behavior.

Block 5.5: Editor-level Toolbars and View-level Toolbars are
temporarily disabled to reduce visual noise in the prototype. The
tests that verified the presence and emphasis of those Toolbars are
marked with ``@pytest.mark.skip``. When the Toolbars are re-enabled,
remove the skip decorators and restore the original assertions.

VTK is not initialized in these tests: the ``Viewport3DView`` is
patched to a fake QWidget *before* the TomographyEditor is
instantiated. This avoids the OpenGL context creation that hangs in
headless CI.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QWidget

from cranioz.editors.core.editor.editor_context import EditorContext
from cranioz.editors.views.mpr_viewer.view import MPRView
from cranioz.ui.editors.tomography.editor import TomographyEditor
from cranioz.ui.toolbars.base import Toolbar
from cranioz.ui.toolbars.specification import ToolbarSpec

# ----- Fake Viewport3DView -----------------------------------------


class _FakeViewport3DView(QWidget):
    """A QWidget that mimics the Viewport3DView API without VTK.

    The ViewLayoutRenderer needs ``view_id``, ``view_type``,
    ``content_widget()``, ``activation_widget()``,
    ``toolbar_specs()`` and ``control_panel_specs()``. This fake
    provides all of them. It is NOT an instance of Viewport3DView,
    but the tests only check that ``views()`` returns objects that
    behave like Views, so this is sufficient.
    """

    def __init__(self, view_id: str = "view.3d", **kwargs: object) -> None:
        super().__init__()
        self.view_id = view_id
        self.view_type = "3d"
        self.setObjectName(f"fake_viewport_3d.{view_id}")
        self.setMinimumSize(200, 150)

    def content_widget(self) -> QWidget:
        return self

    def activation_widget(self) -> QWidget:
        return self

    def toolbar_specs(self) -> list[ToolbarSpec]:
        return []

    def control_panel_specs(self) -> list[ToolbarSpec]:
        return []

    def dispose(self) -> None:
        pass


# ----- Helpers ------------------------------------------------------


def _make_editor_with_context() -> TomographyEditor:
    """Build a TomographyEditor with a minimal EditorContext.

    The ``Viewport3DView`` is patched to ``_FakeViewport3DView``
    *before* the TomographyEditor is instantiated, so the real VTK
    pipeline is never created. This avoids the OpenGL context
    creation that hangs in headless CI.
    """
    with patch(
        "cranioz.ui.editors.tomography.editor.Viewport3DView",
        _FakeViewport3DView,
    ):
        editor = TomographyEditor()
    context = EditorContext(
        editor_id=editor.editor_id,
        tool_registry=MagicMock(name="tool_registry"),
        theme_service=MagicMock(name="theme_service"),
        icon_provider=MagicMock(name="icon_provider"),
        translation_service=None,
    )
    editor.initialize(context)
    return editor


# ----- Tests --------------------------------------------------------


@pytest.mark.qt
@pytest.mark.integration
def test_editor_materializes_four_views_and_no_editor_toolbars(qtbot) -> None:
    """The 2x2 grid has 4 Views and the Editor materializes no Toolbars."""
    editor = _make_editor_with_context()
    content = editor.content_widget()
    qtbot.addWidget(content)

    views = editor.views()
    assert len(views) == 4
    # The 3D view is a _FakeViewport3DView (a QWidget). The two MPR
    # views are real.
    assert isinstance(views[0], MPRView)
    assert isinstance(views[1], MPRView)
    assert isinstance(views[2], MPRView)
    assert isinstance(views[3], _FakeViewport3DView)

    # No Editor-level Toolbars are materialized (Block 5.5).
    editor_toolbars = content.findChildren(Toolbar)
    editor_toolbar_ids = {tb.spec.toolbar_id for tb in editor_toolbars}
    assert editor_toolbar_ids == set(), (
        f"Expected no Editor-level Toolbars, found: {editor_toolbar_ids}"
    )

    editor.dispose()


@pytest.mark.skip(reason="View-level Toolbars temporarily disabled (Block 5.5)")
@pytest.mark.qt
@pytest.mark.integration
def test_activating_view_emphasizes_its_view_level_toolbars(qtbot) -> None:
    """The original test, kept for when the Toolbars are re-enabled."""
    editor = _make_editor_with_context()
    content = editor.content_widget()
    qtbot.addWidget(content)

    axial_view = editor.views()[0]
    editor.set_active_view(axial_view.view_id)

    view_toolbars = [
        tb for tb in content.findChildren(Toolbar) if tb.spec.toolbar_id.startswith("toolbar.view.")
    ]
    by_id = {tb.spec.toolbar_id: tb for tb in view_toolbars}

    axial_tools = by_id["toolbar.view.axial.tools"]
    assert axial_tools.is_emphasized()

    editor.dispose()


@pytest.mark.skip(reason="Editor-level Toolbars temporarily disabled (Block 5.5)")
@pytest.mark.qt
@pytest.mark.integration
def test_editor_level_always_toolbar_unaffected(qtbot) -> None:
    """The original test, kept for when the Toolbars are re-enabled."""
    editor = _make_editor_with_context()
    content = editor.content_widget()
    qtbot.addWidget(content)

    editor_toolbars = [
        tb
        for tb in content.findChildren(Toolbar)
        if tb.spec.toolbar_id.startswith("toolbar.tomography.")
    ]
    by_id = {tb.spec.toolbar_id: tb for tb in editor_toolbars}

    axial_view = editor.views()[0]
    editor.set_active_view(axial_view.view_id)

    left_toolbar = by_id["toolbar.tomography.left"]
    assert not left_toolbar.is_emphasized()

    editor.dispose()


# ----- Sanity checks ------------------------------------------------


@pytest.mark.qt
@pytest.mark.integration
def test_editor_content_widget_is_a_widget(qtbot) -> None:
    """The Editor's content_widget() returns a QWidget instance."""
    editor = _make_editor_with_context()
    content = editor.content_widget()
    qtbot.addWidget(content)

    assert isinstance(content, QWidget)

    editor.dispose()


@pytest.mark.qt
@pytest.mark.integration
def test_editor_dispose_clears_content(qtbot) -> None:
    """dispose() detaches the content widget and releases references."""
    editor = _make_editor_with_context()
    content = editor.content_widget()
    qtbot.addWidget(content)

    editor.dispose()

    assert editor._content is None  # noqa: SLF001
    assert editor._view_layout_renderer is None  # noqa: SLF001
