"""AppPathResolver.

Resolves the application-level paths of CranioZ.

The resolver answers questions like:

- Where is the root directory that contains all projects?
- Where are the flow definitions stored?
- Where is the cache stored?

These paths are configured once at boot from ``paths.json`` and
remain stable for the entire session.

The resolver does NOT know about individual projects. It only
provides the roots that other components use to locate data. The
paths of a specific project are resolved by the ProjectPathResolver
(see ``infrastructure/project/project_path_resolver.py``).

Rules:

- ``initialize`` accepts a ``PathsConfig`` and resolves each root.
- If a path is configured, it is used.
- If a path is ``None``, a default is derived from the user's home
  directory.
- Missing directories are created unless ``create=False`` is passed.
- Failure to resolve or create a directory raises
  ``AppPathInaccessible``.
"""

from __future__ import annotations

from pathlib import Path

from cranioz.config.schema import PathsConfig


class AppPathInaccessible(Exception):
    """Raised when an application path cannot be resolved, created, or accessed."""


DEFAULT_PROJECT_ROOT_NAME = "CranioZ"
DEFAULT_PROJECTS_DIR_NAME = "Projects"
DEFAULT_FLOWS_DIR_NAME = "Flows"
DEFAULT_CACHE_DIR_NAME = "Cache"


class AppPathResolver:
    """Resolves the application-level paths of CranioZ.

    Configured once at boot. Provides the roots that other components
    use to locate data. Does not know about ProjectId or project
    structure.
    """

    def __init__(self) -> None:
        self._projects_root: Path | None = None
        self._flows_root: Path | None = None
        self._cache_root: Path | None = None

    # ----- Initialization -------------------------------------------

    def initialize(
        self,
        config: PathsConfig,
        *,
        create: bool = True,
    ) -> None:
        """Resolve and store the application paths from configuration.

        Args:
            config: the ``PathsConfig`` section of the application
                configuration. May contain ``None`` for any path, in
                which case the default is used.
            create: if True, create missing directories. If False,
                missing directories raise ``AppPathInaccessible``.

        Raises:
            AppPathInaccessible: if any path cannot be resolved,
                created, or accessed.
        """
        self._projects_root = self._resolve_dir(
            configured=config.project_root,
            default=self._default_projects_root(),
            field_name="project_root",
            create=create,
        )
        self._flows_root = self._resolve_dir(
            configured=config.flows_root,
            default=self._default_flows_root(),
            field_name="flows_root",
            create=create,
        )
        self._cache_root = self._resolve_dir(
            configured=config.cache_root,
            default=self._default_cache_root(),
            field_name="cache_root",
            create=create,
        )

    # ----- Accessors ------------------------------------------------

    @property
    def projects_root(self) -> Path:
        """Directory that contains all CranioZ projects.

        Each project lives in a subdirectory named after its
        ``ProjectId``.
        """
        if self._projects_root is None:
            raise AppPathInaccessible("resolver is not initialized")
        return self._projects_root

    @property
    def flows_root(self) -> Path:
        """Directory that contains the flow definitions."""
        if self._flows_root is None:
            raise AppPathInaccessible("resolver is not initialized")
        return self._flows_root

    @property
    def cache_root(self) -> Path:
        """Directory used for transient cached data."""
        if self._cache_root is None:
            raise AppPathInaccessible("resolver is not initialized")
        return self._cache_root

    # ----- Path resolution ------------------------------------------

    def resolve_in_projects_root(self, relative: str) -> Path:
        """Resolve a logical relative path against the projects root.

        The relative path is validated against traversal. No
        assumption is made about the existence of the target.

        This method is intended for low-level infrastructure code.
        Application code should use ``ProjectPathResolver`` for
        per-project paths.

        Raises:
            AppPathInaccessible: if the path escapes the root.
        """
        return self._resolve_under_root(self.projects_root, relative)

    # ----- Internals ------------------------------------------------

    @staticmethod
    def _resolve_under_root(root: Path, relative: str) -> Path:
        candidate = (root / relative).resolve()
        resolved_root = root.resolve()
        if resolved_root not in candidate.parents and candidate != resolved_root:
            raise AppPathInaccessible(f"path escapes root: {relative}")
        return candidate

    @staticmethod
    def _resolve_dir(
        *,
        configured: str | None,
        default: Path,
        field_name: str,
        create: bool,
    ) -> Path:
        path = Path(configured).expanduser() if configured else default

        if not path.exists():
            if not create:
                raise AppPathInaccessible(f"{field_name} does not exist: {path}")
            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise AppPathInaccessible(f"could not create {field_name}: {path}: {exc}") from exc

        if not path.is_dir():
            raise AppPathInaccessible(f"{field_name} is not a directory: {path}")
        return path

    # ----- Defaults -------------------------------------------------

    @staticmethod
    def _default_projects_root() -> Path:
        return Path.home() / "Documents" / DEFAULT_PROJECT_ROOT_NAME / DEFAULT_PROJECTS_DIR_NAME

    @staticmethod
    def _default_flows_root() -> Path:
        return Path.home() / "Documents" / DEFAULT_PROJECT_ROOT_NAME / DEFAULT_FLOWS_DIR_NAME

    @staticmethod
    def _default_cache_root() -> Path:
        return Path.home() / ".cranioz" / DEFAULT_CACHE_DIR_NAME
