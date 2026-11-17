"""Architecture boundary tests.

Executable specification of the dependency rules defined in
``refactoring_plan.md`` section 4 and section 4.1.

These tests use AST inspection of source files (not runtime imports) so
that they can enforce boundaries on packages that are not yet imported
by any test, and so that they fail loudly when a rule stops being
checked (for example, when a package path is moved and the test
silently inspects an empty directory).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).parent.parent.parent / "src" / "cranioz"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_imports(file_path: Path) -> set[str]:
    """Return the set of module paths imported by ``file_path``.

    Covers ``import x``, ``import x.y as z``, ``from x import y`` and
    ``from x.y import z``. Relative imports (``from . import x``) are
    ignored because they cannot cross package boundaries in the way
    the rules care about.
    """
    if not file_path.exists():
        return set()

    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
                # ``from cranioz.modules.core import module`` imports the
                # submodule ``cranioz.modules.core.module`` too, so record
                # the fully-qualified name of each imported name as well.
                # This catches ``from cranioz.editors import builtin`` and
                # similar re-export paths.
                for alias in node.names:
                    imports.add(f"{node.module}.{alias.name}")

    return imports


def _get_all_py_files(package_path: Path) -> list[Path]:
    if not package_path.exists():
        return []
    return sorted(package_path.rglob("*.py"))


def _iter_imports(files: list[Path]) -> list[tuple[Path, str]]:
    for f in files:
        for imp in _get_imports(f):
            yield f, imp


# ---------------------------------------------------------------------------
# Rule 4.1.1 — modules.core must not import editors
# ---------------------------------------------------------------------------


def test_modules_core_does_not_import_editors() -> None:
    files = _get_all_py_files(SRC_ROOT / "modules" / "core")
    for py_file, imp in _iter_imports(files):
        assert not imp.startswith("cranioz.editors"), (
            f"{py_file.relative_to(SRC_ROOT)} imports '{imp}'. "
            f"Rule 4.1.1: modules.core must not import editors."
        )


# ---------------------------------------------------------------------------
# Rule 4.1.2 — modules.builtin must not import editors or workspace
# ---------------------------------------------------------------------------


def test_modules_builtin_does_not_import_editors_or_workspace() -> None:
    files = _get_all_py_files(SRC_ROOT / "modules" / "builtin")
    for py_file, imp in _iter_imports(files):
        assert not imp.startswith("cranioz.editors"), (
            f"{py_file.relative_to(SRC_ROOT)} imports '{imp}'. "
            f"Rule 4.1.2: modules.builtin must not import concrete Editors."
        )
        assert not imp.startswith("cranioz.ui.workspace"), (
            f"{py_file.relative_to(SRC_ROOT)} imports '{imp}'. "
            f"Rule 4.1.2: modules.builtin must not import Workspace components."
        )


# ---------------------------------------------------------------------------
# Rule 4.1.4 — editors.core.* must not import Modules or Workspace
# ---------------------------------------------------------------------------


def test_editors_core_does_not_import_modules_or_workspace() -> None:
    # The editor package does not exist yet; until Step 4 populates it, the
    # pre-migration location (ui/editors) is the baseline. Both paths are
    # inspected so that the rule fails loudly if neither contains .py files.
    candidates = [
        SRC_ROOT / "editors" / "core",
        SRC_ROOT / "ui" / "editors",
    ]
    files: list[Path] = []
    for c in candidates:
        files.extend(_get_all_py_files(c))

    assert files, (
        "Rule 4.1.4 checked no files: neither editors/core/ nor ui/editors/ "
        "exists with .py files. Refusing to pass silently."
    )

    for py_file, imp in _iter_imports(files):
        assert not imp.startswith("cranioz.modules"), (
            f"{py_file.relative_to(SRC_ROOT)} imports '{imp}'. "
            f"Rule 4.1.4: editors.core must not depend on Modules."
        )
        assert not imp.startswith("cranioz.ui.workspace"), (
            f"{py_file.relative_to(SRC_ROOT)} imports '{imp}'. "
            f"Rule 4.1.4: editors.core must not depend on Workspace Areas."
        )


# ---------------------------------------------------------------------------
# Rule 4.1.11 — editors.core.* must not import ui.theme.compiler
# ---------------------------------------------------------------------------


def test_editors_core_does_not_import_theme_compiler() -> None:
    candidates = [
        SRC_ROOT / "editors" / "core",
        SRC_ROOT / "ui" / "editors",
    ]
    files: list[Path] = []
    for c in candidates:
        files.extend(_get_all_py_files(c))

    for py_file, imp in _iter_imports(files):
        assert "ui.theme.compiler" not in imp, (
            f"{py_file.relative_to(SRC_ROOT)} imports '{imp}'. "
            f"Rule 4.1.11: editors.core must not import ui.theme.compiler "
            f"(QSS application is shell-only)."
        )


# ---------------------------------------------------------------------------
# Domain isolation — nothing below domain may import higher layers
# ---------------------------------------------------------------------------


def test_domain_imports_no_higher_layers() -> None:
    files = _get_all_py_files(SRC_ROOT / "domain")
    forbidden = (
        "cranioz.application",
        "cranioz.infrastructure",
        "cranioz.ui",
        "cranioz.editors",
        "cranioz.modules",
    )
    for py_file, imp in _iter_imports(files):
        for prefix in forbidden:
            assert not imp.startswith(prefix), (
                f"{py_file.relative_to(SRC_ROOT)} imports '{imp}'. "
                f"Domain isolation: domain must not import {prefix}."
            )