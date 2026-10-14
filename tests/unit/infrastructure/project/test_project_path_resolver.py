"""Tests for ProjectPathResolver.

ProjectPathResolver derives every file path inside a CranioZ
project from a ProjectId and the projects root. It never escapes
the project directory, and it validates the ProjectId at
construction time.

These tests do not touch the real filesystem except in the
``exists()`` tests, which use ``tmp_path``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cranioz.domain.project.project_id import ProjectId
from cranioz.infrastructure.project.project_path_resolver import (
    PATIENT_RECORD_FILE_NAME,
    PROJECT_FILE_NAME,
    WORKFLOW_FILE_NAME,
    ProjectPathInaccessible,
    ProjectPathResolver,
)

# ----- Helpers ------------------------------------------------------


def _resolver(
    projects_root: Path,
    project_id: str = "abc-123",
) -> ProjectPathResolver:
    return ProjectPathResolver(
        projects_root=projects_root,
        project_id=ProjectId(project_id),
    )


# ----- Identity -----------------------------------------------------


def test_resolver_holds_projects_root(tmp_path: Path) -> None:
    resolver = _resolver(tmp_path)
    assert resolver.projects_root == tmp_path


def test_resolver_holds_project_id(tmp_path: Path) -> None:
    resolver = _resolver(tmp_path, "abc-123")
    assert resolver.project_id == ProjectId("abc-123")


# ----- Standard paths -----------------------------------------------


def test_project_dir_is_under_projects_root(tmp_path: Path) -> None:
    resolver = _resolver(tmp_path, "abc-123")
    assert resolver.project_dir == tmp_path / "abc-123"


def test_project_file(tmp_path: Path) -> None:
    resolver = _resolver(tmp_path, "abc-123")
    assert resolver.project_file == tmp_path / "abc-123" / PROJECT_FILE_NAME


def test_patient_record_file(tmp_path: Path) -> None:
    resolver = _resolver(tmp_path, "abc-123")
    assert resolver.patient_record_file == (tmp_path / "abc-123" / PATIENT_RECORD_FILE_NAME)


def test_workflow_file(tmp_path: Path) -> None:
    resolver = _resolver(tmp_path, "abc-123")
    assert resolver.workflow_file == tmp_path / "abc-123" / WORKFLOW_FILE_NAME


def test_standard_file_names_are_constants() -> None:
    assert PROJECT_FILE_NAME == "project.json"
    assert PATIENT_RECORD_FILE_NAME == "patient_record.json"
    assert WORKFLOW_FILE_NAME == "workflow.json"


# ----- resource() ---------------------------------------------------


def test_resource_with_posix_separator(tmp_path: Path) -> None:
    resolver = _resolver(tmp_path, "abc-123")
    resolved = resolver.resource("imaging/ct.dcm")
    assert resolved == (tmp_path / "abc-123" / "imaging" / "ct.dcm").resolve()


def test_resource_with_nested_path(tmp_path: Path) -> None:
    resolver = _resolver(tmp_path, "abc-123")
    resolved = resolver.resource("planning/osteotomies/lefort_i.json")
    assert (
        resolved == (tmp_path / "abc-123" / "planning" / "osteotomies" / "lefort_i.json").resolve()
    )


def test_resource_rejects_empty(tmp_path: Path) -> None:
    resolver = _resolver(tmp_path)
    with pytest.raises(ProjectPathInaccessible, match="must not be empty"):
        resolver.resource("")


def test_resource_rejects_absolute_posix(tmp_path: Path) -> None:
    resolver = _resolver(tmp_path)
    with pytest.raises(ProjectPathInaccessible, match="absolute"):
        resolver.resource("/etc/passwd")


def test_resource_rejects_traversal(tmp_path: Path) -> None:
    resolver = _resolver(tmp_path)
    with pytest.raises(ProjectPathInaccessible, match="escapes"):
        resolver.resource("../outside")


def test_resource_rejects_deep_traversal(tmp_path: Path) -> None:
    resolver = _resolver(tmp_path)
    with pytest.raises(ProjectPathInaccessible, match="escapes"):
        resolver.resource("../../etc/passwd")


def test_resource_accepts_path_that_stays_inside(tmp_path: Path) -> None:
    # "foo/../bar" resolves back inside the project. The final
    # resolved path is inside, so it is accepted.
    resolver = _resolver(tmp_path, "abc-123")
    resolved = resolver.resource("foo/../bar")
    assert resolved == (tmp_path / "abc-123" / "bar").resolve()


# ----- ProjectId validation -----------------------------------------


def test_project_id_empty_is_rejected(tmp_path: Path) -> None:
    # ProjectId itself rejects empty; we cannot even build it.
    with pytest.raises(ValueError):
        ProjectId("")


def test_project_id_with_slash_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ProjectPathInaccessible, match="separators"):
        ProjectPathResolver(
            projects_root=tmp_path,
            project_id=ProjectId("abc/def"),
        )


def test_project_id_with_backslash_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ProjectPathInaccessible, match="separators"):
        ProjectPathResolver(
            projects_root=tmp_path,
            project_id=ProjectId("abc\\def"),
        )


def test_project_id_with_dotdot_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ProjectPathInaccessible, match=r"\.\."):
        ProjectPathResolver(
            projects_root=tmp_path,
            project_id=ProjectId("abc..def"),
        )


def test_project_id_with_colon_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ProjectPathInaccessible, match=":"):
        ProjectPathResolver(
            projects_root=tmp_path,
            project_id=ProjectId("C:abc"),
        )


def test_project_id_starting_with_dot_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ProjectPathInaccessible, match="start with"):
        ProjectPathResolver(
            projects_root=tmp_path,
            project_id=ProjectId(".hidden"),
        )


def test_project_id_with_control_character_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ProjectPathInaccessible, match="control"):
        ProjectPathResolver(
            projects_root=tmp_path,
            project_id=ProjectId("abc\x00def"),
        )


def test_project_id_with_newline_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ProjectPathInaccessible, match="control"):
        ProjectPathResolver(
            projects_root=tmp_path,
            project_id=ProjectId("abc\ndef"),
        )


# ----- exists() -----------------------------------------------------


def test_exists_returns_false_when_dir_missing(tmp_path: Path) -> None:
    resolver = _resolver(tmp_path, "abc-123")
    assert resolver.exists() is False


def test_exists_returns_true_when_dir_present(tmp_path: Path) -> None:
    project_dir = tmp_path / "abc-123"
    project_dir.mkdir()
    resolver = _resolver(tmp_path, "abc-123")
    assert resolver.exists() is True


def test_exists_is_false_when_path_is_a_file(tmp_path: Path) -> None:
    # A file where the project directory should be is not "existing".
    file_path = tmp_path / "abc-123"
    file_path.write_text("x", encoding="utf-8")
    resolver = _resolver(tmp_path, "abc-123")
    assert resolver.exists() is False
