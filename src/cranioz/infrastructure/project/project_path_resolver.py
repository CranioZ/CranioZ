"""ProjectPathResolver.

Resolves file paths inside a specific CranioZ project.

The resolver is initialized with two pieces of information:

- The projects root, provided by ``AppPathResolver.projects_root``.
- The ``ProjectId`` of the project being opened.

From those, it derives every path that belongs to the project:

    <projects_root>/<project_id>/
    <projects_root>/<project_id>/project.json
    <projects_root>/<project_id>/patient_record.json
    <projects_root>/<project_id>/workflow.json
    <projects_root>/<project_id>/imaging/ct.dcm
    <projects_root>/<project_id>/models/maxilla.stl
    ...

The resolver does NOT touch the filesystem beyond checking whether
the project directory exists (``exists()``). It does not create
directories, does not read files, and does not write anything. Those
responsibilities belong to the ProjectRepository.

Rules:

- The ``ProjectId`` value must be a safe path component. Values
  containing ``/``, ``\\``, ``..``, ``:``, control characters, or
  starting with ``.`` are rejected at construction time.
- Every path returned by this resolver is guaranteed to be inside
  the project directory. Traversal attempts through ``resource()``
  raise ``ProjectPathInaccessible``.
- The resolver is stateless after construction. It can be reused
  for the lifetime of the project.

See also:

- ``infrastructure/app/app_path_resolver.py`` — application-level
  paths (projects root, flows root, cache root).
- ADR-0004 and ``project_pt.md`` §14 — the design rationale for
  separating application paths from project paths.
"""

from __future__ import annotations

from pathlib import Path

from cranioz.domain.project.project_id import ProjectId

# Standard file names inside a project directory. Kept as module
# constants so they can be referenced in tests and in the
# repository without risk of typo.
PROJECT_FILE_NAME = "project.json"
PATIENT_RECORD_FILE_NAME = "patient_record.json"
WORKFLOW_FILE_NAME = "workflow.json"


class ProjectPathInaccessible(Exception):
    """Raised when a project path cannot be resolved."""


class ProjectPathResolver:
    """Resolves file paths inside a specific CranioZ project.

    The resolver is built once per project, typically when the
    ProjectManager opens the project. It does not touch the disk
    except when ``exists()`` is called.
    """

    def __init__(
        self,
        projects_root: Path,
        project_id: ProjectId,
    ) -> None:
        self._validate_project_id(project_id)
        self._projects_root = projects_root
        self._project_id = project_id

    # ----- Identity ------------------------------------------------

    @property
    def projects_root(self) -> Path:
        """The root directory that contains all projects."""
        return self._projects_root

    @property
    def project_id(self) -> ProjectId:
        """The ProjectId this resolver was built for."""
        return self._project_id

    # ----- Standard paths ------------------------------------------

    @property
    def project_dir(self) -> Path:
        """Directory of this project: ``<projects_root>/<project_id>``."""
        return self._projects_root / self._project_id.value

    @property
    def project_file(self) -> Path:
        """The project.json file of this project."""
        return self.project_dir / PROJECT_FILE_NAME

    @property
    def patient_record_file(self) -> Path:
        """The patient_record.json file of this project."""
        return self.project_dir / PATIENT_RECORD_FILE_NAME

    @property
    def workflow_file(self) -> Path:
        """The workflow.json file of this project."""
        return self.project_dir / WORKFLOW_FILE_NAME

    # ----- Free-form resources -------------------------------------

    def resource(self, relative: str) -> Path:
        """Resolve a logical relative path inside the project.

        Accepts POSIX-style (``"imaging/ct.dcm"``) and Windows-style
        (``"imaging\\ct.dcm"``) separators. Both are normalized to
        the platform's separator internally.

        The returned path is guaranteed to be inside the project
        directory. Traversal attempts (``..``) or absolute paths
        raise ``ProjectPathInaccessible``.

        The method does not check whether the target exists.
        """
        if not relative:
            raise ProjectPathInaccessible("relative path must not be empty")

        # Reject absolute paths in a platform-independent way.
        # Path(...).is_absolute() only detects platform-native
        # absolutes: on Windows it does not detect "/etc/passwd",
        # because a leading "/" is interpreted as the root of the
        # current drive. Since the resolver must behave the same on
        # every platform, we reject any leading separator and any
        # drive letter explicitly.
        if relative.startswith(("/", "\\")):
            raise ProjectPathInaccessible(f"relative path must not be absolute: {relative!r}")
        if len(relative) >= 2 and relative[1] == ":":
            # Windows drive letter, e.g. "C:...".
            raise ProjectPathInaccessible(f"relative path must not be absolute: {relative!r}")
        if Path(relative).is_absolute():
            # Covers any remaining platform-specific absolute form.
            raise ProjectPathInaccessible(f"relative path must not be absolute: {relative!r}")

        project_dir = self.project_dir.resolve()
        candidate = (project_dir / relative).resolve()

        if project_dir not in candidate.parents and candidate != project_dir:
            raise ProjectPathInaccessible(f"path escapes project directory: {relative!r}")
        return candidate

    # ----- State ---------------------------------------------------

    def exists(self) -> bool:
        """Return True if the project directory exists on disk.

        Does not check for individual files: the caller may want to
        inspect the project directory even if some files are missing.
        """
        return self.project_dir.is_dir()

    # ----- Validation ----------------------------------------------

    @staticmethod
    def _validate_project_id(project_id: ProjectId) -> None:
        """Reject ProjectIds that cannot be used as a path component.

        The ProjectId is a domain-level concept; it may contain any
        string the domain allows. This resolver, however, is about
        to embed it into a filesystem path, so it must be a safe
        single path segment.

        Rejected patterns:

        - empty or whitespace-only
        - contains ``/`` or ``\\`` (path separators)
        - contains ``..`` (traversal)
        - contains ``:`` (Windows drive separator, NTFS stream
          separator)
        - contains ASCII control characters (0x00-0x1F)
        - starts with ``.`` (would produce hidden directories, and
          would allow ``.`` or ``..`` themselves)
        """
        value = project_id.value

        if not value or not value.strip():
            raise ProjectPathInaccessible("ProjectId value must not be empty or whitespace only")
        if "/" in value or "\\" in value:
            raise ProjectPathInaccessible(
                f"ProjectId value must not contain path separators: {value!r}"
            )
        if ".." in value:
            raise ProjectPathInaccessible(f"ProjectId value must not contain '..': {value!r}")
        if ":" in value:
            raise ProjectPathInaccessible(f"ProjectId value must not contain ':': {value!r}")
        if any(ord(ch) < 0x20 for ch in value):
            raise ProjectPathInaccessible(
                f"ProjectId value must not contain control characters: {value!r}"
            )
        if value.startswith("."):
            raise ProjectPathInaccessible(f"ProjectId value must not start with '.': {value!r}")
