import pytest
from PySide6.QtWidgets import QLabel, QTabWidget

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.workspace.areas.editor_stack import (
    EditorStack,
    EditorStackOrientation,
)


class FakeEditor(Editor):
    def __init__(self, editor_id: str) -> None:
        super().__init__(editor_id, editor_id)
        self.content_calls = 0
        self.activate_calls = 0
        self.deactivate_calls = 0
        self.dispose_calls = 0

    def content_widget(self):
        self.content_calls += 1
        return QLabel(self.title)

    def activate(self):
        self.activate_calls += 1

    def deactivate(self):
        self.deactivate_calls += 1

    def dispose(self):
        self.dispose_calls += 1


@pytest.fixture
def editors():
    return (FakeEditor("editor.a"), FakeEditor("editor.b"), FakeEditor("editor.c"))


def test_editor_stack_is_not_a_qtabwidget(qtbot, editors):
    stack = EditorStack(editors, EditorStackOrientation.BOTTOM)
    qtbot.addWidget(stack)
    assert stack.findChildren(QTabWidget) == []


def test_lazy_materialization(qtbot, editors):
    a, b, c = editors
    stack = EditorStack(editors, EditorStackOrientation.BOTTOM, active_editor_id="editor.a")
    qtbot.addWidget(stack)

    # Only the active editor (a) was materialized.
    assert a.content_calls == 1
    assert b.content_calls == 0
    assert c.content_calls == 0

    # Switch to b -> materializes b.
    stack._set_active("editor.b")
    assert b.content_calls == 1
    assert a.content_calls == 1  # Does not re-materialize a.


def test_lifecycle(qtbot, editors):
    a, b, _ = editors
    stack = EditorStack(editors, EditorStackOrientation.BOTTOM, active_editor_id="editor.a")
    qtbot.addWidget(stack)

    # The active editor (a) should have been activated exactly once.
    assert a.activate_calls == 1
    assert b.activate_calls == 0
    # FIX: 'a' was the initial active editor, so it must NOT have been
    # deactivated during construction.
    assert a.deactivate_calls == 0

    stack._set_active("editor.b")

    # The previously active editor (a) should have been deactivated once.
    assert a.deactivate_calls == 1
    # The newly active editor (b) should have been activated once.
    assert b.activate_calls == 1


def test_active_editor_changed_signal(qtbot, editors):
    stack = EditorStack(editors, EditorStackOrientation.BOTTOM)
    qtbot.addWidget(stack)

    received = []
    stack.active_editor_changed.connect(received.append)
    stack._set_active("editor.b")
    assert received == ["editor.b"]
