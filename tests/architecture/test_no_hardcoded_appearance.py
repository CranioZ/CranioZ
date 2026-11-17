"""Ensure shared appearance values are not hardcoded in the shell.

Per themes-and-design-tokens.md §10.4, the Qt presentation layer MUST
consume tokens via ThemeService / ThemeCompiler. Shared colors and
opacity MUST NOT be hardcoded in shell widgets.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_ALLOWED_FILES: frozenset[str] = frozenset(
    {
        "src/cranioz/ui/theme/tokens.py",
        "src/cranioz/ui/theme/compiler.py",
    }
)

_KNOWN_DEBT_FILES: frozenset[str] = frozenset(
    {
        "src/cranioz/ui/workspace/areas/area_widget.py",
        "src/cranioz/ui/workspace/workspace.py",
        "src/cranioz/editors/views/viewport_3d/presets.py",
        "src/cranioz/editors/core/editor/placeholder_editor.py",
        "src/cranioz/ui/workspace/areas/editor_stack.py",
    }
)

_DEBT_MAX_LITERALS: dict[str, int] = {
    "src/cranioz/ui/workspace/areas/area_widget.py": 5,
    "src/cranioz/ui/workspace/workspace.py": 3,
    "src/cranioz/editors/views/viewport_3d/presets.py": 3,
    "src/cranioz/editors/core/editor/placeholder_editor.py": 1,
    "src/cranioz/ui/workspace/areas/editor_stack.py": 7,
}

_SCAN_ROOT = Path("src/cranioz/ui")

_COLOR_LITERAL_RE = re.compile(r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b|rgba?\([^)]*\)")

_OPACITY_LITERAL_RE = re.compile(r"\b0\.9[0-9]\b")


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def _scan(regex: re.Pattern[str]) -> list[str]:
    offenders: list[str] = []
    for path in _iter_python_files(_SCAN_ROOT):
        posix = path.as_posix()
        if posix in _ALLOWED_FILES:
            continue
        if posix in _KNOWN_DEBT_FILES:
            continue
        text = path.read_text(encoding="utf-8")
        for match in regex.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            offenders.append(f"{posix}:{line}: {match.group(0)}")
    return offenders


def test_no_hardcoded_colors_in_ui_shell() -> None:
    offenders = _scan(_COLOR_LITERAL_RE)
    assert not offenders, (
        "Hardcoded color literals found in the shell. "
        "Use ThemeService / ThemeCompiler tokens instead. "
        "If this file is intentionally deferred, add it to "
        "_KNOWN_DEBT_FILES and open a backlog item.\n" + "\n".join(offenders)
    )


def test_no_hardcoded_opacity_values_in_ui_shell() -> None:
    offenders = _scan(_OPACITY_LITERAL_RE)
    assert not offenders, (
        "Hardcoded opacity-like literals found in the shell. "
        "Use SurfaceTokens via the compiler. "
        "If this file is intentionally deferred, add it to "
        "_KNOWN_DEBT_FILES and open a backlog item.\n" + "\n".join(offenders)
    )


def test_known_debt_files_exist() -> None:
    missing = [name for name in _KNOWN_DEBT_FILES if not Path(name).is_file()]
    assert not missing, f"_KNOWN_DEBT_FILES references missing files: {missing}"


def test_debt_max_matches_debt_files() -> None:
    assert set(_DEBT_MAX_LITERALS) == _KNOWN_DEBT_FILES


@pytest.mark.parametrize("debt_file", sorted(_KNOWN_DEBT_FILES))
def test_debt_file_has_no_new_hardcoded_colors(debt_file: str) -> None:
    path = Path(debt_file)
    text = path.read_text(encoding="utf-8")
    color_count = len(_COLOR_LITERAL_RE.findall(text))
    opacity_count = len(_OPACITY_LITERAL_RE.findall(text))
    total = color_count + opacity_count
    budget = _DEBT_MAX_LITERALS[debt_file]
    assert total == budget, (
        f"{debt_file} has {total} hardcoded literals "
        f"({color_count} colors, {opacity_count} opacities), "
        f"but the frozen budget is {budget}. "
        f"If you removed literals, reduce the budget. "
        f"If you added literals, justify the addition in the PR "
        f"and increase the budget."
    )
