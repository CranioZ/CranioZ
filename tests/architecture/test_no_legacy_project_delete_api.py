"""Architecture guard (implementation_plan.md §8.9).

No call site may use a pre-Sprint-J API or bypass the ProjectManager
to delete project files directly.

The gate protects three boundaries:

1. ADR-0016 removed `ProjectCatalog(repository=...)` and
   `ProjectCatalog.refresh()`. Any call site using them is a
   regression.

2. project.md §10 forbids the Home Page (and any UI) from deleting
   project files directly. The only place a `project.json` may be
   *accessed* is `FilesystemProjectRepository` (and its two
   collaborators, `ProjectPathResolver` and `ProjectSerialization`).

3. Sprint J confirms that deletion is coordinated by the
   ProjectManager. No module outside the project subsystem may call
   `ProjectRepository.delete` directly.

This is the executable form of §8.9:

    "No call site uses a pre-ADR API that the accepted ADR removed
     without a shim ... Verified by grep in the sprint close review."

The test uses textual grep for the `.refresh()` and `.delete(...)`
checks (mirroring the §8.9 phrasing), and AST for the
`ProjectCatalog(...)` constructor and the `project.json` access
detection, where argument position matters and mere *mention* in a
docstring must not be flagged.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).parents[2]
_SRC = _REPO_ROOT / "src" / "cranioz"

# ---------------------------------------------------------------------
# Whitelist: files that may legitimately access project.json or
# ProjectRepository.delete. Adding an entry is a deliberate decision,
# visible in the PR.
# ---------------------------------------------------------------------

_PROJECT_JSON_WHITELIST: frozenset[Path] = frozenset(
    {
        _SRC / "infrastructure" / "project" / "filesystem_project_repository.py",
        _SRC / "infrastructure" / "project" / "project_path_resolver.py",
        _SRC / "infrastructure" / "project" / "project_serialization.py",
    }
)

_REPOSITORY_DELETE_WHITELIST: frozenset[Path] = frozenset(
    {
        # The manager is the single lifecycle writer (project.md §25).
        _SRC / "main_window" / "project" / "manager.py",
    }
)

# ---------------------------------------------------------------------
# project.json access detection tables (test 3).
# ---------------------------------------------------------------------

_ACCESS_LITERALS: tuple[str, ...] = ("project.json",)
_PATH_CONSTRUCTORS: frozenset[str] = frozenset({"Path", "PurePath"})
_OPEN_LIKE: frozenset[str] = frozenset({"open"})
_DESTRUCTIVE_METHODS: frozenset[str] = frozenset({"unlink", "rmtree", "rmdir", "remove"})

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _python_files() -> list[Path]:
    return [p for p in _SRC.rglob("*.py") if p.is_file() and p.name != "__init__.py"]


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _expression_mentions(node: ast.AST, literals: tuple[str, ...]) -> bool:
    """Return True if any string Constant in ``node`` contains one of
    ``literals``. Docstrings and comments are not ``Constant`` nodes
    inside a ``Call``'s receiver, so they do not trigger.

    This is a conservative check: a false negative (missing a
    destructive call) is preferable to a false positive that forces
    whitelist churn.
    """
    return any(
        isinstance(child, ast.Constant)
        and isinstance(child.value, str)
        and any(lit in child.value for lit in literals)
        for child in ast.walk(node)
    )


def _project_json_accesses(tree: ast.AST, path: Path) -> list[str]:
    """Return a list of human-readable project.json access descriptions.

    Detects *access*, not *mention*:

    - ``Path("...project.json...")`` / ``PurePath(...)``
    - ``open("...project.json...", ...)`` (first arg only)
    - ``<expr mentioning project.json>.unlink()`` /
      ``.rmtree()`` / ``.rmdir()`` / ``.remove()``
    """
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        name = _call_name(node)

        # Case 1 + 2: Path(...) / PurePath(...) / open(...) with a
        # literal string containing "project.json".
        if (name in _PATH_CONSTRUCTORS or name in _OPEN_LIKE) and node.args:
            arg = node.args[0]
            if (
                isinstance(arg, ast.Constant)
                and isinstance(arg.value, str)
                and any(lit in arg.value for lit in _ACCESS_LITERALS)
            ):
                offenders.append(
                    f"{path.relative_to(_REPO_ROOT)}:{node.lineno}: {name}({arg.value!r})"
                )
                continue

        # Case 3: destructive method on a receiver that mentions
        # "project.json".
        if isinstance(node.func, ast.Attribute) and node.func.attr in _DESTRUCTIVE_METHODS:
            receiver = node.func.value
            if _expression_mentions(receiver, _ACCESS_LITERALS):
                offenders.append(
                    f"{path.relative_to(_REPO_ROOT)}:{node.lineno}: "
                    f".{node.func.attr}() on project.json expression"
                )

    return offenders


# ---------------------------------------------------------------------
# Test 1: no call site constructs ProjectCatalog(repository=...)
# ---------------------------------------------------------------------


def test_no_call_site_constructs_project_catalog_with_repository() -> None:
    """ADR-0016 removed `ProjectCatalog(repository=...)`."""
    offenders: list[str] = []
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if _call_name(node) != "ProjectCatalog":
                continue
            for kw in node.keywords:
                if kw.arg == "repository":
                    offenders.append(
                        f"{path.relative_to(_REPO_ROOT)}:{node.lineno}: "
                        f"ProjectCatalog(repository=...) is the pre-ADR-0016 API"
                    )
    assert not offenders, "\n".join(offenders)


# ---------------------------------------------------------------------
# Test 2: no call site calls ProjectCatalog.refresh()
# ---------------------------------------------------------------------


def test_no_call_site_calls_project_catalog_refresh() -> None:
    """ADR-0016 removed `ProjectCatalog.refresh()`.

    A `refresh()` call on a *different* class (e.g. `HomePage.refresh`,
    `ProjectTable.refresh`) is allowed and common. This test is
    necessarily textual: we cannot infer the receiver type without
    type inference. We grep for `.refresh()` in files that also
    mention `ProjectCatalog`, and fail if any is found.

    A future AST/type-aware upgrade can tighten this; the §8.9
    phrasing ("grep in the sprint close review") authorizes the
    textual form.
    """
    offenders: list[str] = []
    for path in _python_files():
        source = path.read_text(encoding="utf-8")
        if "ProjectCatalog" not in source or ".refresh(" not in source:
            continue
        for lineno, line in enumerate(source.splitlines(), start=1):
            if ".refresh(" in line and "catalog" in line.lower():
                offenders.append(f"{path.relative_to(_REPO_ROOT)}:{lineno}: {line.strip()}")
    assert not offenders, (
        "ProjectCatalog.refresh() was removed by ADR-0016. "
        "Freshness is automatic via SynchronizedProjectIndex. "
        "Offending call site(s):\n" + "\n".join(offenders)
    )


# ---------------------------------------------------------------------
# Test 3: only FilesystemProjectRepository may access project.json
# ---------------------------------------------------------------------


def test_only_filesystem_repository_references_project_json() -> None:
    """project.md §10: no UI or domain module may *access* project.json.

    The repository, the path resolver, and the serializer own the
    filename. Everything else must go through them.
    """
    offenders: list[str] = []
    for path in _python_files():
        if path in _PROJECT_JSON_WHITELIST:
            continue
        source = path.read_text(encoding="utf-8")
        # Cheap pre-filter: skip AST parse if the filename is not
        # mentioned at all.
        if "project.json" not in source:
            continue
        tree = ast.parse(source, filename=str(path))
        offenders.extend(_project_json_accesses(tree, path))

    assert not offenders, (
        "project.json may only be accessed by FilesystemProjectRepository, "
        "ProjectPathResolver, and ProjectSerialization. "
        "Offending access site(s):\n" + "\n".join(offenders)
    )


# ---------------------------------------------------------------------
# Test 4: only ProjectManager may call ProjectRepository.delete
# ---------------------------------------------------------------------


def test_only_project_manager_calls_repository_delete() -> None:
    """project.md §25: the Project Manager is the single lifecycle writer.

    Outside the manager, no production module may call
    `.delete(...)` on a `ProjectRepository` instance.
    """
    offenders: list[str] = []
    for path in _python_files():
        if path in _REPOSITORY_DELETE_WHITELIST:
            continue
        source = path.read_text(encoding="utf-8")
        if "ProjectRepository" not in source or ".delete(" not in source:
            continue
        for lineno, line in enumerate(source.splitlines(), start=1):
            if ".delete(" not in line or "def delete" in line:
                continue
            if "repository.delete" in line or "_repository.delete" in line:
                offenders.append(f"{path.relative_to(_REPO_ROOT)}:{lineno}: {line.strip()}")
    assert not offenders, (
        "Only ProjectManager may call ProjectRepository.delete "
        "(project.md §25). Offending call site(s):\n" + "\n".join(offenders)
    )
