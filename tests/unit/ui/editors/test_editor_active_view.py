"""Unit tests for Editor active View state (Bloco 3).

Covers the contract added in Bloco 3:
- ``active_view_id`` starts as ``None``.
- ``set_active_view`` updates the state and emits ``active_view_changed``.
- Repeating the same id is a no-op (no signal).
- An unknown view_id is rejected: no state change, no signal, WARNING logged.
- ``None`` clears the state and emits ``None``.
- ``dispose()`` resets ``active_view_id`` without emitting.
- An Editor with no Views rejects every ``set_active_view`` call.

The tests use a ``FakeView`` whose ``content_widget`` is a ``QLabel``
and a ``FakeEditor`` that returns a static tuple of Views.

Every test requires ``qapp`` because ``Editor.__init__`` instantiates a
``QObject`` (``_EditorSignals``). This mirrors the requirement already
imposed by ``MPRView`` (see ``_MPRSignals``).
"""

from __future__ import annotations

import logging

import pytest
from PySide6.QtWidgets import QLabel, QWidget
from pytestqt.qtbot import QtBot

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.editors.view import View


# ----- Fixtures ------------------------------------------------------


class FakeView(View):
    """Minimal View whose content_widget is a QLabel."""

    def __init__(self, view_id: str) -> None:
        super().__init__(view_id=view_id, view_type="fake")
        self._label: QLabel | None = None

    def content_widget(self) -> QWidget:
        if self._label is None:
            self._label = QLabel(self.view_id)
        return self._label


class FakeEditor(Editor):
    """Editor that hosts a fixed set of Views (or none)."""

    def __init__(self, view_ids: tuple[str, ...] = ()) -> None:
        super().__init__(editor_id="editor.fake", title="Fake")
        self._views: tuple[View, ...] = tuple(FakeView(vid) for vid in view_ids)

    def content_widget(self) -> QWidget:
        return QWidget()

    def views(self) -> tuple[View, ...]:
        return self._views


@pytest.fixture
def editor(qapp: QtBot) -> FakeEditor:
    """Editor with two Views: view.a and view.b."""
    return FakeEditor(view_ids=("view.a", "view.b"))


# ----- Initial state -------------------------------------------------


def test_active_view_id_starts_none(qapp: QtBot) -> None:
    editor = FakeEditor(view_ids=("view.a",))
    assert editor.active_view_id is None


def test_editor_with_no_views_starts_with_no_active_view(qapp: QtBot) -> None:
    editor = FakeEditor(view_ids=())
    assert editor.active_view_id is None
    assert editor.views() == ()


# ----- set_active_view: valid id -------------------------------------


def test_set_active_view_updates_state_and_emits(
    qtbot: QtBot,
    editor: FakeEditor,
) -> None:
    received: list[str | None] = []
    editor.active_view_changed.connect(received.append)

    editor.set_active_view("view.a")

    assert editor.active_view_id == "view.a"
    assert received == ["view.a"]


def test_set_active_view_switch_to_another_view(
    qtbot: QtBot,
    editor: FakeEditor,
) -> None:
    received: list[str | None] = []
    editor.active_view_changed.connect(received.append)

    editor.set_active_view("view.a")
    editor.set_active_view("view.b")

    assert editor.active_view_id == "view.b"
    assert received == ["view.a", "view.b"]


# ----- set_active_view: idempotency ----------------------------------


def test_set_active_view_same_id_is_noop(
    qtbot: QtBot,
    editor: FakeEditor,
) -> None:
    editor.set_active_view("view.a")

    received: list[str | None] = []
    editor.active_view_changed.connect(received.append)

    editor.set_active_view("view.a")

    assert editor.active_view_id == "view.a"
    assert received == []


# ----- set_active_view: unknown id ----------------------------------


def test_set_active_view_unknown_id_is_rejected_with_warning(
    qtbot: QtBot,
    editor: FakeEditor,
    caplog: pytest.LogCaptureFixture,
) -> None:
    received: list[str | None] = []
    editor.active_view_changed.connect(received.append)

    with caplog.at_level(
        logging.WARNING, logger="cranioz.ui.editors.base_editor"
    ):
        editor.set_active_view("view.unknown")

    assert editor.active_view_id is None
    assert received == []
    assert any(
        "view.unknown" in record.message and "editor.fake" in record.message
        for record in caplog.records
    )


def test_set_active_view_unknown_id_does_not_clear_existing(
    qtbot: QtBot,
    editor: FakeEditor,
) -> None:
    editor.set_active_view("view.a")

    received: list[str | None] = []
    editor.active_view_changed.connect(received.append)

    editor.set_active_view("view.unknown")

    assert editor.active_view_id == "view.a"
    assert received == []


# ----- set_active_view: None -----------------------------------------


def test_set_active_view_none_clears_and_emits_none(
    qtbot: QtBot,
    editor: FakeEditor,
) -> None:
    editor.set_active_view("view.a")

    received: list[str | None] = []
    editor.active_view_changed.connect(received.append)

    editor.set_active_view(None)

    assert editor.active_view_id is None
    assert received == [None]


def test_set_active_view_none_when_already_none_is_noop(
    qtbot: QtBot,
    editor: FakeEditor,
) -> None:
    received: list[str | None] = []
    editor.active_view_changed.connect(received.append)

    editor.set_active_view(None)

    assert editor.active_view_id is None
    assert received == []


# ----- dispose -------------------------------------------------------


def test_dispose_resets_active_view_without_emitting(
    qtbot: QtBot,
    editor: FakeEditor,
) -> None:
    editor.set_active_view("view.a")

    received: list[str | None] = []
    editor.active_view_changed.connect(received.append)

    editor.dispose()

    assert editor.active_view_id is None
    assert received == []


# ----- Editor with no Views ------------------------------------------


def test_set_active_view_on_editor_with_no_views_is_rejected(
    qtbot: QtBot,
    caplog: pytest.LogCaptureFixture,
) -> None:
    editor = FakeEditor(view_ids=())

    received: list[str | None] = []
    editor.active_view_changed.connect(received.append)

    with caplog.at_level(
        logging.WARNING, logger="cranioz.ui.editors.base_editor"
    ):
        editor.set_active_view("view.anything")

    assert editor.active_view_id is None
    assert received == []
    assert any("view.anything" in r.message for r in caplog.records)


# ----- Signal contract: object payload --------------------------------


def test_active_view_changed_is_signal_object(
    qtbot: QtBot,
    editor: FakeEditor,
) -> None:
    """Lock the ``Signal(object)`` decision: emitting ``None`` must work.

    If this ever changes to ``Signal(str)``, this test fails and the
    Bloco 4 consumers (which rely on ``None`` to mean "no View active")
    must be revisited.
    """
    received: list[object] = []
    editor.active_view_changed.connect(received.append)

    editor.set_active_view("view.a")
    editor.set_active_view(None)

    assert received == ["view.a", None]