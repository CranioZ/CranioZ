"""Ensure shared appearance values are not hardcoded in the shell.

Per themes-and-design-tokens.md §10.4, the Qt presentation layer MUST
consume tokens via ThemeService / ThemeCompiler. Shared colors and
opacity MUST NOT be hardcoded in shell widgets.

Allowed files:

- ``cranioz/ui/theme/tokens.py``    — canonical token values.
- ``cranioz/ui/theme/compiler.py``  — the only place tokens become QSS.

Excluded from the scan:

- clinical color definitions (segmentation palettes, etc.);
- imaging data;
- tests;
- third-party.

Known debt
----------
The following files still contain hardcoded colors from before the
appearance system existed. They are tracked here as a frozen baseline:
the test fails only if a *new* hardcoded color appears, or if an
existing debt file grows beyond its frozen count.

Migrating them is part of the widget migration sprint (Sprint F+).
Removing a file or reducing its count is encouraged.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: Files allowed to contain literal colors: the canonical token module
#: and the compiler (which composes from those tokens).
_ALLOWED_FILES: frozenset[str] = frozenset(
    {
        "src/cranioz/ui/theme/tokens.py",
        "src/cranioz/ui/theme/compiler.py",
    }
)

#: Files with pre-existing hardcoded colors that have NOT been migrated
#: to tokens yet. This set MUST shrink over time. Adding a file here is
#: a regression that requires a TODO in the sprint backlog.
_KNOWN_DEBT_FILES: frozenset[str] = frozenset(
    {
        "src/cranioz/ui/home/widgets/flow_row.py",
        "src/cranioz/ui/home/widgets/start_button.py",
        "src/cranioz/ui/workspace/areas/area_widget.py",
        "src/cranioz/ui/workspace/workspace.py",
        "src/cranioz/ui/workspace/workspace_spec.py",
        "src/cranioz/ui/editors/viewport_3d/presets.py",
    }
)

#: Frozen literal counts per debt file, observed on 2026-11-08 when the
#: baseline was created. These are upper bounds: a debt file may not
#: grow beyond them. Reduce the number when migrating a literal.
_DEBT_MAX_LITERALS: dict[str, int] = {
    "src/cranioz/ui/home/widgets/flow_row.py": 9,  # not 8
    "src/cranioz/ui/home/widgets/start_button.py": 5,
    "src/cranioz/ui/workspace/areas/area_widget.py": 5,
    "src/cranioz/ui/workspace/workspace.py": 3,
    "src/cranioz/ui/workspace/workspace_spec.py": 1,
    "src/cranioz/ui/editors/viewport_3d/presets.py": 3,
}

#: Directories to scan for hardcoded appearance literals.
_SCAN_ROOT = Path("src/cranioz/ui")

#: Hex colors (#rrggbb or #rgb) and rgba()/rgb() calls.
_COLOR_LITERAL_RE = re.compile(r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b|rgba?\([^)]*\)")

#: Floats that look like opacities (0.90 to 0.99).
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
    """Catch typos in _KNOWN_DEBT_FILES early."""
    missing = [name for name in _KNOWN_DEBT_FILES if not Path(name).is_file()]
    assert not missing, f"_KNOWN_DEBT_FILES references missing files: {missing}"


def test_debt_max_matches_debt_files() -> None:
    """Every debt file has a frozen count; no count is orphaned."""
    assert set(_DEBT_MAX_LITERALS) == _KNOWN_DEBT_FILES


@pytest.mark.parametrize("debt_file", sorted(_KNOWN_DEBT_FILES))
def test_debt_file_has_no_new_hardcoded_colors(debt_file: str) -> None:
    """A debt file may not gain *new* hardcoded literals.

    The baseline is the number of color and opacity literals observed
    when the file was added to _KNOWN_DEBT_FILES. This test does not
    assert an exact snapshot; it asserts that the file has not grown
    beyond the debt it was added for. Reduce the number when migrating
    a literal to a token.
    """
    path = Path(debt_file)
    text = path.read_text(encoding="utf-8")
    color_count = len(_COLOR_LITERAL_RE.findall(text))
    opacity_count = len(_OPACITY_LITERAL_RE.findall(text))
    total = color_count + opacity_count
    budget = _DEBT_MAX_LITERALS[debt_file]
    assert total <= budget, (
        f"{debt_file} has grown beyond its frozen debt: "
        f"expected <= {budget} literals, found {total} "
        f"({color_count} colors, {opacity_count} opacities). "
        f"Migrate a literal to a token, or justify the addition in the PR."
    )
