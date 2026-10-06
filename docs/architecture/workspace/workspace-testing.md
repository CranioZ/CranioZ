# Workspace — Testing Strategy

> **Status:** Draft
> **Related:** [workspace.md](../architecture/workspace.md),
> [workspace-implementation.md](implementation/workspace-implementation.md)
> **Scope:** How the Workspace subsystem is tested

---

## 1. Purpose

This document defines **how** the Workspace is tested: which tools, which
categories of tests, which fixtures, and which quality thresholds.

It is meant to be practical: any contributor should be able to read this
and write a valid test for the Workspace.

---

## 2. Testing Principles

Tests follow the project's engineering principles:

| Principle | How it applies to testing |
|---|---|
| #11 — Determinism | Tests are deterministic; no flaky tests allowed. |
| #12 — Performance is clinical | Layout performance is measured, not assumed. |
| #13 — Documentation is code | Test names document intent. |
| #15 — Errors are information | Tests assert on error messages, not just exceptions. |

Additionally:

- **Test behavior, not implementation.** Tests should survive refactoring.
- **One concept per test.** A test with "and" in its name is two tests.
- **Fail fast.** A failing test should point to the exact broken behavior.
- **No QApplication state leaks.** Each test cleans up after itself.

---

## 3. Tools

| Tool | Purpose |
|---|---|
| **pytest** | Test runner and assertion framework |
| **pytest-qt** | Qt widget testing, `QApplication` lifecycle, signals |
| **pytest-cov** | Coverage measurement |
| **pytest-benchmark** | Performance benchmarks |
| **hypothesis** | Property-based testing for layout invariants |
| **mypy** | Static type checking (runs in CI, not in tests) |

All tools are already installed via `cranioz[test]`.

---

## 4. Test Categories

The Workspace tests are organized in four categories:

| Category | Purpose | Speed | Qt required? |
|---|---|---|---|
| **Unit** | Test a single class in isolation | Fast (<10ms) | Usually no |
| **Widget** | Test a widget's behavior | Fast (~50ms) | Yes |
| **Integration** | Test multiple components together | Medium (~200ms) | Yes |
| **Visual** | Compare rendered output | Slow (>1s) | Yes |

Markers:

```python
@pytest.mark.unit
@pytest.mark.qt
@pytest.mark.integration
@pytest.mark.visual
@pytest.mark.slow
```

Run subsets:

```bash
pytest -m "unit"                  # only unit tests
pytest -m "not slow"              # everything except slow tests
pytest -m "qt and not visual"     # only widget tests
```

---

## 5. Folder Structure

Test files mirror the source layout:

```text
tests/
├── conftest.py
├── unit/
│   └── ui/
│       ├── test_placement.py
│       ├── test_area.py
│       ├── test_area_manager.py
│       ├── test_editor_host.py
│       ├── test_editor_registry.py
│       ├── test_layout_tree.py
│       ├── test_region.py
│       └── test_overlay.py
├── integration/
│   └── ui/
│       ├── test_workspace.py
│       ├── test_main_window.py
│       ├── test_layout_builder.py
│       ├── test_layout_renderer.py
│       └── test_layout_io.py
└── data/
    └── fixtures/
        └── layout_samples/
            ├── single_central.json
            ├── left_central_right.json
            ├── four_areas.json
            ├── empty.json
            └── unknown_areas.json
```

**Rule:** a test file's name mirrors the source file it tests.

| Source | Test |
|---|---|
| `ui/workspace/placement.py` | `tests/unit/ui/test_placement.py` |
| `ui/workspace/area.py` | `tests/unit/ui/test_area.py` |
| `ui/workspace/area_manager.py` | `tests/unit/ui/test_area_manager.py` |
| `ui/editors/editor_host.py` | `tests/unit/ui/test_editor_host.py` |
| `ui/editors/editor_registry.py` | `tests/unit/ui/test_editor_registry.py` |
| `ui/workspace/layout_tree.py` | `tests/unit/ui/test_layout_tree.py` |
| `ui/workspace/region.py` | `tests/unit/ui/test_region.py` |
| `ui/workspace/overlay.py` | `tests/unit/ui/test_overlay.py` |
| `ui/workspace/workspace.py` | `tests/integration/ui/test_workspace.py` |
| `ui/workspace/layout_builder.py` | `tests/integration/ui/test_layout_builder.py` |
| `ui/workspace/layout_renderer.py` | `tests/integration/ui/test_layout_renderer.py` |
| `ui/main_window.py` | `tests/integration/ui/test_main_window.py` |

---

## 6. Fixtures

### 6.1 Global fixtures (`tests/conftest.py`)

```python
import pytest
from PySide6.QtWidgets import QApplication, QLabel

from cranioz.ui.editors.base_editor import Editor
from cranioz.ui.workspace.area import Area
from cranioz.ui.workspace.area_manager import AreaManager
from cranioz.ui.workspace.workspace import Workspace


@pytest.fixture(scope="session")
def qapp():
    """Session-wide QApplication (required by Qt)."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def workspace(qapp):
    """Fresh Workspace instance."""
    ws = Workspace()
    yield ws
    ws.deleteLater()


@pytest.fixture
def area_manager():
    """Fresh AreaManager instance."""
    return AreaManager()


class DummyEditor(Editor):
    """Minimal concrete Editor for tests."""

    def __init__(self, editor_id: str = "editor.dummy", title: str = "Dummy"):
        super().__init__(editor_id=editor_id, title=title)
        self.set_widget(QLabel(f"[{title}]"))


@pytest.fixture
def make_editor():
    """Factory to create minimal Editors for tests."""
    def _factory(editor_id: str = "editor.dummy") -> Editor:
        return DummyEditor(editor_id=editor_id, title=editor_id)
    return _factory


@pytest.fixture
def make_area(qapp, make_editor):
    """Factory to create minimal Areas for tests."""
    def _factory(area_id: str, title: str | None = None) -> Area:
        area = Area(id=area_id, title=title or area_id)
        area.editor_host.add_editor(make_editor())
        return area
    return _factory
```

### 6.2 Fixture rules

- **`qapp` is session-scoped.** Creating multiple `QApplication` instances
  breaks Qt. Always use the same one.
- **Widget fixtures are function-scoped.** Each test gets a fresh widget.
- **Always clean up.** Use `deleteLater()` on Qt widgets to avoid leaking.
- **No global state.** Fixtures must not depend on module-level variables.

---

## 7. Example Tests

### 7.1 Unit test — `Placement`

```python
# tests/unit/ui/test_placement.py
import pytest

from cranioz.ui.workspace.placement import Placement


@pytest.mark.unit
def test_placement_enum_has_expected_members():
    expected = {"LEFT", "CENTRAL", "RIGHT", "BOTTOM"}
    actual = {member.name for member in Placement}
    assert actual == expected


@pytest.mark.unit
def test_placement_enum_values_are_lowercase_strings():
    for member in Placement:
        assert member.value == member.name.lower()
```

### 7.2 Unit test — `AreaManager`

```python
# tests/unit/ui/test_area_manager.py
import pytest


@pytest.mark.unit
def test_register_adds_area(area_manager, make_area):
    area = make_area("test")
    area_manager.register(area)
    assert area_manager.get("test") is area


@pytest.mark.unit
def test_duplicate_id_raises(area_manager, make_area):
    area_manager.register(make_area("dup"))
    with pytest.raises(ValueError, match="already registered"):
        area_manager.register(make_area("dup"))


@pytest.mark.unit
def test_unregister_removes_area(area_manager, make_area):
    area_manager.register(make_area("test"))
    area_manager.unregister("test")
    assert area_manager.get("test") is None


@pytest.mark.unit
def test_unregister_unknown_id_is_noop(area_manager):
    area_manager.unregister("does-not-exist")
    assert area_manager.get("does-not-exist") is None
```

### 7.3 Widget test — `Area`

```python
# tests/unit/ui/test_area.py
import pytest

from cranioz.ui.workspace.area import Area


@pytest.mark.qt
def test_area_has_id_and_title(qtbot):
    area = Area(id="area.test", title="Test")
    qtbot.addWidget(area)
    assert area.id == "area.test"
    assert area.title == "Test"


@pytest.mark.qt
def test_area_has_editor_host(qtbot):
    area = Area(id="area.test", title="Test")
    qtbot.addWidget(area)
    assert area.editor_host is not None


@pytest.mark.qt
def test_area_does_not_store_placement(qtbot):
    """Area must not expose `placement` — it is construction metadata."""
    area = Area(id="area.test", title="Test")
    qtbot.addWidget(area)
    assert not hasattr(area, "placement")
```

### 7.4 Unit test — `EditorHost`

```python
# tests/unit/ui/test_editor_host.py
import pytest

from cranioz.ui.editors.editor_host import EditorHost


@pytest.mark.qt
def test_add_editor(qtbot, make_editor):
    host = EditorHost()
    qtbot.addWidget(host)
    editor = make_editor("editor.a")
    host.add_editor(editor)
    assert editor in host.list_editors()


@pytest.mark.qt
def test_remove_editor(qtbot, make_editor):
    host = EditorHost()
    qtbot.addWidget(host)
    editor = make_editor("editor.a")
    host.add_editor(editor)
    host.remove_editor(editor.id)
    assert host.get_editor(editor.id) is None


@pytest.mark.qt
def test_set_active_editor(qtbot, make_editor):
    host = EditorHost()
    qtbot.addWidget(host)
    a = make_editor("editor.a")
    b = make_editor("editor.b")
    host.add_editor(a)
    host.add_editor(b)
    host.set_active(a.id)
    assert host.active_editor is a


@pytest.mark.qt
def test_detach_does_not_destroy_editor(qtbot, make_editor):
    host = EditorHost()
    qtbot.addWidget(host)
    editor = make_editor("editor.a")
    host.add_editor(editor)
    detached = host.detach_editor(editor.id)
    assert detached is editor
```

### 7.5 Unit test — `EditorRegistry`

```python
# tests/unit/ui/test_editor_registry.py
import pytest

from cranioz.ui.editors.editor_registry import EditorRegistry


@pytest.mark.unit
def test_register_and_resolve():
    registry = EditorRegistry()
    registry.register("editor.dummy", DummyEditor)
    assert registry.resolve("editor.dummy") is DummyEditor


@pytest.mark.unit
def test_resolve_unknown_raises():
    registry = EditorRegistry()
    with pytest.raises(KeyError, match="editor.unknown"):
        registry.resolve("editor.unknown")


@pytest.mark.unit
def test_create_returns_instance(qtbot):
    registry = EditorRegistry()
    registry.register("editor.dummy", DummyEditor)
    editor = registry.create("editor.dummy")
    qtbot.addWidget(editor)
    assert isinstance(editor, DummyEditor)
```

### 7.6 Unit test — `LayoutTree.from_specs`

```python
# tests/unit/ui/test_layout_tree.py
import pytest

from cranioz.ui.workspace.layout_tree import Leaf, Split, SplitDirection
from cranioz.ui.workspace.layout_tree import LayoutTree
from cranioz.ui.workspace.placement import Placement


@pytest.mark.unit
def test_from_specs_single_central(make_area):
    specs = [_spec("area.central", Placement.CENTRAL)]
    areas = {"area.central": make_area("area.central")}
    tree = LayoutTree.from_specs(specs, areas)

    assert isinstance(tree.root, Leaf)
    assert tree.root.area.id == "area.central"


@pytest.mark.unit
def test_from_specs_left_central_right(make_area):
    specs = [
        _spec("area.left", Placement.LEFT),
        _spec("area.central", Placement.CENTRAL),
        _spec("area.right", Placement.RIGHT),
    ]
    areas = {s.area_id: make_area(s.area_id) for s in specs}
    tree = LayoutTree.from_specs(specs, areas)

    assert isinstance(tree.root, Split)
    assert tree.root.direction == SplitDirection.HORIZONTAL
    assert len(tree.root.children) == 3


@pytest.mark.unit
def test_from_specs_with_bottom(make_area):
    specs = [
        _spec("area.central", Placement.CENTRAL),
        _spec("area.bottom", Placement.BOTTOM),
    ]
    areas = {s.area_id: make_area(s.area_id) for s in specs}
    tree = LayoutTree.from_specs(specs, areas)

    assert isinstance(tree.root, Split)
    assert tree.root.direction == SplitDirection.VERTICAL


@pytest.mark.unit
def test_from_specs_requires_central(make_area):
    specs = [_spec("area.left", Placement.LEFT)]
    areas = {"area.left": make_area("area.left")}
    with pytest.raises(ValueError, match="CENTRAL"):
        LayoutTree.from_specs(specs, areas)


def _spec(area_id, placement):
    """Helper to build a minimal AreaSpec for tests."""
    from cranioz.ui.workspace.area_spec import AreaSpec
    return AreaSpec(
        area_id=area_id,
        title=area_id,
        placement=placement,
        editor_ids=["editor.dummy"],
    )
```

### 7.7 Integration test — `Workspace` with `ModuleUISpec`

```python
# tests/integration/ui/test_workspace.py
import pytest

from cranioz.ui.workspace.area_spec import AreaSpec
from cranioz.ui.workspace.module_ui_spec import ModuleUISpec
from cranioz.ui.workspace.placement import Placement
from cranioz.ui.workspace.workspace import Workspace


@pytest.mark.qt
@pytest.mark.integration
def test_workspace_loads_spec_single_central(qtbot):
    ws = Workspace()
    qtbot.addWidget(ws)
    spec = ModuleUISpec(
        areas=[AreaSpec("area.central", "Central", Placement.CENTRAL, ["editor.dummy"])],
    )
    ws.load_spec(spec)
    assert "area.central" in [a.id for a in ws.list_areas()]


@pytest.mark.integration
def test_workspace_loads_spec_left_central_right(qtbot):
    ws = Workspace()
    qtbot.addWidget(ws)
    spec = ModuleUISpec(
        areas=[
            AreaSpec("area.left", "Left", Placement.LEFT, ["editor.dummy"]),
            AreaSpec("area.central", "Central", Placement.CENTRAL, ["editor.dummy"]),
            AreaSpec("area.right", "Right", Placement.RIGHT, ["editor.dummy"]),
        ],
    )
    ws.load_spec(spec)
    assert {a.id for a in ws.list_areas()} == {
        "area.left", "area.central", "area.right"
    }
```

### 7.8 Benchmark — layout performance

```python
# tests/integration/ui/test_layout_benchmark.py
import pytest


@pytest.mark.qt
@pytest.mark.benchmark
def test_load_spec_with_20_areas(benchmark, qtbot, make_area):
    from cranioz.ui.workspace.workspace import Workspace

    ws = Workspace()
    qtbot.addWidget(ws)

    areas = [make_area(f"area.{i}") for i in range(20)]

    def add_all():
        for area in areas:
            ws._area_manager.register(area)

    benchmark(add_all)
    # Acceptance: adding 20 areas takes < 100ms on a modern laptop
    assert benchmark.stats["mean"] < 0.1
```

---

## 8. Testing Anti-Patterns

Things **not** to do:

| Anti-pattern | Why it is bad |
|---|---|
| `time.sleep()` in tests | Flaky; use `qtbot.waitSignal` or `qtbot.wait`. |
| Multiple `QApplication` instances | Breaks Qt; use the session-scoped `qapp`. |
| Asserting on `repr()` of widgets | Fragile; assert on properties or state. |
| Testing private methods (`_foo`) | Couples tests to implementation. |
| Catching all exceptions | Hides real failures. |
| Sharing state between tests | Order-dependent test suites are useless. |
| Long-running tests without `@pytest.mark.slow` | Slows the whole suite. |
| Skipping tests without a reason | `@pytest.mark.skip(reason="...")` always. |

---

## 9. Testing the Workspace — Specific Cases

### 9.1 Area registration

| Scenario | Expected |
|---|---|
| Register a new Area | Added to `AreaManager`. |
| Register duplicate ID | `ValueError` with clear message. |
| Unregister non-existent ID | No error, no-op. |
| List areas when none registered | Empty list. |

### 9.2 Spec loading

| Scenario | Expected |
|---|---|
| `ModuleUISpec` with `[central]` | `Leaf(central)` built. |
| `ModuleUISpec` with `[left, central, right]` | `Split(HORIZONTAL, 3 children)`. |
| `ModuleUISpec` with `[left, central, right, bottom]` | `Split(VERTICAL)` with horizontal sub-split. |
| `ModuleUISpec` without `CENTRAL` | `ValueError` with clear message. |

### 9.3 Visibility

| Scenario | Expected |
|---|---|
| Hide a visible Area | Area not visible, still registered. |
| Show a hidden Area | Area visible again. |
| Hide all Areas | Workspace empty but stable. |
| Hide then remove an Area | No error. |

### 9.4 Persistence

| Scenario | Expected |
|---|---|
| Save and load empty layout | Round-trip stable. |
| Save and load 4-areas layout | Round-trip stable. |
| Load layout with unknown Area ID | Warning, area skipped. |
| Load layout with missing Area | Default placement applied. |
| Load malformed JSON | `ValueError` with clear message. |

### 9.5 Lifecycle

| Scenario | Expected |
|---|---|
| Create Workspace, load spec, destroy | No leaks (use `gc` + `weakref`). |
| Close MainWindow with open Areas | All Areas cleaned up. |
| Reopen project | Areas re-created from layout. |

### 9.6 Module switch

| Scenario | Expected |
|---|---|
| Switch to a Module with same `area_id` and same `editor_ids` | Area is **reused**. |
| Switch to a Module with same `area_id` but different `editor_ids` | Area is **reconfigured**. |
| Switch to a Module without a given `area_id` | Area is **destroyed**. |
| Switch to a Module with a new `area_id` | Area is **created**. |

### 9.7 Overlays

| Scenario | Expected |
|---|---|
| Register an Overlay | Overlay is added to `OverlayManager`. |
| Change layout (visibility toggle) | Overlay is **repositioned**. |
| Remove an Overlay | Overlay is unregistered. |

---

## 10. CI Integration

The CI runs tests in a matrix:

```yaml
# .github/workflows/ci.yml (excerpt)
strategy:
  matrix:
    python-version: ["3.12", "3.13"]
    os: [ubuntu-latest, windows-latest, macos-latest]

steps:
  - uses: actions/checkout@v4
  - uses: astral-sh/setup-uv@v3
  - run: uv sync --all-extras
  - run: uv run pytest -m "not slow" --cov=src/cranioz --cov-report=xml
  - run: uv run pytest -m "slow" --benchmark-only
```

**Headless Qt:** set `QT_QPA_PLATFORM=offscreen` in CI.

```yaml
env:
  QT_QPA_PLATFORM: offscreen
```

---

## 11. Coverage Targets

| Scope | Target | Notes |
|---|---|---|
| `ui/workspace/` | **≥ 80%** | Per the project's validation criteria. |
| `ui/editors/` | ≥ 70% | EditorHost, EditorRegistry, base Editor. |
| Overall `ui/` | ≥ 60% | Increasing as features are added. |

Coverage is enforced via `--cov-fail-under` in CI for the workspace scope.

---

## 12. Performance Benchmarks

The Workspace has performance criteria derived from the PDF:

| Metric | Target | Test |
|---|---|---|
| Load `ModuleUISpec` with 20 Areas | < 100 ms | `test_load_spec_with_20_areas` |
| Build `LayoutTree` from specs | < 20 ms | `test_build_tree_benchmark` |
| Remove an Area | < 20 ms | `test_remove_area` |
| Save layout | < 10 ms | `test_save_layout_benchmark` |
| Load layout | < 20 ms | `test_load_layout_benchmark` |
| Reposition 3 Overlays | < 10 ms | `test_reposition_overlays_benchmark` |

Benchmarks run on every PR. A regression of more than 20% blocks the PR.

---

## 13. Manual Testing Checklist

Before each release, manually verify:

- [ ] Window opens and closes cleanly on Windows, Linux, macOS.
- [ ] Areas are resizable with the mouse.
- [ ] Areas can be hidden and shown.
- [ ] Layout persists across restarts.
- [ ] Module switch preserves compatible Areas.
- [ ] Editor tabs appear when ≥ 2 Editors.
- [ ] Overlay repositions on window resize.
- [ ] High-DPI display looks correct (150%, 200% scaling).
- [ ] Multiple monitors: floating Areas appear on the correct monitor.
- [ ] Keyboard shortcuts work as expected.
- [ ] No console errors or warnings during normal use.

---

## 14. Definition of Done for Tests

A feature is considered tested when:

- [ ] Unit tests cover the core logic.
- [ ] Widget tests cover the UI behavior.
- [ ] Integration tests cover the interaction with other components.
- [ ] Coverage target is met.
- [ ] No flaky tests.
- [ ] No `time.sleep()` in tests.
- [ ] All tests have clear names describing intent.
- [ ] All tests pass locally and in CI.

---

## 15. Open Questions

### 15.1 Should visual regression tests be added?

**Option A:** Yes — screenshot comparison for the Workspace.
**Option B:** No — defer until the UI is more stable.

**Current lean:** Option B.

### 15.2 Should Hypothesis be used more aggressively?

**Option A:** Yes — property tests for layout invariants.
**Option B:** No — hypothesis is slow and can be flaky with Qt.

**Current lean:** Use Hypothesis only for pure logic (no Qt).

### 15.3 How to test multi-monitor behavior in CI?

CI environments have one virtual screen.

**Current lean:** Mock `QScreen` geometry in tests. Do not attempt to
test actual multi-monitor behavior in CI.
