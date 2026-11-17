"""ModuleManifest — declarative metadata for a Module (modules.md v10 §5).

This module defines the data types that a built-in module's
``manifest.py`` returns. The full validation (version parsing,
dependency constraint parsing, uniqueness in the registry) lives in
the ``ModuleRegistry`` and ``ModuleLoader``; this module is data only.

A ModuleManifest carries identity and dependencies. It does **not**
list contributions (Commands, Tools, Editors, UI specs). Those are
declared by the Module implementation (``modules.md`` v10 §5.4).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModuleDependency:
    """A hard dependency on another Module (modules.md v10 §6.1).

    ``version_constraint`` is a semantic-version constraint string
    (e.g. ``">=1.0.0"``, ``">=1.0.0,<2.0.0"``). An empty string means
    "any version".
    """

    module_id: str
    version_constraint: str = ""

    def __post_init__(self) -> None:
        if not self.module_id:
            raise ValueError("ModuleDependency.module_id must not be empty")


@dataclass(frozen=True)
class ModuleManifest:
    """Declarative metadata for a Module (modules.md v10 §5.1).

    Carries identity (``module_id``, ``version``), display keys
    (``label_key``, ``description_key``), the Python entry point, and
    the hard dependencies. It does not carry contributions.
    """

    module_id: str
    version: str
    label_key: str
    description_key: str
    entry_point: str
    dependencies: tuple[ModuleDependency, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.module_id:
            raise ValueError("ModuleManifest.module_id must not be empty")
        if not self.version:
            raise ValueError("ModuleManifest.version must not be empty")
        if not self.label_key:
            raise ValueError("ModuleManifest.label_key must not be empty")
        if not self.description_key:
            raise ValueError("ModuleManifest.description_key must not be empty")
        if not self.entry_point:
            raise ValueError("ModuleManifest.entry_point must not be empty")
        for dep in self.dependencies:
            if not isinstance(dep, ModuleDependency):
                raise ValueError(
                    f"ModuleManifest.dependencies must contain "
                    f"ModuleDependency instances, got {type(dep).__name__}"
                )

    def __repr__(self) -> str:
        return (
            f"ModuleManifest(module_id={self.module_id!r}, "
            f"version={self.version!r}, "
            f"dependencies={[d.module_id for d in self.dependencies]!r})"
        )
