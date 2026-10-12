"""ProjectPathResolver.

Resolves the root directory where CranioZ projects are stored.

Rules:
- The resolver is initialized once at boot and remains stable.
- If config provides a path, it is used.
- If config provides None, the default is used:
  <user_home>/Documents/CranioZ/Projects
- If the directory does not exist, it is created.
- If it cannot be created or accessed, the resolver raises
  ProjectRootInaccessible.
"""

from __future__ import annotations

from pathlib import Path


class ProjectRootInaccessible(Exception):
    """Raised when the project root cannot be resolved, created, or accessed."""


DEFAULT_PROJECT_ROOT_NAME = "CranioZ"
DEFAULT_PROJECTS_DIR_NAME = "Projects"


class ProjectPathResolver:
    def __init__(self) -> None:
        self._project_root: Path | None = None

    def initialize(
        self,
        configured_root: str | None,
        *,
        create: bool = True,
    ) -> Path:
        """Resolve and store the project root.

        Args:
            configured_root: path from configuration, or None to use the default.
            create: if True, create the directory when it does not exist.

        Returns:
            The resolved project root.

        Raises:
            ProjectRootInaccessible: if the directory cannot be used.
        """
        root = self._resolve(configured_root)

        if not root.exists():
            if not create:
                raise ProjectRootInaccessible(f"project root does not exist: {root}")
            try:
                root.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise ProjectRootInaccessible(
                    f"could not create project root: {root}: {exc}"
                ) from exc

        if not root.is_dir():
            raise ProjectRootInaccessible(f"project root is not a directory: {root}")

        self._project_root = root
        return root

    @property
    def project_root(self) -> Path:
        if self._project_root is None:
            raise ProjectRootInaccessible("resolver is not initialized")
        return self._project_root

    def resolve(self, relative: str) -> Path:
        """Resolve a logical relative path against the project root.

        The relative path is validated against traversal. No assumption is
        made about the existence of the target.
        """
        if self._project_root is None:
            raise ProjectRootInaccessible("resolver is not initialized")

        candidate = (self._project_root / relative).resolve()
        root = self._project_root.resolve()

        if root not in candidate.parents and candidate != root:
            raise ProjectRootInaccessible(
                f"path escapes project root: {relative}"
            )
        return candidate

    @staticmethod
    def _resolve(configured_root: str | None) -> Path:
        if configured_root:
            return Path(configured_root).expanduser()
        return (
            Path.home()
            / "Documents"
            / DEFAULT_PROJECT_ROOT_NAME
            / DEFAULT_PROJECTS_DIR_NAME
        )
