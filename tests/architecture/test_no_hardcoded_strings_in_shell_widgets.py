"""Architecture guard: no hardcoded user-facing strings in shell widgets.

The shell widgets (HomePage tree, Top Bar segments, MainWindow,
Workspace placeholder editor, bootstrap) must resolve every
user-facing string through the TranslationService. Hardcoded strings
in these files are a regression: they bypass the catalog, cannot be
translated, and drift from the rest of the application.

This test scans the AST of each shell file and flags string literals
passed directly to a small set of UI-construction sites:

- QLabel(<str>)
- QPushButton(<str>)
- QLineEdit().setPlaceholderText(<str>)
- QWidget.setToolTip(<str>)
- QWidget.setAccessibleName(<str>)
- QWidget.setWindowTitle(<str>)
- QMenu.addAction(<str>)
- QMenu.addMenu(<str>)
- QMessageBox.<method>(<parent>, <str>, <str>)
- QFileDialog.<method>(<parent>, <str>, ...)

A literal is allowed only when it is:
- not a user-facing string (an objectName, a QSS selector, an icon
  glyph, an empty string), or
- explicitly whitelisted below with a comment explaining why.

The test does NOT check the catalog (TranslationValidator covers that).
It only checks that the code routes strings through a translator.

Rationale:
- Hardcoded strings are caught at review time by this test, before
  they reach CI.
- The whitelist documents every exception. Adding an exception
  requires touching this test file, which makes the decision visible
  in a PR.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

# ---------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------

# The shell is the set of files that build the application frame and
# the Home Page. Editors, Tools, Toolbars, dialogs owned by feature
# modules, and domain/application layers are out of scope: they either
# already translate their own strings through EditorContext, or do
# not present strings to the user at all.
_REPO_ROOT = Path(__file__).parents[2]
_SHELL_FILES: tuple[Path, ...] = (
    _REPO_ROOT / "src" / "cranioz" / "__main__.py",
    _REPO_ROOT / "src" / "cranioz" / "ui" / "main_window.py",
    _REPO_ROOT / "src" / "cranioz" / "ui" / "home" / "home_page.py",
    _REPO_ROOT / "src" / "cranioz" / "ui" / "home" / "widgets" / "community_sidebar.py",
    _REPO_ROOT / "src" / "cranioz" / "ui" / "home" / "widgets" / "flow_list.py",
    _REPO_ROOT / "src" / "cranioz" / "ui" / "home" / "widgets" / "flow_row.py",
    _REPO_ROOT / "src" / "cranioz" / "ui" / "home" / "widgets" / "home_bottom_bar.py",
    _REPO_ROOT / "src" / "cranioz" / "ui" / "home" / "widgets" / "home_top_bar.py",
    _REPO_ROOT / "src" / "cranioz" / "ui" / "home" / "widgets" / "project_table.py",
    _REPO_ROOT / "src" / "cranioz" / "ui" / "home" / "widgets" / "start_button.py",
    _REPO_ROOT / "src" / "cranioz" / "ui" / "workspace" / "workspace_spec.py",
    _REPO_ROOT / "src" / "cranioz" / "ui" / "workspace" / "structure" / "home_segment.py",
    _REPO_ROOT / "src" / "cranioz" / "ui" / "workspace" / "structure" / "modules_segment.py",
    _REPO_ROOT / "src" / "cranioz" / "ui" / "workspace" / "structure" / "extras_segment.py",
)

# ---------------------------------------------------------------------
# Whitelist
# ---------------------------------------------------------------------
#
# Each entry is (file_relative_to_repo, literal). The literal must
# appear in exactly the call site described by the comment. Adding an
# entry is a deliberate decision, visible in the PR.
#
# Categories:
# - Glyphs / symbols that are not translated (the glyph IS the UI).
# - objectName / QSS selectors (technical identifiers).
# - File-dialog filters whose only translatable part is the label
#   (already passed through tr() at the call site, so the literal
#   argument is a composite string; see dialog.stl_filter).
# - Empty strings.
_WHITELIST: tuple[tuple[str, str], ...] = (
    # Glyphs used as button content. Replaced by icons in a later
    # phase (ThemeService.icon_name); until then they are the UI.
    ("src/cranioz/ui/home/widgets/home_top_bar.py", "☰"),
    ("src/cranioz/ui/home/widgets/home_top_bar.py", "?"),
    ("src/cranioz/ui/home/widgets/home_top_bar.py", "⚙"),
    ("src/cranioz/ui/home/widgets/start_button.py", "→"),
    ("src/cranioz/ui/workspace/structure/modules_segment.py", "+"),
    # Separator glyph in the flow row.
    ("src/cranioz/ui/home/widgets/flow_row.py", "→"),
)

# ---------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------


class _CallSite:
    """A call expression whose positional or keyword arguments are
    inspected for string literals."""

    __slots__ = ("func_name", "kw_names", "positions")

    def __init__(
        self,
        func_name: str,
        positions: tuple[int, ...] = (),
        kw_names: tuple[str, ...] = (),
    ) -> None:
        self.func_name = func_name
        self.positions = positions
        self.kw_names = kw_names


# Calls whose relevant string arguments are inspected. Only the
# arguments that reach the UI as user-facing text are listed.
_CALL_SITES: tuple[_CallSite, ...] = (
    # Constructors / methods that display text.
    _CallSite("QLabel", positions=(0,)),
    _CallSite("QPushButton", positions=(0,)),
    _CallSite("QLineEdit", positions=(0,)),  # first arg is text, usually ""
    _CallSite("setPlaceholderText", positions=(0,)),
    _CallSite("setToolTip", positions=(0,)),
    _CallSite("setAccessibleName", positions=(0,)),
    _CallSite("setWindowTitle", positions=(0,)),
    _CallSite("setText", positions=(0,)),
    _CallSite("addAction", positions=(0,)),
    _CallSite("addMenu", positions=(0,)),
    # QMessageBox.<method>(parent, title, text)
    _CallSite("information", positions=(1, 2)),
    _CallSite("warning", positions=(1, 2)),
    _CallSite("critical", positions=(1, 2)),
    _CallSite("question", positions=(1, 2)),
    # QFileDialog.get<X>FileName(parent, title, ...) — only title.
    _CallSite("getOpenFileName", positions=(1,)),
    _CallSite("getSaveFileName", positions=(1,)),
    _CallSite("getExistingDirectory", positions=(1,)),
)


def _call_name(node: ast.Call) -> str:
    """Return the trailing identifier of a call's callee.

    ``foo.bar(...)``  → "bar"
    ``bar(...)``      → "bar"
    ``foo().bar(...)`` → "bar"
    """
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _is_tr_call(node: ast.AST) -> bool:
    """Return True if the node is a tr() / _tr() / translation_service.tr()
    call."""
    if not isinstance(node, ast.Call):
        return False
    name = _call_name(node)
    return name in {"tr", "_tr"}


def _literal_strings_in_arg(node: ast.AST) -> list[str]:
    """Return the string literals inside an argument.

    - A plain ``Constant`` string yields [value].
    - A ``JoinedStr`` (f-string) yields its literal fragments.
    - A ``tr(...)`` / ``_tr(...)`` call yields [] (translated).
    - A ``str.format(...)`` call yields [] (the base is checked).
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.JoinedStr):
        result: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                result.append(value.value)
        return result
    return []


def _arg_at(call: ast.Call, position: int) -> ast.AST | None:
    if len(call.args) > position:
        return call.args[position]
    return None


def _kwarg(call: ast.Call, name: str) -> ast.AST | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


# ---------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------


def _scan_file(path: Path) -> list[tuple[int, str, str]]:
    """Return (lineno, call_name, literal) for every offending literal.

    ``literal`` is the string value (for f-strings, the offending
    literal fragment). The lineno points at the call site.
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    offenders: list[tuple[int, str, str]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        site = next((s for s in _CALL_SITES if s.func_name == name), None)
        if site is None:
            continue

        candidates: list[ast.AST] = []
        for position in site.positions:
            arg = _arg_at(node, position)
            if arg is not None:
                candidates.append(arg)
        for kw_name in site.kw_names:
            arg = _kwarg(node, kw_name)
            if arg is not None:
                candidates.append(arg)

        for arg in candidates:
            if _is_tr_call(arg):
                continue
            for literal in _literal_strings_in_arg(arg):
                if literal == "":
                    continue
                offenders.append((node.lineno, name, literal))

    return offenders


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------


@pytest.mark.architecture
@pytest.mark.parametrize(
    "shell_file",
    _SHELL_FILES,
    ids=lambda p: str(p.relative_to(_REPO_ROOT)).replace("\\", "/"),
)
def test_shell_file_has_no_hardcoded_ui_strings(shell_file: Path) -> None:
    """Every shell file must route user-facing strings through tr()."""
    if not shell_file.is_file():
        pytest.fail(f"shell file not found: {shell_file}")

    offenders = _scan_file(shell_file)
    if not offenders:
        return

    relative = str(shell_file.relative_to(_REPO_ROOT)).replace("\\", "/")
    unwhitelisted = [
        (lineno, name, literal)
        for lineno, name, literal in offenders
        if (relative, literal) not in _WHITELIST
    ]

    if unwhitelisted:
        lines = [
            f"{relative}:{lineno}: {name}(...) uses hardcoded string "
            f"{literal!r}. Wrap it with tr(key, source) / _tr(key, source)."
            for lineno, name, literal in unwhitelisted
        ]
        pytest.fail(
            "Hardcoded user-facing string(s) found in the shell:\n"
            + "\n".join(lines)
            + "\n\nIf the literal is not user-facing (a glyph, an "
            "objectName, a QSS selector, a composite file-dialog "
            "filter), add it to _WHITELIST in this test file, with a "
            "comment explaining why."
        )


def test_whitelist_entries_are_used() -> None:
    """Every whitelist entry must still match at least one offending
    literal. A stale entry means the code changed and the whitelist
    was not updated."""
    seen: set[tuple[str, str]] = set()
    for shell_file in _SHELL_FILES:
        if not shell_file.is_file():
            continue
        relative = str(shell_file.relative_to(_REPO_ROOT)).replace("\\", "/")
        for _lineno, _name, literal in _scan_file(shell_file):
            seen.add((relative, literal))

    stale = [entry for entry in _WHITELIST if entry not in seen]
    if stale:
        pytest.fail(
            "Stale whitelist entries (the literal is no longer produced "
            "by the file):\n"
            + "\n".join(f"  {path}: {literal!r}" for path, literal in stale)
            + "\n\nRemove them from _WHITELIST in this test file."
        )
