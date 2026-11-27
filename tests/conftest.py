"""Shared pytest fixtures for CranioZ tests."""

# Standard Library
import contextlib
import logging
import os
from collections.abc import Callable, Iterator
from typing import Any

# Third-Party Libraries
import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

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

try:
    import shiboken6
except ImportError:  # pragma: no cover
    shiboken6 = None

# =====================================================================
# Local Imports (cranioz.*)
# =====================================================================

# --- Application Layer (Commands, Events, Flows, and Projects) ---
from cranioz.application.commands.executor import CommandExecutor
from cranioz.application.commands.in_memory_bus import InMemoryCommandBus
from cranioz.application.commands.stack import InMemoryCommandStack
from cranioz.application.commands.transaction import (
    InMemoryTransactionManager,
)
from cranioz.application.event_bus import EventBus
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
from cranioz.application.scene.scene_provider import InMemorySceneProvider

# --- Domain Layer ---
from cranioz.domain.patient.value_objects.patient_id import PatientId
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.scene.domain_object_store import DomainObjectStore
from cranioz.editors.builtin.tomography.editor import TomographyEditor
from cranioz.editors.core.editor.editor_registry import EditorRegistry

# --- Infrastructure & Configuration (Settings, Workspace, Themes, etc.) ---
from cranioz.infrastructure.settings.in_memory_settings_service import (
    InMemorySettingsService,
)

# --- User Interface: Icons ---
from cranioz.ui.icons.provider import IconProvider
from cranioz.ui.icons.svg import SvgIconProvider, default_svg_icons_root
from cranioz.ui.icons.unicode import UnicodeIconProvider

# --- User Interface: Main Window ---
from cranioz.ui.main_window import MainWindow

# --- User Interface: Themes ---
from cranioz.ui.theme.service import ThemeService
from cranioz.ui.theme.tokens import ThemeMode

# --- User Interface: Tools & Toolbars ---
from cranioz.ui.toolbars.specification import (
    ToolbarOrientation,
    ToolbarSpec,
    ToolbarVisibilityMode,
)
from cranioz.ui.tools.builtin.log_tool import LogTool
from cranioz.ui.tools.builtin.toggle_tool import ToggleTool
from cranioz.ui.tools.registry.tool_registry import ToolRegistry

# --- User Interface: Workspace ---
from cranioz.ui.workspace.workspace_spec import (
    PLACEHOLDER_EDITOR_CLASS,
    PLACEHOLDER_EDITOR_ID,
)

# --- User Interface: Editors ---
from tests.fixtures.editors.test_editor import DummyEditor

_logger = logging.getLogger(__name__)


# =====================================================================
# Fake VTK renderer (used only by _patch_viewport_3d_view)
# =====================================================================


class _FakeViewPropsCollection:
    """Mimics the subset of ``vtkViewProps`` the tests touch.

    ``test_set_mesh_adds_actor`` calls ``GetNumberOfItems()`` and
    ``test_viewport_3d_set_volume_marks_has_volume`` may call
    ``GetLastItem()``. Nothing else is needed.
    """

    def __init__(self, props: list[object]) -> None:
        self._props = props

    def GetNumberOfItems(self) -> int:  # noqa: N802 - VTK naming
        return len(self._props)

    def GetLastItem(self) -> object | None:  # noqa: N802 - VTK naming
        return self._props[-1] if self._props else None


class _FakeRenderer:
    """Minimal stand-in for ``vtkRenderer`` used only in tests.

    The real ``Viewport3DView`` (``src/cranioz/ui/editors/viewport_3d/view.py``)
    calls this slice of the ``vtkRenderer`` API from methods that are
    **not** patched by ``_patch_viewport_3d_view``:

    * ``set_mesh``       → ``RemoveActor``, ``AddActor``
    * ``set_volume``     → ``AddVolume`` (and possibly ``AddActor``)
    * ``dispose``        → ``RemoveAllViewProps``
    * test ``test_set_mesh_adds_actor`` → ``GetViewProps``

    Any new method the production code starts using will surface as an
    ``AttributeError`` in a test; add it here (with a VTK-style name)
    to unblock the test.
    """

    def __init__(self) -> None:
        self._view_props: list[object] = []

    # ----- View prop management -------------------------------------

    def RemoveAllViewProps(self) -> None:  # noqa: N802 - VTK naming
        self._view_props.clear()

    def AddActor(self, actor: object) -> None:  # noqa: N802 - VTK naming
        self._view_props.append(actor)

    def RemoveActor(self, actor: object) -> None:  # noqa: N802 - VTK naming
        # VTK silently ignores unknown actors; mirror that.
        with contextlib.suppress(ValueError):
            self._view_props.remove(actor)

    def AddVolume(self, volume: object) -> None:  # noqa: N802 - VTK naming
        self._view_props.append(volume)

    def RemoveVolume(self, volume: object) -> None:  # noqa: N802 - VTK naming
        with contextlib.suppress(ValueError):
            self._view_props.remove(volume)

    def AddViewProp(self, prop: object) -> None:  # noqa: N802 - VTK naming
        self._view_props.append(prop)

    def GetViewProps(self) -> _FakeViewPropsCollection:  # noqa: N802
        return _FakeViewPropsCollection(self._view_props)

    # ----- Camera / lifecycle no-ops --------------------------------

    def ResetCamera(self) -> None:  # noqa: N802 - VTK naming
        pass

    def ResetCameraClippingRange(self) -> None:  # noqa: N802 - VTK naming
        pass


# =====================================================================
# VTK-free Viewport3DView (class-level patch)
# =====================================================================


@pytest.fixture(autouse=True)
def _patch_viewport_3d_view(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable VTK initialization for every test.

    The real ``Viewport3DView`` initializes VTK/OpenGL in its
    ``_ensure_pipeline`` method, which hangs in headless CI. This
    fixture patches ``_ensure_pipeline`` on the class so that every
    ``Viewport3DView`` instance created during the test skips VTK
    initialization.

    The fake methods mirror the contract of the real ones closely
    enough that tests asserting on ``has_mesh``, ``has_volume``,
    ``renderer``, ``volume_actor`` and ``preset`` observe consistent
    state:

    * ``_ensure_pipeline`` creates a ``_FakeRenderer`` (the real one
      creates a ``vtkRenderer``).
    * ``set_mesh`` populates ``_mesh`` and ``_mesh_actor`` and adds
      the actor to the fake renderer.
    * ``set_volume`` populates ``_volume``, ``_volume_set``,
      ``_volume_actor`` and ``_preset`` and adds the volume to the
      fake renderer.

    The ``_FakeRenderer`` exposes the slice of the ``vtkRenderer`` API
    that the real ``dispose``, ``set_mesh`` and ``set_volume`` call,
    so those methods can run unpatched against the fake.
    """
    # Imported here, not at module level: ``view.py`` imports VTK at
    # the top of the module. Importing it during conftest collection
    # would initialize VTK before QApplication, which on Windows
    # produces a wrong QSurfaceFormat and breaks the boot sequence.
    # The fixture runs after ``qapp`` thanks to pytest-qt's autouse
    # ordering.
    from cranioz.editors.views.viewport_3d.presets import get_preset  # noqa: PLC0415
    from cranioz.editors.views.viewport_3d.view import Viewport3DView  # noqa: PLC0415

    def _fake_ensure_pipeline(self) -> None:
        """Simulate the real _ensure_pipeline without VTK.

        The real implementation creates a ``vtkRenderer`` and stores it
        as ``self._renderer``. ``content_widget()`` calls this method
        eagerly (Block 4), so tests that do
        ``qtbot.addWidget(view.content_widget())`` then assert
        ``view.renderer is not None``. The fake must therefore create
        ``_renderer`` the first time it is called.

        A real ``vtkRenderer`` is replaced by ``_FakeRenderer``, which
        exposes the minimal API used by ``dispose``, ``set_mesh`` and
        ``set_volume``.
        """
        if getattr(self, "_renderer", None) is None:
            self._renderer = _FakeRenderer()

    def _fake_set_volume(self, volume: Any) -> None:
        """Simulate ``set_volume`` without VTK."""
        self._volume = volume
        self._volume_set = True
        if getattr(volume, "is_hu_calibrated", False):
            self._preset = get_preset("bone")
        else:
            self._preset = get_preset("cbct")
        if getattr(self, "_volume_actor", None) is None:
            self._volume_actor = object()
        # The real set_volume ensures the pipeline exists before adding
        # the actor; mirror that so ``view.renderer`` is not None.
        self._ensure_pipeline()
        self._renderer.AddVolume(self._volume_actor)

    def _fake_set_mesh(self, mesh: Any) -> None:
        """Mirror the real ``set_mesh`` contract without VTK.

        The real implementation (``view.py:224-250``) does three things
        the tests care about:

        1. Validates that ``mesh`` is not ``None`` — raises
           ``ValueError("Viewport3DView.set_mesh requires a non-None Mesh")``.
        2. Ensures the VTK pipeline exists (``_ensure_pipeline``), which
           creates ``self._renderer``.
        3. Removes the previous mesh actor, adds the new one, and stores
           ``_mesh_actor`` and ``_mesh``.

        The fake skips the actual ``vtkPolyData``/``vtkActor`` creation
        (no VTK) but mirrors steps 1-3 so that:

        - ``has_mesh`` reflects the same state as production.
        - ``view.renderer`` is not None after the call.
        - ``set_mesh(None)`` raises ``ValueError`` like production.
        """
        if mesh is None:
            raise ValueError("Viewport3DView.set_mesh requires a non-None Mesh")
        self._mesh = mesh
        if getattr(self, "_mesh_actor", None) is None:
            self._mesh_actor = object()
        # The real set_mesh ensures the pipeline exists before adding
        # the actor; mirror that so ``view.renderer`` is not None.
        self._ensure_pipeline()
        self._renderer.AddActor(self._mesh_actor)

    monkeypatch.setattr(Viewport3DView, "_ensure_pipeline", _fake_ensure_pipeline)
    monkeypatch.setattr(Viewport3DView, "set_volume", _fake_set_volume)
    monkeypatch.setattr(Viewport3DView, "set_mesh", _fake_set_mesh)

    # Replace the properties so that reads match what the fake writes,
    # regardless of how the original class implements them.
    monkeypatch.setattr(
        Viewport3DView,
        "volume_actor",
        property(lambda self: getattr(self, "_volume_actor", None)),
    )
    monkeypatch.setattr(
        Viewport3DView,
        "has_volume",
        property(lambda self: getattr(self, "_volume_set", False)),
    )
    monkeypatch.setattr(
        Viewport3DView,
        "preset",
        property(lambda self: getattr(self, "_preset", None)),
    )
    monkeypatch.setattr(
        Viewport3DView,
        "has_mesh",
        property(lambda self: getattr(self, "_mesh_actor", None) is not None),
    )
    monkeypatch.setattr(
        Viewport3DView,
        "renderer",
        property(lambda self: getattr(self, "_renderer", None)),
    )


# =====================================================================
# Factories
# =====================================================================


def make_theme_service(mode: ThemeMode = ThemeMode.DARK) -> ThemeService:
    return ThemeService(
        settings=InMemorySettingsService(),
        default_mode=mode,
    )


def make_icon_provider(
    theme_service: ThemeService | None = None,
) -> IconProvider:
    if theme_service is None:
        theme_service = make_theme_service(ThemeMode.DARK)
    return SvgIconProvider(
        theme_service=theme_service,
        icons_root=default_svg_icons_root(),
        fallback_provider=UnicodeIconProvider(theme_service=theme_service),
    )


# =====================================================================
# Qt main_window
# =====================================================================


@pytest.fixture(scope="session")
def qapp() -> QApplication:
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
def _finalize_vtk_interactors() -> Iterator[None]:
    yield
    if not _HAS_VTK:
        return
    if shiboken6 is None:
        return

    for widget in QApplication.allWidgets():
        if not isinstance(widget, QVTKRenderWindowInteractor):
            continue
        if not shiboken6.isValid(widget):
            continue
        try:
            widget.Finalize()
        except RuntimeError:
            _logger.debug("VTK Finalize failed for %r", widget, exc_info=True)


# ----- Theme ---------------------------------------------------------


@pytest.fixture
def theme_service() -> ThemeService:
    return make_theme_service(ThemeMode.DARK)


# ----- Icons ---------------------------------------------------------


@pytest.fixture
def icon_provider(theme_service: ThemeService) -> IconProvider:
    return make_icon_provider(theme_service)


# ----- Tools and Registry --------------------------------------------


@pytest.fixture
def tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register("tool.log", LogTool)
    registry.register("tool.toggle", ToggleTool)
    return registry


@pytest.fixture
def make_test_editor() -> Callable[..., DummyEditor]:
    def _factory(
        editor_id: str = "editor.test",
        title: str = "Test Editor",
    ) -> DummyEditor:
        return DummyEditor(editor_id=editor_id, title=title)

    return _factory


# ----- Toolbar spec factory ------------------------------------------


@pytest.fixture
def make_toolbar_spec() -> Callable[..., ToolbarSpec]:
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


# ----- MainWindow with an open project ------------------------------


def _close_main_window(window: MainWindow) -> None:
    """Close the active project on ``window`` using the public API.

    Prefers ``MainWindow.close_current_project()`` when it exists; falls
    back to the legacy private ``_on_home_clicked`` so this fixture
    keeps working during the transition period without test churn.

    If neither method exists, logs a warning instead of raising: a
    leaked workspace is a nuisance for the next test, not a reason to
    fail this one during teardown.
    """
    if window.current_workspace() is None:
        return

    close = getattr(window, "close_current_project", None)
    if callable(close):
        close()
        return

    legacy = getattr(window, "_on_home_clicked", None)  # noqa: SLF001
    if callable(legacy):
        legacy()
        return

    _logger.warning(
        "MainWindow exposes neither close_current_project() nor "
        "_on_home_clicked(); workspace may leak between tests"
    )


@pytest.fixture
def main_window_with_open_project(qtbot: QtBot) -> Iterator[MainWindow]:
    """Build a MainWindow with an open project.

    The command bus is intentionally left without registered handlers:
    UI tests that use this fixture only assert layout, toggle and
    lifecycle behaviour. If a test needs command dispatch, register the
    handlers explicitly in that test.
    """
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
    project_id = ProjectId("p-001")
    manager.create_project(
        "test-actor",
        project_id=project_id,
        project_name="Case 001",
        patient_id=PatientId("pat-001"),
        patient_display_name="João Silva",
        clinical_procedure="orthognathic",
    )

    scene_provider = InMemorySceneProvider()
    domain_object_store = DomainObjectStore()

    editor_registry = EditorRegistry()
    editor_registry.register(PLACEHOLDER_EDITOR_ID, PLACEHOLDER_EDITOR_CLASS)
    editor_registry.register("editor.tomography", TomographyEditor)

    tool_registry = ToolRegistry()
    tool_registry.register("tool.log", LogTool)
    tool_registry.register("tool.toggle", ToggleTool)

    command_bus = InMemoryCommandBus()
    command_dispatcher = CommandExecutor(
        command_bus=command_bus,
        command_stack=InMemoryCommandStack(),
        event_bus=event_bus,
        transaction_manager=InMemoryTransactionManager(),
    )

    theme_service = make_theme_service(ThemeMode.DARK)
    icon_provider = make_icon_provider(theme_service)

    window = MainWindow(
        catalog=catalog,
        manager=manager,
        actor="test-actor",
        editor_registry=editor_registry,
        tool_registry=tool_registry,
        theme_service=theme_service,
        icon_provider=icon_provider,
        command_dispatcher=command_dispatcher,
        command_bus=command_bus,
        scene_provider=scene_provider,
        domain_object_store=domain_object_store,
    )
    qtbot.addWidget(window)

    # Block 5.5: give the MainWindow (and therefore the Workspace
    # inside it) a real geometry before opening the project. Without
    # this, workspace.width() is 0 and _apply_default_splitter_sizes
    # bails out via the ``total_w < min_central`` guard, leaving the
    # AreaWidgets at width 0 (the toggle tests then fail).
    window.resize(1000, 650)
    window.show()
    qtbot.wait(50)

    window.home().refresh()
    window.home().project_open_requested.emit(project_id, "orthognathic")
    # The Workspace's layout update is debounced (50 ms). Wait long
    # enough for the timer to fire and the splitter sizes to be
    # applied before the test inspects the geometry.
    qtbot.wait(100)

    yield window

    _close_main_window(window)
