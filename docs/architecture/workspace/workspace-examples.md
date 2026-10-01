# Workspace — Code Examples

> **Status:** Draft
> **Related:** [workspace.md](../architecture/workspace.md),
> [workspace-implementation.md](workspace-implementation.md),
> [workspace-testing.md](workspace-testing.md)
> **Scope:** Reference implementation patterns for the Workspace subsystem

---

## 1. Purpose

This document provides **concrete code examples** for the Workspace
subsystem. It is not a specification — it is a reference for
contributors to understand the expected shape, style, and behavior of
the code.

**Note:** these are drafts. Final code lives in `src/cranioz/`. When in
doubt, the implementation plan
([workspace-implementation.md](workspace-implementation.md)) is the
authoritative source.

---

## 2. Style Conventions

All examples follow the project's conventions:

- **Python 3.12+ syntax** (`from __future__ import annotations`, PEP 604
  unions).
- **Strict typing** — every public method has type hints.
- **Google-style docstrings** — every public class and method documented.
- **Double quotes** for strings (ruff format).
- **Line length 100** (ruff).
- **English only** for identifiers and comments (Principle #1).

Example header:

```python
"""Module docstring describing the purpose of this file."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cranioz.domain.scene.scene import Scene
```

---

## 3. Example 1 — `Placement` enum

**File:** `src/cranioz/ui/workspace/placement.py`

```python
"""Placement values for Areas inside the Workspace."""

from __future__ import annotations

from enum import Enum


class Placement(Enum):
    """Construction metadata for Area placement.

    Used by the LayoutBuilder to build the split tree from a
    ModuleUISpec. Once the tree is built, Placement is no longer
    consulted — the tree is the single source of truth.
    """

    LEFT = "left"
    CENTRAL = "central"
    RIGHT = "right"
    BOTTOM = "bottom"

    def __str__(self) -> str:
        return self.value
```

**Notes:**

- Enum values are lowercase strings (serialization-friendly).
- `__str__` returns the value, useful for logs and debug.
- `FLOATING` is not included — it belongs to a future phase.

---

## 4. Example 2 — `Area`

**File:** `src/cranioz/ui/workspace/area.py`

```python
"""Generic UI container hosted by the Workspace."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from cranioz.ui.editors.editor_host import EditorHost


class Area(QWidget):
    """Generic UI container.

    An Area is a self-contained visual container. Every panel, viewport,
    toolbar, or floating window in the application is an Area.

    An Area **hosts an EditorHost**, which in turn hosts one or more
    Editors. The Area does not know what content its EditorHost
    contains.

    The Area does **not** store ``placement``. Placement is construction
    metadata of ``AreaSpec``.

    See ``docs/architecture/workspace.md`` for the conceptual model.
    """

    def __init__(
        self,
        id: str,
        title: str,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the Area.

        Args:
            id: Stable string identifier (e.g., ``area.left``).
            title: User-facing title (translatable).
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self._id = id
        self._title = title
        self._visible = True
        self._editor_host = EditorHost(self)

    @property
    def id(self) -> str:
        """Return the stable identifier of this Area."""
        return self._id

    @property
    def title(self) -> str:
        """Return the user-facing title of this Area."""
        return self._title

    @property
    def editor_host(self) -> EditorHost:
        """Return the EditorHost hosted by this Area."""
        return self._editor_host

    @property
    def visible(self) -> bool:
        """Return whether this Area is currently visible."""
        return self._visible

    def activate(self) -> None:
        """Activate the Area (make it visible and focused)."""
        self._visible = True
        self.show()

    def deactivate(self) -> None:
        """Deactivate the Area (hide it without unregistering)."""
        self._visible = False
        self.hide()

    def __repr__(self) -> str:
        return f"<Area id={self._id!r}>"
```

**Notes:**

- `Area` is **concrete**. Not abstract, no subclasses.
- `Area` hosts an `EditorHost` — it does not store `content` directly.
- `Area` does **not** expose `placement`.
- `activate` / `deactivate` control visibility, not lifecycle.

---

## 5. Example 3 — `AreaManager`

**File:** `src/cranioz/ui/workspace/area_manager.py`

```python
"""Registry of Areas known to the Workspace."""

from __future__ import annotations

from cranioz.ui.workspace.area import Area


class AreaManager:
    """Registry for Areas.

    Responsible for tracking all Areas known to the Workspace, providing
    lookup by ID, and enforcing uniqueness.
    """

    def __init__(self) -> None:
        """Initialize an empty AreaManager."""
        self._areas: dict[str, Area] = {}

    def register(self, area: Area) -> None:
        """Register an Area.

        Args:
            area: The Area to register.

        Raises:
            ValueError: If an Area with the same ID is already registered.
        """
        if area.id in self._areas:
            raise ValueError(f"Area '{area.id}' is already registered")
        self._areas[area.id] = area

    def unregister(self, area_id: str) -> None:
        """Unregister an Area by ID.

        This is a no-op if the Area is not registered.

        Args:
            area_id: The ID of the Area to unregister.
        """
        self._areas.pop(area_id, None)

    def get(self, area_id: str) -> Area | None:
        """Look up an Area by ID.

        Args:
            area_id: The ID of the Area to look up.

        Returns:
            The Area, or ``None`` if not registered.
        """
        return self._areas.get(area_id)

    def list_all(self) -> list[Area]:
        """Return all registered Areas, in registration order."""
        return list(self._areas.values())

    def __len__(self) -> int:
        return len(self._areas)

    def __contains__(self, area_id: str) -> bool:
        return area_id in self._areas
```

**Notes:**

- Pure Python — no Qt dependency. Easy to test.
- Uses dict for O(1) lookup.
- Preserves registration order (Python 3.7+ dict guarantee).

---

## 6. Example 4 — `AreaSpec` and `ModuleUISpec`

**File:** `src/cranioz/ui/workspace/area_spec.py`

```python
"""Construction metadata for Areas."""

from __future__ import annotations

from dataclasses import dataclass, field

from cranioz.ui.workspace.placement import Placement


@dataclass(frozen=True)
class AreaSpec:
    """Construction metadata for a single Area.

    Used by the LayoutBuilder to build the tree. The Module declares
    Areas via AreaSpec; the Workspace materializes them.

    Note: editor_ids are strings, not concrete Editor classes. The
    EditorRegistry resolves them.
    """

    area_id: str
    title: str
    placement: Placement
    editor_ids: list[str] = field(default_factory=list)
    active_editor_id: str | None = None
```

**File:** `src/cranioz/ui/workspace/module_ui_spec.py`

```python
"""Declaration of a Module's UI composition."""

from __future__ import annotations

from dataclasses import dataclass, field

from cranioz.ui.workspace.area_spec import AreaSpec


@dataclass(frozen=True)
class ModuleUISpec:
    """A Module's UI composition declaration.

    The Module does not own Areas nor Editors. It declares what it wants
    through this spec. The Workspace materializes the declaration.
    """

    areas: list[AreaSpec] = field(default_factory=list)
    overlays: list[object] = field(default_factory=list)  # OverlaySpec (future)
```

**Notes:**

- `AreaSpec` and `ModuleUISpec` are **data-only**.
- The Module **does not import** Editor classes.
- The `editor_ids` are resolved by the `EditorRegistry`.

---

## 7. Example 5 — `EditorHost`

**File:** `src/cranioz/ui/editors/editor_host.py`

```python
"""Host for one or more Editors inside an Area."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QStackedWidget,
    QTabBar,
    QVBoxLayout,
    QWidget,
)

from cranioz.ui.editors.base_editor import Editor


class EditorHost(QWidget):
    """Hosts one or more Editors inside an Area.

    Responsibilities:
    - Manage the list of Editors.
    - Track the active Editor (only one at a time).
    - Show tabs when there are 2 or more Editors.
    - Hide tabs when there is 0 or 1 Editor.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._editors: dict[str, Editor] = {}
        self._active_id: str | None = None

        self._tab_bar = QTabBar(self)
        self._stack = QStackedWidget(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._tab_bar)
        layout.addWidget(self._stack, stretch=1)

        self._tab_bar.currentChanged.connect(self._on_tab_changed)
        self._update_tab_visibility()

    @property
    def active_editor(self) -> Editor | None:
        if self._active_id is None:
            return None
        return self._editors.get(self._active_id)

    def add_editor(self, editor: Editor, *, activate: bool = True) -> None:
        """Add an Editor to the host."""
        if editor.id in self._editors:
            raise ValueError(f"Editor '{editor.id}' is already added")
        self._editors[editor.id] = editor
        self._stack.addWidget(editor)
        self._tab_bar.addTab(editor.title)
        if activate or self._active_id is None:
            self.set_active(editor.id)
        self._update_tab_visibility()

    def remove_editor(self, editor_id: str) -> None:
        """Remove an Editor from the host."""
        editor = self._editors.pop(editor_id, None)
        if editor is None:
            return
        self._stack.removeWidget(editor)
        editor.setParent(None)
        self._update_tab_visibility()

    def detach_editor(self, editor_id: str) -> Editor | None:
        """Detach an Editor without destroying it."""
        editor = self._editors.get(editor_id)
        if editor is None:
            return None
        self.remove_editor(editor_id)
        return editor

    def get_editor(self, editor_id: str) -> Editor | None:
        return self._editors.get(editor_id)

    def list_editors(self) -> list[Editor]:
        return list(self._editors.values())

    def set_active(self, editor_id: str) -> None:
        editor = self._editors.get(editor_id)
        if editor is None:
            raise KeyError(f"Editor '{editor_id}' not found")
        self._active_id = editor_id
        self._stack.setCurrentWidget(editor)

    def _on_tab_changed(self, index: int) -> None:
        if 0 <= index < self._tab_bar.count():
            editor_id = list(self._editors.keys())[index]
            self.set_active(editor_id)

    def _update_tab_visibility(self) -> None:
        self._tab_bar.setVisible(len(self._editors) >= 2)
```

**Notes:**

- Shows tabs only when there are **2 or more** Editors.
- One Editor is always active (or none, if empty).
- `detach_editor` returns the Editor without destroying it.

---

## 8. Example 6 — `EditorRegistry`

**File:** `src/cranioz/ui/editors/editor_registry.py`

```python
"""Registry of Editor classes, indexed by editor_id."""

from __future__ import annotations

from cranioz.ui.editors.base_editor import Editor


class EditorRegistry:
    """Resolves editor_id strings to concrete Editor classes.

    The Module declares editor_ids (strings). The Registry resolves
    them to concrete classes and creates instances.
    """

    def __init__(self) -> None:
        self._classes: dict[str, type[Editor]] = {}

    def register(self, editor_id: str, editor_type: type[Editor]) -> None:
        if editor_id in self._classes:
            raise ValueError(f"Editor id '{editor_id}' is already registered")
        self._classes[editor_id] = editor_type

    def resolve(self, editor_id: str) -> type[Editor]:
        if editor_id not in self._classes:
            raise KeyError(f"Editor id '{editor_id}' is not registered")
        return self._classes[editor_id]

    def create(self, editor_id: str) -> Editor:
        editor_type = self.resolve(editor_id)
        return editor_type()
```

**Notes:**

- Pure Python — no Qt dependency.
- Easy to test.
- Plugins can register editors at runtime.

---

## 9. Example 7 — `LayoutTree`

**File:** `src/cranioz/ui/workspace/layout_tree.py`

```python
"""N-ary split tree for the Workspace layout."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from abc import ABC

from cranioz.ui.workspace.area import Area
from cranioz.ui.workspace.area_spec import AreaSpec
from cranioz.ui.workspace.placement import Placement


class SplitDirection(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class SplitNode(ABC):
    """Base class for tree nodes."""


@dataclass
class Leaf(SplitNode):
    """A leaf node containing exactly one Area."""

    area: Area


@dataclass
class Split(SplitNode):
    """A split node with two or more children."""

    direction: SplitDirection
    children: list[SplitNode] = field(default_factory=list)


class LayoutTree:
    """N-ary split tree.

    The tree is the single source of truth for the layout.
    """

    def __init__(self, root: SplitNode) -> None:
        self._root = root

    @property
    def root(self) -> SplitNode:
        return self._root

    @classmethod
    def from_specs(
        cls,
        specs: list[AreaSpec],
        areas: dict[str, Area],
    ) -> "LayoutTree":
        """Build a tree from a list of AreaSpec.

        Rules:
        - CENTRAL is required.
        - LEFT, CENTRAL, RIGHT are grouped into a HORIZONTAL split.
        - BOTTOM is a separate VERTICAL split below the horizontal one.
        """
        by_placement: dict[Placement, list[AreaSpec]] = {
            p: [] for p in Placement
        }
        for spec in specs:
            by_placement[spec.placement].append(spec)

        if not by_placement[Placement.CENTRAL]:
            raise ValueError("Layout must declare at least one CENTRAL area")

        top_leaves: list[Leaf] = []
        for placement in (Placement.LEFT, Placement.CENTRAL, Placement.RIGHT):
            for spec in by_placement[placement]:
                top_leaves.append(Leaf(area=areas[spec.area_id]))

        if len(top_leaves) == 1:
            top_node: SplitNode = top_leaves[0]
        else:
            top_node = Split(SplitDirection.HORIZONTAL, top_leaves)

        if by_placement[Placement.BOTTOM]:
            bottom_leaves = [
                Leaf(area=areas[spec.area_id])
                for spec in by_placement[Placement.BOTTOM]
            ]
            bottom_node: SplitNode = (
                bottom_leaves[0]
                if len(bottom_leaves) == 1
                else Split(SplitDirection.HORIZONTAL, bottom_leaves)
            )
            return cls(
                root=Split(SplitDirection.VERTICAL, [top_node, bottom_node])
            )

        return cls(root=top_node)
```

**Notes:**

- `LayoutTree` is a **pure data model** — no Qt dependency.
- The tree is derived from `AreaSpec` metadata.
- Once built, the tree is the **single source of truth**.

---

## 10. Example 8 — Test for `Area`

**File:** `tests/unit/ui/test_area.py`

```python
"""Tests for Area."""

from __future__ import annotations

import pytest

from cranioz.ui.workspace.area import Area


@pytest.mark.qt
def test_area_has_id(qtbot):
    area = Area(id="area.test", title="Test")
    qtbot.addWidget(area)
    assert area.id == "area.test"


@pytest.mark.qt
def test_area_has_title(qtbot):
    area = Area(id="area.test", title="Test")
    qtbot.addWidget(area)
    assert area.title == "Test"


@pytest.mark.qt
def test_area_has_editor_host(qtbot):
    area = Area(id="area.test", title="Test")
    qtbot.addWidget(area)
    assert area.editor_host is not None


@pytest.mark.qt
def test_area_does_not_store_placement(qtbot):
    area = Area(id="area.test", title="Test")
    qtbot.addWidget(area)
    assert not hasattr(area, "placement")
```

**Notes:**

- Uses `qtbot.addWidget` to register the widget for cleanup.
- One assertion per test.
- Test names describe intent.

---

## 11. Example 9 — Acceptance test (Phase 1)

**File:** `tests/integration/ui/test_phase_1_acceptance.py`

```python
"""Acceptance test for Phase 1 of the Workspace implementation.

Phase 1 delivers the Base Model: Placement, Area, AreaManager,
AreaSpec.
"""

from __future__ import annotations

import pytest

from cranioz.ui.workspace.area import Area
from cranioz.ui.workspace.area_manager import AreaManager
from cranioz.ui.workspace.area_spec import AreaSpec
from cranioz.ui.workspace.placement import Placement


@pytest.mark.unit
def test_placement_has_expected_members():
    expected = {"LEFT", "CENTRAL", "RIGHT", "BOTTOM"}
    actual = {member.name for member in Placement}
    assert actual == expected


@pytest.mark.qt
def test_area_manager_registers_and_retrieves(qtbot):
    manager = AreaManager()
    area = Area(id="area.test", title="Test")
    qtbot.addWidget(area)
    manager.register(area)
    assert manager.get("area.test") is area


@pytest.mark.unit
def test_area_spec_has_editor_ids():
    spec = AreaSpec(
        area_id="area.central",
        title="Central",
        placement=Placement.CENTRAL,
        editor_ids=["editor.dummy"],
    )
    assert spec.editor_ids == ["editor.dummy"]
```

**Notes:**

- This is the **acceptance test** for Phase 1.
- It verifies the core types exist and behave as expected.

---

## 12. Running the Examples

Once the Base Model is implemented, you can run:

```bash
# Run the tests
pytest tests/unit/ui/ -v

# Run only Qt tests
pytest -m "qt" -v

# Run the application (once MainWindow + Workspace are wired)
python -m cranioz
```

Expected behavior after Phase 1:

- `Placement` enum exists with `LEFT`, `CENTRAL`, `RIGHT`, `BOTTOM`.
- `Area` can be created (with an internal `EditorHost`).
- `Area` does not expose `placement`.
- `AreaManager` registers and retrieves Areas.
- `AreaSpec` accepts `editor_ids` as strings.
- Tests pass.

---

## 13. Common Patterns

### 13.1 Creating an Area

```python
from cranioz.ui.workspace.area import Area

area = Area(id="area.central", title="Central")
```

### 13.2 Registering an Area

```python
from cranioz.ui.workspace.area_manager import AreaManager

manager = AreaManager()
manager.register(area)
```

### 13.3 Creating an AreaSpec

```python
from cranioz.ui.workspace.area_spec import AreaSpec
from cranioz.ui.workspace.placement import Placement

spec = AreaSpec(
    area_id="area.central",
    title="Central",
    placement=Placement.CENTRAL,
    editor_ids=["editor.viewport_3d"],
)
```

---

## 14. Anti-Patterns

Things **not** to do in the Workspace:

| Anti-pattern | Why it is bad |
|---|---|
| `Area` mutates the Scene directly | Violates Principle #5. |
| `Workspace` knows about clinical concepts | Violates §1.2 of workspace.md. |
| `Area` subclasses for "panel", "viewport", etc | Violates Principle #7. |
| Hardcoded layout positions | Layout must be data-driven. |
| Areas with global state | Makes testing and reuse hard. |
| `MainWindow` doing business logic | MainWindow is a shell. |
| Workspace knowing about Toolbars | Violates §1.3 of workspace.md. |
| Storing `placement` on `Area` | Placement is construction metadata of `AreaSpec`. |
| `AreaSpec.editor: Editor` | The Module must not instantiate Editors. Use `editor_ids`. |
