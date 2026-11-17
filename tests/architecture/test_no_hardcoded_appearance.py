"""Architecture boundary tests.

Executable specification of the dependency rules defined in
refactoring_plan.md section 4 and section 4.1.
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC_ROOT = Path(__file__).parent.parent.parent / "src" / "cranioz"


def _is_type_checking_test(test: ast.expr) -> bool:
    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
        return True
    if (
        isinstance(test, ast.Attribute)
        and isinstance(test.value, ast.Name)
        and test.value.id == "typing"
        and test.attr == "TYPE_CHECKING"
    ):
        return True
    return False


def _get_imports(file_path: Path) -> set[str]:
    """Return the set of runtime module paths imported by file_path."""
    if not file_path.exists():
        return set()

    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    imports: set[str] = set()

    def _visit(node: ast.AST) -> None:
        if isinstance(node, ast.If) and _is_type_checking_test(node.test):
            for child in node.orelse:
                _visit(child)
            return

        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
            for alias in node.names:
                imports.add(f"{node.module}.{alias.name}")

        for child in ast.iter_child_nodes(node):
            _visit(child)

    _visit(tree)
    return imports


def _get_all_py_files(package_path: Path) -> list[Path]:
    if not package_path.exists():
        return []
    return sorted(package_path.rglob("*.py"))


def _iter_imports(files: list[Path]) -> list[tuple[Path, str]]:
    for f in files:
        for imp in _get_imports(f):
            yield f, imp


def test_modules_core_does_not_import_editors() -> None:
    files = _get_all_py_files(SRC_ROOT / "modules" / "core")
    for py_file, imp in _iter_imports(files):
        assert not imp.startswith("cranioz.editors"), (
            f"{py_file.relative_to(SRC_ROOT)} imports '{imp}'. "
            f"Rule 4.1.1: modules.core must not import editors."
        )


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


def test_editors_core_does_not_import_modules_or_workspace() -> None:
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
            f"Rule 4.1.11: editors.core must not import ui.theme.compiler."
        )


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
