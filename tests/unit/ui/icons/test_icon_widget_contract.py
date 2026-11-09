"""Contract: widgets do not import providers directly or hardcode glyphs."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_SHELL_FILES = (
    Path("src/cranioz/ui/home/widgets/home_top_bar.py"),
    Path("src/cranioz/ui/home/widgets/community_sidebar.py"),
    Path("src/cranioz/ui/workspace/structure/home_segment.py"),
    Path("src/cranioz/ui/workspace/structure/modules_segment.py"),
    Path("src/cranioz/ui/workspace/structure/extras_segment.py"),
    Path("src/cranioz/ui/home/widgets/start_button.py"),
    Path("src/cranioz/ui/home/widgets/flow_row.py"),
)

_GLYPHS = {
    "☰",
    "?",
    "⚙",
    "→",
    "+",
    "⋮",
    "▭",
    "▯",
    "⌂",
    "◧",
    "◨",
    "⬓",
}


def _string_literals_in_code(source: str) -> set[str]:
    """Return string literals that are *not* docstrings."""
    tree = ast.parse(source)
    literals: set[str] = set()

    # Collect all string literal values.
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            literals.add(node.value)

    # Remove docstrings: first statement of Module, ClassDef, FunctionDef
    # is the docstring if it is a Constant str.
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef))
            and node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            literals.discard(node.body[0].value.value)

    return literals


@pytest.mark.parametrize("file_path", _SHELL_FILES, ids=lambda p: p.name)
def test_widget_does_not_hardcode_glyphs(file_path: Path) -> None:
    source = file_path.read_text(encoding="utf-8")
    literals = _string_literals_in_code(source)
    offenders = _GLYPHS & literals
    assert not offenders, f"{file_path} still hardcodes glyphs: {sorted(offenders)!r}"


def test_widgets_do_not_import_unicode_provider_directly() -> None:
    forbidden = {
        "from cranioz.ui.icons.unicode import UnicodeIconProvider",
        "import cranioz.ui.icons.unicode",
    }
    for file_path in _SHELL_FILES:
        source = file_path.read_text(encoding="utf-8")
        for needle in forbidden:
            assert needle not in source, f"{file_path} imports provider directly: {needle!r}"
