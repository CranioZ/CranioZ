"""Visual debug tool for AreaLayoutRenderer (Sprint G).

Opens a small window that renders a single Area via
``AreaLayoutRenderer``. Two toggle buttons let you compare:

- **Editors: 1 / 2** — the single-Editor case (container, no
  QSplitter) vs the multi-Editor case (QSplitter with one container
  per Editor).
- **Toolbar position: LEFT / RIGHT / TOP / BOTTOM** — where the
  Editor's Toolbar is placed inside its container.

Each Editor is a ``DebugEditor`` (an ``Editor`` subclass with a
colored label and a configurable Toolbar), so the script can control
the Toolbar specification directly and show one Toolbar per Editor at
the chosen position.

This is a manual inspection tool. It is not a test. It does not
assert anything. It uses the same production widgets the real
application uses (``AreaLayoutRenderer``, ``Toolbar``, ``ThemeService``,
``UnicodeIconProvider``).

Run from the repository root:

    .venv\\Scripts\\python.exe scripts\\debug\\ui\\workspace\\debug_area_layout_renderer.py

Requirements: PySide6, a working display. No VTK needed.

Notes:

- The Editors are **recreated on every rebuild**, mirroring the real
  Workspace: ``LayoutBuilder`` creates fresh Editor instances per
  ``load_spec()``, and the old ones are disposed. Reusing the same
  Editor instance across rebuilds would return a ``content_widget()``
  whose parent container was already deleted by Qt, raising
  ``RuntimeError: Internal C++ object already deleted``.
- ``DebugEditor.dispose()`` invalidates the cached ``content_widget``
  (same pattern as ``TomographyEditor`` and ``MeshDebugEditor``).
  Without this, the cached ``QLabel`` becomes a dangling reference
  after the container is destroyed.
- The Toolbar uses two ``tool.log`` entries. ``tool.toggle`` declares
  ``icon = "toggle"``, which is not in the ``UnicodeIconProvider``
  catalog (66 names); using it would print
  ``unknown icon name 'toggle'`` on every rebuild. The debug tool
  only needs two buttons to show the Toolbar position, so it uses
  two ``tool.log`` entries. Fixing the catalog is out of scope
  (Sprint F follow-up).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running from the repository root without installing the package.
# The script lives in ``scripts/debug/ui/workspace/`` (3 levels below
# the repo root), so ``parents[3]`` is ``C:\CranioZ``.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QSurfaceFormat  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

# ----- Apply the same surface format as the real entry point --------
_fmt = QSurfaceFormat()
_fmt.setDepthBufferSize(24)
_fmt.setStencilBufferSize(8)
_fmt.setVersion(2, 1)
_fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
QSurfaceFormat.setDefaultFormat(_fmt)
QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)


# ----- Imports that need the QApplication to exist (theme, icons) ---
from cranioz.infrastructure.settings.in_memory_settings_service import (  # noqa: E402
    InMemorySettingsService,
)
from cranioz.ui.editors.base_editor import Editor  # noqa: E402
from cranioz.ui.icons.provider import IconProvider  # noqa: E402
from cranioz.ui.icons.unicode import UnicodeIconProvider  # noqa: E402
from cranioz.ui.theme.service import ThemeService  # noqa: E402
from cranioz.ui.toolbars.specification import (  # noqa: E402
    ToolbarOrientation,
    ToolbarPosition,
    ToolbarSpec,
)
from cranioz.ui.tools.builtin.log_tool import LogTool  # noqa: E402
from cranioz.ui.tools.registry.tool_registry import ToolRegistry  # noqa: E402
from cranioz.ui.workspace.areas.area import Area  # noqa: E402
from cranioz.ui.workspace.areas.area_layout_renderer import (  # noqa: E402
    AreaLayoutRenderer,
)
from cranioz.ui.workspace.areas.placement import Placement  # noqa: E402


# ----- Debug Editor --------------------------------------------------


class DebugEditor(Editor):
    """An Editor that shows a colored label and a configurable Toolbar.

    The content is a QLabel with the editor_id, so the script can show
    which container belongs to which Editor. The Toolbar is declared
    from the current position (the script sets it on each rebuild).
    """

    _COLORS = {
        "editor.debug.a": "#3B82F6",  # blue
        "editor.debug.b": "#F59E0B",  # amber
        "editor.debug.c": "#10B981",  # green
    }

    def __init__(
        self,
        editor_id: str = "editor.debug.a",
        title: str = "Debug Editor",
    ) -> None:
        super().__init__(editor_id=editor_id, title=title)
        self._label: QLabel | None = None
        self._position: ToolbarPosition = ToolbarPosition.LEFT
        self._orientation: ToolbarOrientation = ToolbarOrientation.VERTICAL

    def set_toolbar_position(
        self,
        position: ToolbarPosition,
        orientation: ToolbarOrientation,
    ) -> None:
        self._position = position
        self._orientation = orientation

    def content_widget(self) -> QWidget:
        if self._label is None:
            color = self._COLORS.get(self.editor_id, "#888888")
            self._label = QLabel(self.editor_id)
            self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._label.setStyleSheet(
                f"QLabel {{"
                f"  background-color: {color};"
                f"  color: white;"
                f"  font-size: 22px;"
                f"  font-weight: bold;"
                f"  padding: 24px;"
                f"}}"
            )
        return self._label

    def toolbar_specs(self) -> list[ToolbarSpec]:
        # Two ``tool.log`` entries: ``tool.toggle``'s icon name is not
        # in the UnicodeIconProvider catalog and would print a warning
        # on every rebuild. The debug tool only needs two buttons to
        # demonstrate the Toolbar position.
        return [
            ToolbarSpec(
                toolbar_id=f"toolbar.{self.editor_id}.debug",
                title=f"{self.title} Toolbar",
                orientation=self._orientation,
                position=self._position,
                tool_ids=("tool.log", "tool.log"),
            )
        ]

    def dispose(self) -> None:
        """Release the cached content widget.

        The Editor owns its content_widget() and must invalidate the
        cache on dispose(). Otherwise, after the parent container is
        deleted by Qt, content_widget() returns a dangling reference
        and the next render fails with
        ``RuntimeError: Internal C++ object already deleted``.

        ``TomographyEditor`` and ``MeshDebugEditor`` follow the same
        rule.
        """
        if self._label is not None:
            self._label.setParent(None)
            self._label.deleteLater()
            self._label = None


# ----- Main window ---------------------------------------------------


class DebugWindow(QMainWindow):
    """Window with two toggles and a host for the rendered Area."""

    def __init__(
        self,
        renderer: AreaLayoutRenderer,
    ) -> None:
        super().__init__()
        self._renderer = renderer
        self._area = Area(
            area_id="area.debug",
            title="Debug Area",
            placement=Placement.CENTRAL,
        )

        self._editors: list[DebugEditor] = []

        # ----- Controls ---------------------------------------------
        self._editor_count_combo = QComboBox()
        self._editor_count_combo.addItems(["1 Editor", "2 Editors"])
        self._editor_count_combo.currentIndexChanged.connect(self._rebuild)

        self._position_combo = QComboBox()
        for pos in (
            ToolbarPosition.LEFT,
            ToolbarPosition.RIGHT,
            ToolbarPosition.TOP,
            ToolbarPosition.BOTTOM,
        ):
            self._position_combo.addItem(pos.value.upper(), pos)
        self._position_combo.currentIndexChanged.connect(self._rebuild)

        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(8, 8, 8, 8)
        controls_layout.setSpacing(8)
        controls_layout.addWidget(QLabel("Editors:"))
        controls_layout.addWidget(self._editor_count_combo)
        controls_layout.addSpacing(16)
        controls_layout.addWidget(QLabel("Toolbar position:"))
        controls_layout.addWidget(self._position_combo)
        controls_layout.addStretch(1)

        # ----- Host -----------------------------------------------
        self._host = QWidget()
        self._host_layout = QVBoxLayout(self._host)
        self._host_layout.setContentsMargins(0, 0, 0, 0)
        self._host_layout.setSpacing(0)

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(controls, stretch=0)
        central_layout.addWidget(self._host, stretch=1)
        self.setCentralWidget(central)

        self.setWindowTitle("CranioZ — AreaLayoutRenderer debug")
        self.resize(900, 600)

        self._rebuild()

    # ----- Rebuild ------------------------------------------------

    def _rebuild(self) -> None:
        editor_count = int(self._editor_count_combo.currentText().split()[0])
        position: ToolbarPosition = self._position_combo.currentData()
        orientation = (
            ToolbarOrientation.VERTICAL
            if position in (ToolbarPosition.LEFT, ToolbarPosition.RIGHT)
            else ToolbarOrientation.HORIZONTAL
        )

        # Dispose the previous Editors and re-create them, exactly like
        # the real Workspace does on load_spec(): the LayoutBuilder
        # creates fresh Editor instances per build; the old ones are
        # disposed.
        for editor in self._editors:
            editor.dispose()
        self._editors = [
            DebugEditor(editor_id="editor.debug.a"),
            DebugEditor(editor_id="editor.debug.b"),
        ]
        for editor in self._editors:
            editor.set_toolbar_position(position, orientation)

        # Rebuild the Area with the fresh Editors.
        self._area = Area(
            area_id="area.debug",
            title="Debug Area",
            placement=Placement.CENTRAL,
        )
        for editor in self._editors[:editor_count]:
            self._area.add_editor(editor)

        # Clear the host. This destroys the previous containers (and,
        # transitively, the previous DebugEditors' QLabels), but the
        # Editors have already been disposed above, so their cache is
        # None and the next render will create fresh labels.
        while self._host_layout.count():
            item = self._host_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        # Render.
        content_widgets: dict[str, QWidget] = {}
        rendered = self._renderer.render(self._area, content_widgets)
        self._host_layout.addWidget(rendered)


# ----- Entry point ---------------------------------------------------


def main() -> int:
    app = QApplication.instance() or QApplication([])

    # Theme: apply the dark QSS so the Toolbars and labels look like
    # the real application.
    settings = InMemorySettingsService()
    theme_service = ThemeService(settings=settings)
    theme_service.compiler().apply(theme_service.compiled())
    icon_provider: IconProvider = UnicodeIconProvider(theme_service)

    # Tool registry: the ToolbarSpec references ``tool.log`` twice.
    tool_registry = ToolRegistry()
    tool_registry.register("tool.log", LogTool)

    renderer = AreaLayoutRenderer(
        tool_registry=tool_registry,
        theme_service=theme_service,
        icon_provider=icon_provider,
    )

    window = DebugWindow(renderer=renderer)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())