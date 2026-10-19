"""FilesystemProjectRepository — filesystem adapter for ProjectRepository.

Implements the `ProjectRepository` port (Peça 7.1) over a directory tree:

    <projects_root>/
    └── <project_id>/
        ├── project.json        (owned by this repository)
        └── patient_record.json (owned by the Patient persistence layer;
                                 not read or written here)

The repository uses `ProjectPathResolver` for path resolution and never
constructs filesystem paths manually. `ProjectPathResolver` guarantees
that every resolved path stays inside the project directory, so this
repository cannot be tricked into writing outside the projects root.

Design rules (see `project.md` §11-§12):

- No lifecycle decisions. `create` creates; `delete` deletes. The
  Project Manager (Peça 7.5) coordinates *when* to call them.
- Every infrastructure failure is translated into the
  `ProjectRepositoryError` family. Callers never see `OSError`,
  `FileNotFoundError`, or JSON `DecodeError`.
- `delete` raises `ProjectNotFound` when the project is missing. This
  matches the contract defined in Peça 7.1.
- `exists` checks `project.json`, not the directory. The directory may
  exist because of files owned by other layers; from the repository's
  point of view, a project exists iff its `project.json` is present.
- `delete` removes only `project.json`. Other files belong to other
  persistence layers, which own their own lifecycle.
- `create` is atomic at the level of the visible project directory:
  it writes `project.json` first, then renames into place. A crash
  mid-write leaves no partially-created project that `list_metadata`
  would see.
- `list_metadata` skips corrupted entries and logs them; one bad
  project does not break the Home Page.

Threading: not thread-safe. The Project Manager runs on the main
thread and is the only caller.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from cranioz.application.project.project_errors import (
    ProjectAlreadyExists,
    ProjectCorrupted,
    ProjectNotFound,
    ProjectStorageError,
)
from cranioz.domain.project.project import Project
from cranioz.domain.project.project_id import ProjectId
from cranioz.domain.project.project_summary import ProjectSummary
from cranioz.infrastructure.project.project_path_resolver import (
    PROJECT_FILE_NAME,
    ProjectPathInaccessible,
    ProjectPathResolver,
)
from cranioz.infrastructure.project.project_serialization import (
    ProjectSerializationError,
    project_from_dict,
    project_to_dict,
)

_logger = logging.getLogger(__name__)


class FilesystemProjectRepository:
    """Filesystem-backed implementation of `ProjectRepository`."""

    def __init__(self, projects_root: Path) -> None:
        self._projects_root = Path(projects_root)

    # ----- create ----------------------------------------------------

    def create(self, project: Project) -> None:
        resolver = self._resolver_for(project.project_id)
        project_dir = resolver.project_dir

        # exists() is the authoritative check: a directory without
        # project.json is not a project (it may be a stray directory).
        if resolver.project_file.is_file():
            raise ProjectAlreadyExists(
                f"project already exists: {project.project_id.value!r}",
                project_id=project.project_id,
            )

        try:
            project_dir.mkdir(parents=False, exist_ok=True)
        except OSError as exc:
            raise ProjectStorageError(
                f"cannot create project directory: {project_dir}: {exc}",
                project_id=project.project_id,
            ) from exc

        try:
            self._write_project_json(resolver, project)
        except Exception:
            # Rollback: if we created the directory, remove it. If the
            # directory existed (owned by another layer), leave it alone.
            try:
                if project_dir.is_dir():
                    project_json = resolver.project_file
                    if not project_json.exists():
                        project_dir.rmdir()
            except OSError:
                _logger.exception(
                    "could not roll back project directory after failed create: %s",
                    project_dir,
                )
            raise

    # ----- get -------------------------------------------------------

    def get(self, project_id: ProjectId) -> Project:
        resolver = self._resolver_for(project_id)

        if not resolver.project_file.is_file():
            raise ProjectNotFound(
                f"project not found: {project_id.value!r}",
                project_id=project_id,
            )

        data = self._read_project_json(resolver, project_id)

        try:
            return project_from_dict(data)
        except ProjectSerializationError as exc:
            raise ProjectCorrupted(
                f"project is corrupted: {project_id.value!r}: {exc}",
                project_id=project_id,
            ) from exc

    # ----- update ----------------------------------------------------

    def update(self, project: Project) -> None:
        resolver = self._resolver_for(project.project_id)

        if not resolver.project_file.is_file():
            raise ProjectNotFound(
                f"project not found: {project.project_id.value!r}",
                project_id=project.project_id,
            )

        self._write_project_json(resolver, project)

    # ----- delete ----------------------------------------------------

    def delete(self, project_id: ProjectId) -> None:
        resolver = self._resolver_for(project_id)

        if not resolver.project_file.is_file():
            raise ProjectNotFound(
                f"project not found: {project_id.value!r}",
                project_id=project_id,
            )

        try:
            resolver.project_file.unlink()
        except OSError as exc:
            raise ProjectStorageError(
                f"cannot delete project file: {exc}",
                project_id=project_id,
            ) from exc

    # ----- exists ----------------------------------------------------

    def exists(self, project_id: ProjectId) -> bool:
        resolver = self._resolver_for(project_id)
        return resolver.project_file.is_file()

    # ----- list_metadata --------------------------------------------

    def list_metadata(self) -> tuple[ProjectSummary, ...]:
        summaries: list[ProjectSummary] = []
        for project_id in self.list_ids():
            try:
                project = self.get(project_id)
            except ProjectCorrupted:
                _logger.exception(
                    "skipping corrupted project while listing: %s",
                    project_id.value,
                )
                continue
            except ProjectNotFound:
                # Race: project disappeared between list_ids and get.
                continue
            except ProjectStorageError:
                _logger.exception(
                    "cannot read project while listing: %s",
                    project_id.value,
                )
                continue
            summaries.append(ProjectSummary.from_metadata(project.metadata))
        return tuple(summaries)

    # ----- list_ids --------------------------------------------------

    def list_ids(self) -> tuple[ProjectId, ...]:
        if not self._projects_root.is_dir():
            return ()

        try:
            entries = list(self._projects_root.iterdir())
        except OSError as exc:
            raise ProjectStorageError(
                f"cannot list projects root: {self._projects_root}: {exc}"
            ) from exc

        ids: list[ProjectId] = []
        for entry in entries:
            if not entry.is_dir():
                continue
            if not (entry / PROJECT_FILE_NAME).is_file():
                # Directory exists but no project.json: not a project.
                continue
            try:
                ids.append(ProjectId(entry.name))
            except ValueError:
                # Not a valid ProjectId; skip.
                continue
        return tuple(ids)

    # ----- Internals -------------------------------------------------

    def _resolver_for(self, project_id: ProjectId) -> ProjectPathResolver:
        try:
            return ProjectPathResolver(
                projects_root=self._projects_root,
                project_id=project_id,
            )
        except ProjectPathInaccessible as exc:
            raise ProjectStorageError(
                f"invalid project_id for filesystem: {project_id.value!r}: {exc}",
                project_id=project_id,
            ) from exc

    def _read_project_json(
        self,
        resolver: ProjectPathResolver,
        project_id: ProjectId,
    ) -> dict[str, Any]:
        project_json = resolver.project_file
        try:
            with project_json.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ProjectCorrupted(
                f"invalid JSON in {project_json}: {exc}",
                project_id=project_id,
            ) from exc
        except OSError as exc:
            raise ProjectStorageError(
                f"cannot read {project_json}: {exc}",
                project_id=project_id,
            ) from exc

        if not isinstance(data, dict):
            raise ProjectCorrupted(
                f"project file must be a JSON object: {project_json}",
                project_id=project_id,
            )
        return data

    def _write_project_json(
        self,
        resolver: ProjectPathResolver,
        project: Project,
    ) -> None:
        data = project_to_dict(project)
        project_json = resolver.project_file

        # Write to a temporary file first, then rename, so that a
        # crash mid-write does not leave a partial project.json.
        tmp = project_json.with_suffix(project_json.suffix + ".tmp")
        try:
            with tmp.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
            tmp.replace(project_json)
        except OSError as exc:
            try:
                if tmp.exists():
                    tmp.unlink()
            except OSError:
                _logger.exception("could not remove temporary file: %s", tmp)
            raise ProjectStorageError(
                f"cannot write {project_json}: {exc}",
                project_id=project.project_id,
            ) from exc
