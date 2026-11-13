"""Tests for ViewLayoutRenderer's ACTIVE_ONLY wiring (Block 4)."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QLabel,
    QWidget,
)
from pytestqt.qtbot import QtBot
from tests.conftest import make_icon_provider, make_theme_service

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.editors.view import View
from cranioz.ui.editors.view_layout_renderer import (
    ViewLayoutRenderer,
    _ViewActivationFilter,
)
from cranioz.ui.editors.view_layout_spec import (
    SplitDirection,
    ViewLayoutSpec,
)
from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.toolbars.base import Toolbar
from cranioz.ui.toolbars.specification import (
    ToolbarOrientation,
    ToolbarPosition,
    ToolbarSpec,
    ToolbarVisibilityMode,
)
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry


class _FakeView(View):
    def __init__(self, view_id: str, *, with_toolbars: bool = True) -> None:
        super().__init__(view_id=view_id, view_type="fake")
        self._with_toolbars = with_toolbars
        self._content: QLabel | None = None

    def content_widget(self) -> QWidget:
        if self._content is None:
            self._content = QLabel(f"content.{self.view_id}")
            self._content.setObjectName(f"fake.{self.view_id}.content")
        return self._content

    def toolbar_specs(self) -> list[ToolbarSpec]:
        if not self._with_toolbars:
            return []
        return [
            ToolbarSpec(
                toolbar_id=f"tb.{self.view_id}.tools",
                title=f"{self.view_id} tools",
                orientation=ToolbarOrientation.VERTICAL,
                position=ToolbarPosition.LEFT,
                tool_ids=("tool.log",),
                visibility_mode=ToolbarVisibilityMode.ACTIVE_ONLY,
            )
        ]

    def dispose(self) -> None:
        if self._content is not None:
            self._content.setParent(None)
            self._content.deleteLater()
            self._content = None


class _FakeEditor(Editor):
    def __init__(self, views: tuple[View, ...]) -> None:
        super().__init__(editor_id="editor.fake", title="Fake")
        self._views = views

    def views(self) -> tuple[View, ...]:
        return self._views

    def content_widget(self) -> QWidget:  # pragma: no cover - not used
        return QWidget()


def _tool_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register("tool.log", LogTool)
    reg.register("tool.toggle", ToggleTool)
    return reg


def _make_renderer(qtbot: QtBot, editor: Editor | None) -> ViewLayoutRenderer:
    theme = make_theme_service()
    icons: IconProvider = make_icon_provider(theme)
    return ViewLayoutRenderer(
        tool_registry=_tool_registry(),
        theme_service=theme,
        icon_provider=icons,
        editor=editor,
    )


def test_default_activation_widget_is_content_widget(qtbot: QtBot) -> None:
    view = _FakeView("view.a")
    qtbot.addWidget(view.content_widget())
    assert view.activation_widget() is view.content_widget()


def test_mouse_press_activates_view(qtbot: QtBot) -> None:
    view_a = _FakeView("view.a")
    view_b = _FakeView("view.b")
    editor = _FakeEditor((view_a, view_b))
    renderer = _make_renderer(qtbot, editor)
    spec = ViewLayoutSpec.split(
        SplitDirection.HORIZONTAL,
        (ViewLayoutSpec.leaf("view.a"), ViewLayoutSpec.leaf("view.b")),
    )
    container = renderer.render(spec, {"view.a": view_a, "view.b": view_b})
    qtbot.addWidget(container)

    emitted: list[str | None] = []
    editor.active_view_changed.connect(emitted.append)

    target = view_a.activation_widget()
    event = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(5, 5),
        QPointF(5, 5),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    # `target.event(event)` bypasses installed event filters.
    # `QApplication.sendEvent` runs them first, which is what the
    # ViewLayoutRenderer relies on.
    QApplication.sendEvent(target, event)

    assert editor.active_view_id == "view.a"
    assert emitted == ["view.a"]


def test_focus_in_activates_view(qtbot: QtBot) -> None:
    view_a = _FakeView("view.a")
    view_b = _FakeView("view.b")
    editor = _FakeEditor((view_a, view_b))
    renderer = _make_renderer(qtbot, editor)
    spec = ViewLayoutSpec.split(
        SplitDirection.HORIZONTAL,
        (ViewLayoutSpec.leaf("view.a"), ViewLayoutSpec.leaf("view.b")),
    )
    container = renderer.render(spec, {"view.a": view_a, "view.b": view_b})
    qtbot.addWidget(container)

    target = view_b.activation_widget()
    QApplication.sendEvent(target, QEvent(QEvent.Type.FocusIn))

    assert editor.active_view_id == "view.b"


def test_hover_does_not_activate(qtbot: QtBot) -> None:
    view_a = _FakeView("view.a")
    editor = _FakeEditor((view_a,))
    renderer = _make_renderer(qtbot, editor)
    spec = ViewLayoutSpec.leaf("view.a")
    container = renderer.render(spec, {"view.a": view_a})
    qtbot.addWidget(container)

    QApplication.sendEvent(
        view_a.activation_widget(), QEvent(QEvent.Type.Enter)
    )

    assert editor.active_view_id is None


def test_active_only_toolbars_start_inactive(qtbot: QtBot) -> None:
    view_a = _FakeView("view.a")
    editor = _FakeEditor((view_a,))
    renderer = _make_renderer(qtbot, editor)
    spec = ViewLayoutSpec.leaf("view.a")
    container = renderer.render(spec, {"view.a": view_a})
    qtbot.addWidget(container)

    toolbars = container.findChildren(Toolbar)
    assert len(toolbars) == 1
    assert isinstance(toolbars[0].graphicsEffect(), QGraphicsOpacityEffect)
    assert toolbars[0].is_active() is False


def test_activating_view_emphasizes_its_toolbars(qtbot: QtBot) -> None:
    view_a = _FakeView("view.a")
    view_b = _FakeView("view.b")
    editor = _FakeEditor((view_a, view_b))
    renderer = _make_renderer(qtbot, editor)
    spec = ViewLayoutSpec.split(
        SplitDirection.HORIZONTAL,
        (ViewLayoutSpec.leaf("view.a"), ViewLayoutSpec.leaf("view.b")),
    )
    container = renderer.render(spec, {"view.a": view_a, "view.b": view_b})
    qtbot.addWidget(container)

    editor.set_active_view("view.a")

    for tb in renderer._toolbars_by_view["view.a"]:
        assert tb.is_active() is True
    for tb in renderer._toolbars_by_view["view.b"]:
        assert tb.is_active() is False


def test_always_toolbar_is_unaffected(qtbot: QtBot) -> None:
    class _AlwaysView(_FakeView):
        def toolbar_specs(self) -> list[ToolbarSpec]:
            return [
                ToolbarSpec(
                    toolbar_id=f"tb.{self.view_id}.always",
                    title="Always",
                    orientation=ToolbarOrientation.VERTICAL,
                    position=ToolbarPosition.LEFT,
                    tool_ids=("tool.log",),
                    visibility_mode=ToolbarVisibilityMode.ALWAYS,
                )
            ]

    view_a = _AlwaysView("view.a")
    editor = _FakeEditor((view_a,))
    renderer = _make_renderer(qtbot, editor)
    spec = ViewLayoutSpec.leaf("view.a")
    container = renderer.render(spec, {"view.a": view_a})
    qtbot.addWidget(container)

    editor.set_active_view("view.a")
    editor.set_active_view(None)

    for tb in renderer._toolbars_by_view["view.a"]:
        assert tb.is_active() is True


def test_clear_cache_removes_filters(qtbot: QtBot) -> None:
    view_a = _FakeView("view.a")
    editor = _FakeEditor((view_a,))
    renderer = _make_renderer(qtbot, editor)
    spec = ViewLayoutSpec.leaf("view.a")
    container = renderer.render(spec, {"view.a": view_a})
    qtbot.addWidget(container)

    assert len(renderer._view_filters) == 1
    renderer.clear_cache()
    assert len(renderer._view_filters) == 0
    assert len(renderer._view_filter_targets) == 0
    assert len(renderer._toolbars_by_view) == 0


def test_render_twice_does_not_duplicate_filters(qtbot: QtBot) -> None:
    view_a = _FakeView("view.a")
    editor = _FakeEditor((view_a,))
    renderer = _make_renderer(qtbot, editor)
    spec = ViewLayoutSpec.leaf("view.a")
    container = renderer.render(spec, {"view.a": view_a})
    qtbot.addWidget(container)
    renderer.render(spec, {"view.a": view_a})

    assert len(renderer._view_filters) == 1
    assert len(renderer._toolbars_by_view["view.a"]) == 1


def test_renderer_without_editor_has_no_filters(qtbot: QtBot) -> None:
    view_a = _FakeView("view.a")
    renderer = _make_renderer(qtbot, editor=None)
    spec = ViewLayoutSpec.leaf("view.a")
    container = renderer.render(spec, {"view.a": view_a})
    qtbot.addWidget(container)

    assert renderer._view_filters == {}
    assert renderer._view_filter_targets == {}
    assert len(renderer._toolbars_by_view["view.a"]) == 1


def test_filter_returns_false_for_activation_event() -> None:
    calls: list[str] = []
    f = _ViewActivationFilter("view.a", calls.append)

    class _Obj:
        pass

    result = f.eventFilter(_Obj(), QEvent(QEvent.Type.MouseButtonPress))
    assert result is False
    assert calls == ["view.a"]


def test_filter_ignores_other_events() -> None:
    calls: list[str] = []
    f = _ViewActivationFilter("view.a", calls.append)

    class _Obj:
        pass

    result = f.eventFilter(_Obj(), QEvent(QEvent.Type.Enter))
    assert result is False
    assert calls == []