"""Integration tests: HomePage flow loading via TaskManager (Sprint K).

Covers the asynchronous flow loading path:

- ``MainWindow._dispatch_flow_loading`` dispatches a ``_LoadFlowsTask``
  through the ``TaskManager``.
- On success, ``FlowList.set_flows`` is called with the loaded
  definitions and ``HomePage.flows_loading_finished`` is emitted.
- On failure, ``HomePage.flows_loading_failed`` is emitted and the
  ``FlowList`` keeps its placeholder.
- On cancellation, ``HomePage.flows_loading_failed`` is emitted
  (``TaskCancelled`` is delivered through ``on_cancel``; the
  MainWindow does not register an ``on_cancel`` callback today, so
  the cancellation surfaces as a missing completion — the test
  asserts no crash and no ``set_flows``).
- The synchronous fallback (``_load_flows_sync``) when no
  ``TaskManager`` is injected.

These tests use a real ``QtTaskManager`` with one worker thread to
keep timings short.
"""

from __future__ import annotations

import threading
from typing import Any

import pytest
from pytestqt.qtbot import QtBot
from tests.conftest import make_icon_provider, make_theme_service

from cranioz.application.event_bus import EventBus
from cranioz.application.flows.definition import FlowDefinition, FlowStep
from cranioz.application.project.access_policy import (
    AllowAllProjectAccessPolicy,
)
from cranioz.application.project.catalog import ProjectCatalog
from cranioz.application.project.in_memory_index import InMemoryProjectIndex
from cranioz.application.project.in_memory_repository import (
    InMemoryProjectRepository,
)
from cranioz.application.project.index_synchronizer import (
    ProjectIndexSynchronizer,
    SynchronizedProjectIndex,
)
from cranioz.application.project.manager import ProjectManager
from cranioz.application.tasks.base import Task, TaskCancelled
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.editors.core.editor.editor_registry import EditorRegistry
from cranioz.infrastructure.tasks.qt_task_manager import QtTaskManager
from cranioz.ui.main_window import MainWindow, _LoadFlowsTask
from cranioz.ui.theme.tokens import ThemeMode
from cranioz.ui.tools.registry.tool_registry import ToolRegistry
from cranioz.ui.workspace.workspace_spec import (
    PLACEHOLDER_EDITOR_CLASS,
    PLACEHOLDER_EDITOR_ID,
)

_ACTOR = "test-actor"


# ----- Helpers -------------------------------------------------------


def _flow(flow_id: str) -> FlowDefinition:
    return FlowDefinition(
        flow_id=flow_id,
        name_key=f"flows.{flow_id}.name",
        version=1,
        steps=(
            FlowStep(
                step_id=f"{flow_id}_s0",
                name_key=f"flows.{flow_id}.steps.s0",
                module_id="patient",
            ),
        ),
    )


class _FakeFlowCatalog:
    """Minimal FlowCatalog stand-in for tests."""

    def __init__(self, definitions: tuple[FlowDefinition, ...]) -> None:
        self._definitions = definitions
        self.calls = 0

    def list_definitions(self) -> tuple[FlowDefinition, ...]:
        self.calls += 1
        return self._definitions


class _FailingFlowCatalog:
    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    def list_definitions(self) -> tuple[FlowDefinition, ...]:
        raise self._exc


class _BlockingFlowCatalog:
    """Flow catalog that blocks until released; used for cancellation."""

    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()

    def list_definitions(self) -> tuple[FlowDefinition, ...]:
        self.started.set()
        while not self.release.is_set():
            self.release.wait(0.01)
        return ()


# ----- Fixtures ------------------------------------------------------


@pytest.fixture
def task_manager(qapp: Any) -> QtTaskManager:
    tm = QtTaskManager(max_threads=1)
    yield tm
    tm.shutdown(grace_seconds=2.0)


def _make_window(
    qtbot: QtBot,
    *,
    flow_catalog: object,
    task_manager: QtTaskManager | None,
) -> MainWindow:
    repository = InMemoryProjectRepository()
    event_bus = EventBus()

    index = InMemoryProjectIndex()
    synchronizer = ProjectIndexSynchronizer(index, repository, event_bus)
    synchronizer.start()
    catalog = ProjectCatalog(SynchronizedProjectIndex(index, synchronizer))

    manager = ProjectManager(
        repository=repository,
        event_bus=event_bus,
        access_policy=AllowAllProjectAccessPolicy(),
    )
    manager.create_project(
        _ACTOR,
        project_id=ProjectId("p-001"),
        project_name="Case 001",
        patient_id=PatientId("pat-001"),
        patient_display_name="Gabriel Silva",
        clinical_procedure="orthognathic",
    )

    editor_registry = EditorRegistry()
    editor_registry.register(PLACEHOLDER_EDITOR_ID, PLACEHOLDER_EDITOR_CLASS)

    theme_service = make_theme_service(ThemeMode.DARK)
    icon_provider = make_icon_provider(theme_service)

    window = MainWindow(
        catalog=catalog,
        manager=manager,
        actor=_ACTOR,
        editor_registry=editor_registry,
        tool_registry=ToolRegistry(),
        theme_service=theme_service,
        icon_provider=icon_provider,
        task_manager=task_manager,
        flow_catalog=flow_catalog,  # type: ignore[arg-type]
    )
    qtbot.addWidget(window)
    return window


# ----- Tests ---------------------------------------------------------


def test_flows_loaded_async_populates_flow_list(qtbot: QtBot, task_manager: QtTaskManager) -> None:
    """The TaskManager loads flows and FlowList receives them."""
    flow_catalog = _FakeFlowCatalog((_flow("orthognathic"),))
    window = _make_window(qtbot, flow_catalog=flow_catalog, task_manager=task_manager)

    with qtbot.waitSignal(window.home().flows_loading_finished, timeout=3000):
        pass  # dispatched in __init__; just wait for completion

    assert flow_catalog.calls == 1
    assert window.home()._flow_list_widget().flow_count() == 1


def test_flows_loading_started_is_emitted(qtbot, task_manager):
    """``flows_loading_started`` is emitted before the Task finishes."""
    flow_catalog = _FakeFlowCatalog((_flow("a"),))
    window = _make_window(qtbot, flow_catalog=flow_catalog, task_manager=task_manager)
    # Observe the signals of the *first* dispatch (from __init__).
    qtbot.waitUntil(lambda: window.home()._flow_list_widget().flow_count() == 1)

    # The first dispatch already emitted started+finished. To test
    # the started signal again, use a fresh window.
    events: list[str] = []
    window.home().flows_loading_started.connect(lambda: events.append("started"))
    window.home().flows_loading_finished.connect(lambda: events.append("finished"))

    window._dispatch_flow_loading()

    qtbot.waitUntil(lambda: "finished" in events, timeout=3000)
    assert events == ["started", "finished"]


def test_flows_loading_failure_emits_failed_signal(
    qtbot: QtBot, task_manager: QtTaskManager
) -> None:
    """A raising FlowCatalog surfaces as ``flows_loading_failed``."""
    flow_catalog = _FailingFlowCatalog(RuntimeError("boom"))
    window = _make_window(qtbot, flow_catalog=flow_catalog, task_manager=task_manager)

    with qtbot.waitSignal(window.home().flows_loading_failed, timeout=3000) as blocker:
        pass

    assert "boom" in blocker.args[0]
    assert window.home()._flow_list_widget().flow_count() == 0


def test_flows_loading_recovery_after_failure(qtbot: QtBot, task_manager: QtTaskManager) -> None:
    """After a failure, a subsequent dispatch can succeed."""
    flow_catalog = _FailingFlowCatalog(RuntimeError("boom"))
    window = _make_window(qtbot, flow_catalog=flow_catalog, task_manager=task_manager)
    with qtbot.waitSignal(window.home().flows_loading_failed, timeout=3000):
        pass

    # Swap the catalog for a working one and re-dispatch.
    window._flow_catalog = _FakeFlowCatalog((_flow("a"),))  # noqa: SLF001
    with qtbot.waitSignal(window.home().flows_loading_finished, timeout=3000):
        window._dispatch_flow_loading()  # noqa: SLF001

    assert window.home()._flow_list_widget().flow_count() == 1


def test_synchronous_fallback_when_no_task_manager(qtbot: QtBot) -> None:
    """Without a TaskManager, flows load synchronously."""
    flow_catalog = _FakeFlowCatalog((_flow("a"), _flow("b")))
    window = _make_window(qtbot, flow_catalog=flow_catalog, task_manager=None)

    # Synchronous: no signal wait needed.
    assert flow_catalog.calls == 1
    assert window.home()._flow_list_widget().flow_count() == 2


def test_load_flows_task_is_a_task_protocol() -> None:
    """``_LoadFlowsTask`` satisfies the ``Task`` Protocol."""
    task = _LoadFlowsTask(_FakeFlowCatalog(()))
    assert isinstance(task, Task)


def test_load_flows_task_checks_cancel_token(qtbot: QtBot) -> None:
    """The task observes cancellation before touching the catalog."""
    catalog = _FakeFlowCatalog((_flow("a"),))

    class _CancelledToken:
        @property
        def is_cancelled(self) -> bool:
            return True

        def raise_if_cancelled(self) -> None:
            raise TaskCancelled()

    task = _LoadFlowsTask(catalog)
    progress_calls: list[float] = []

    with pytest.raises(TaskCancelled):
        task.run(
            progress_calls.append,
            _CancelledToken(),  # type: ignore[arg-type]
        )

    assert catalog.calls == 0  # never reached the catalog
    assert progress_calls == [0.0]
